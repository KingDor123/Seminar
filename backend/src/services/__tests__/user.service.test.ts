
import { UserService } from '../user.service';
import { AppError } from '../../utils/AppError';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

// Mock external libraries
jest.mock('bcrypt');
jest.mock('jsonwebtoken');

// Define types for our mock to help TS
const mockBcrypt = bcrypt as jest.Mocked<typeof bcrypt>;
const mockJwt = jwt as jest.Mocked<typeof jwt>;

describe('UserService', () => {
    let userService: UserService;
    let mockUserRepo: any;

    beforeEach(() => {
        jest.clearAllMocks();

        mockUserRepo = {
            findUserById: jest.fn(),
            findUserByEmail: jest.fn(),
            createUser: jest.fn(),
            updateUser: jest.fn(),
        };

        userService = new UserService(mockUserRepo);
    });

    describe('register', () => {
        const registerData = {
            full_name: 'Test User',
            email: 'test@example.com',
            password: 'password123'
        };

        it('should successfully register a new user', async () => {
            // Setup mocks
            mockUserRepo.findUserByEmail.mockResolvedValue(null);
            mockBcrypt.hash.mockImplementation(() => Promise.resolve('hashed_password') as any);
            mockUserRepo.createUser.mockResolvedValue({
                id: 1,
                ...registerData,
                role: 'user',
                password_hash: 'hashed_password'
            });
            mockJwt.sign.mockReturnValue('mock_token' as any);

            const result = await userService.register(registerData);

            expect(mockUserRepo.findUserByEmail).toHaveBeenCalledWith(registerData.email);
            expect(mockBcrypt.hash).toHaveBeenCalledWith(registerData.password, 10);
            expect(mockUserRepo.createUser).toHaveBeenCalled();
            expect(result).toHaveProperty('token', 'mock_token');
            expect(result.user).not.toHaveProperty('password_hash');
            expect(result.user.email).toBe(registerData.email);
        });

        it('should throw error if email already exists', async () => {
            mockUserRepo.findUserByEmail.mockResolvedValue({ id: 1, email: registerData.email });

            await expect(userService.register(registerData))
                .rejects
                .toThrow(new AppError('User with this email already exists', 409));
            
            expect(mockUserRepo.createUser).not.toHaveBeenCalled();
        });
    });

    describe('login', () => {
        const loginData = {
            email: 'test@example.com',
            password: 'password123'
        };

        const existingUser = {
            id: 1,
            email: loginData.email,
            password_hash: 'hashed_password',
            role: 'user',
            full_name: 'Test User'
        };

        it('should successfully login with correct credentials', async () => {
            mockUserRepo.findUserByEmail.mockResolvedValue(existingUser);
            mockBcrypt.compare.mockImplementation(() => Promise.resolve(true) as any);
            mockJwt.sign.mockReturnValue('mock_token' as any);

            const result = await userService.login(loginData);

            expect(mockBcrypt.compare).toHaveBeenCalledWith(loginData.password, existingUser.password_hash);
            expect(result).toHaveProperty('token', 'mock_token');
        });

        it('should throw error if user does not exist', async () => {
            mockUserRepo.findUserByEmail.mockResolvedValue(null);

            await expect(userService.login(loginData))
                .rejects
                .toThrow(new AppError('Invalid email or password', 401));
        });

        it('should throw error if password is incorrect', async () => {
            mockUserRepo.findUserByEmail.mockResolvedValue(existingUser);
            mockBcrypt.compare.mockImplementation(() => Promise.resolve(false) as any);

            await expect(userService.login(loginData))
                .rejects
                .toThrow(new AppError('Invalid email or password', 401));
        });
    });
});
