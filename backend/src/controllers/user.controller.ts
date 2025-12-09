
import { Request, Response } from 'express';
import { UserService } from '../services/user.service.js';

export class UserController {
    private userService: UserService;

    constructor(userService: UserService){
        this.userService = userService;
    }

    async getUser(req: Request, res: Response) {
        const userId = Number(req.params.id);
        if (!Number.isInteger(userId) || userId <= 0) {
            return res.status(400).json({ message: 'User id must be a positive integer' });
        }
        try {
            const user = await this.userService.getUserById(userId);
            if(user){
                res.status(200).json(user);
            } else {
                res.status(404).json({ message: 'User not found' });
            }
        } catch (error: any) {
            console.error(`[UserController] Error getting user ${userId}:`, error);
            res.status(500).json({ message: 'Internal server error', error: error.message });
        }
    }
}
