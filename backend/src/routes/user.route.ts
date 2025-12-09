import express from 'express';
import { db } from '../config/databaseConfig.js';
import { UserController } from '../controllers/user.controller.js';
import { UserService } from '../services/user.service.js';
import { UserRepo } from '../repositories/user.repo.js';

const router = express.Router();

const userRepo = new UserRepo(db);
const userService = new UserService(userRepo);
const userController = new UserController(userService);

router.get('/users/:id', (req, res) => userController.getUser(req, res));

export default router;
