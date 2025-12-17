import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AppError } from '../utils/AppError.js';
import { ChatRepo } from '../repositories/chat.repo.js'; // Import ChatRepo
import { db } from '../config/databaseConfig.js'; // Import db instance

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
            };
            // Optionally, add the session object here if needed by subsequent middleware/controllers
            session?: {
                id: number;
                user_id: number;
                scenario_id: string;
                start_time: Date;
                end_time?: Date;
            };
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

const chatRepo = new ChatRepo(db); // Initialize ChatRepo here

export const sessionOwnershipMiddleware = async (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
        return next(new AppError('Authentication required to check session ownership', 401));
    }

    const sessionId = parseInt(req.params.sessionId);
    if (isNaN(sessionId)) {
        return next(new AppError('Invalid session ID format', 400));
    }

    try {
        const session = await chatRepo.getSessionById(sessionId);

        if (!session) {
            return next(new AppError('Session not found', 404));
        }

        if (session.user_id !== req.user.id) {
            return next(new AppError('Forbidden: You do not own this session', 403));
        }

        // Attach session object to request for further use if needed
        req.session = session;
        next();
    } catch (error) {
        console.error('Session ownership check failed:', error);
        return next(new AppError('Internal server error during session ownership check', 500));
    }
};
