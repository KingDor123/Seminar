import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { UserRepo, User } from "../repositories/user.repo.js";
import { LoginInput, RegisterInput } from "../utils/validation.js";
import { AppError } from "../utils/AppError.js";

export class UserService {
    private userRepo: UserRepo;
    private readonly JWT_SECRET = process.env.JWT_SECRET || 'dev_secret_key_change_me';
    private readonly SALT_ROUNDS = 10;

    constructor(userRepo: UserRepo){
        this.userRepo = userRepo;
    }

    async getUserById(userId: number){
        return await this.userRepo.findUserById(userId);
    }

    async register(data: RegisterInput): Promise<{ user: Omit<User, 'password_hash'>, token: string }> {
        // Check if user exists
        const existingUser = await this.userRepo.findUserByEmail(data.email);
        if (existingUser) {
            throw new AppError('User with this email already exists', 409);
        }

        // Hash password
        const password_hash = await bcrypt.hash(data.password, this.SALT_ROUNDS);

        // Create user
        const newUser = await this.userRepo.createUser({
            full_name: data.full_name,
            email: data.email,
            password_hash: password_hash,
            role: 'user' // Default role
        });

        // Generate token
        const token = this.generateToken(newUser.id, newUser.role);

        // Return user without password hash
        const { password_hash: _, ...userWithoutPassword } = newUser;
        return { user: userWithoutPassword, token };
    }

    async login(data: LoginInput): Promise<{ user: Omit<User, 'password_hash'>, token: string }> {
        const user = await this.userRepo.findUserByEmail(data.email);
        if (!user) {
            throw new AppError('Invalid email or password', 401);
        }

        const isPasswordValid = await bcrypt.compare(data.password, user.password_hash);
        if (!isPasswordValid) {
            throw new AppError('Invalid email or password', 401);
        }

        const token = this.generateToken(user.id, user.role);

        const { password_hash: _, ...userWithoutPassword } = user;
        return { user: userWithoutPassword, token };
    }

    private generateToken(userId: number, role: string): string {
        return jwt.sign(
            { sub: userId, role },
            this.JWT_SECRET,
            { expiresIn: '7d' }
        );
    }
}