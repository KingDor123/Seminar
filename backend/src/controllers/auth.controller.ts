import { Request, Response } from 'express';
import { UserService } from '../services/user.service.js';
import { loginSchema, registerSchema } from '../utils/validation.js';
import { AppError } from '../utils/AppError.js';

export class AuthController {
    private userService: UserService;

    constructor(userService: UserService) {
        this.userService = userService;
    }

    async register(req: Request, res: Response) {
        try {
            const validatedData = registerSchema.parse(req.body);
            const result = await this.userService.register(validatedData);

            // Set token in HTTP-only cookie
            res.cookie('token', result.token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'strict',
                maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
            });

            res.status(201).json({
                message: 'Registration successful',
                user: result.user,
                token: result.token // Also returning it for client-side storage if preferred, though cookie is set
            });
        } catch (error: any) {
            if (error.name === 'ZodError') {
                return res.status(400).json({ message: 'Validation error', errors: error.errors });
            }
            if (error instanceof AppError) {
                return res.status(error.statusCode).json({ message: error.message });
            }
            console.error('[AuthController] Register error:', error);
            res.status(500).json({ message: 'Internal server error' });
        }
    }

    async login(req: Request, res: Response) {
        try {
            const validatedData = loginSchema.parse(req.body);
            const result = await this.userService.login(validatedData);

            res.cookie('token', result.token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'strict',
                maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
            });

            res.status(200).json({
                message: 'Login successful',
                user: result.user,
                token: result.token
            });
        } catch (error: any) {
             if (error.name === 'ZodError') {
                return res.status(400).json({ message: 'Validation error', errors: error.errors });
            }
            if (error instanceof AppError) {
                return res.status(error.statusCode).json({ message: error.message });
            }
            console.error('[AuthController] Login error:', error);
            res.status(500).json({ message: 'Internal server error' });
        }
    }

    async logout(req: Request, res: Response) {
        res.clearCookie('token');
        res.status(200).json({ message: 'Logout successful' });
    }

    async getMe(req: Request, res: Response) {
        try {
            if (!req.user) {
                return res.status(401).json({ message: 'Not authenticated' });
            }

            const user = await this.userService.getUserById(req.user.id);
            if (!user) {
                return res.status(404).json({ message: 'User not found' });
            }

            const { password_hash, ...userWithoutPassword } = user;
            res.status(200).json({ user: userWithoutPassword });
        } catch (error) {
            console.error('[AuthController] GetMe error:', error);
            res.status(500).json({ message: 'Internal server error' });
        }
    }
}
