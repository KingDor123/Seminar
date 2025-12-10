import express from 'express';
import { db } from '../config/databaseConfig.js';
import { AuthController } from '../controllers/auth.controller.js';
import { UserService } from '../services/user.service.js';
import { UserRepo } from '../repositories/user.repo.js';
import { authMiddleware } from '../middleware/auth.middleware.js';

const router = express.Router();

const userRepo = new UserRepo(db);
const userService = new UserService(userRepo);
const authController = new AuthController(userService);

router.post('/auth/register', (req, res) => authController.register(req, res));
router.post('/auth/login', (req, res) => authController.login(req, res));
router.post('/auth/logout', (req, res) => authController.logout(req, res));
router.get('/auth/me', authMiddleware, (req, res) => authController.getMe(req, res));

export default router;
