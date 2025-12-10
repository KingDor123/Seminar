import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { AppError } from "../utils/AppError.js";
export class UserService {
    userRepo;
    JWT_SECRET = process.env.JWT_SECRET || 'dev_secret_key_change_me';
    SALT_ROUNDS = 10;
    constructor(userRepo) {
        this.userRepo = userRepo;
    }
    async getUserById(userId) {
        return await this.userRepo.findUserById(userId);
    }
    async register(data) {
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
    async login(data) {
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
    generateToken(userId, role) {
        return jwt.sign({ sub: userId, role }, this.JWT_SECRET, { expiresIn: '7d' });
    }
}
