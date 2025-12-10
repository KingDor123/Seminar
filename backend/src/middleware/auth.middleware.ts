import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AppError } from '../utils/AppError.js';

interface JwtPayload {
    sub: number;
    role: string;
}

// Extend Express Request to include user
declare global {
    namespace Express {
        interface Request {
            user?: {
                id: number;
                role: string;
            }
        }
    }
}

export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
    // 1. Get token from cookies or header
    let token = req.cookies.token;

    // Fallback: Check Authorization header (Bearer <token>)
    if (!token && req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
        token = req.headers.authorization.split(' ')[1];
    }

    if (!token) {
        return next(new AppError('Not authenticated', 401));
    }

    try {
        // 2. Verify token
        const secret = process.env.JWT_SECRET || 'dev_secret_key_change_me';
        const decoded = jwt.verify(token, secret) as JwtPayload;

        // 3. Attach user info to request
        req.user = {
            id: decoded.sub,
            role: decoded.role
        };

        next();
    } catch (error) {
        return next(new AppError('Invalid or expired token', 401));
    }
};
