

import { UserRepo } from "../repositories/user.repo.js";

export class UserService {
    private userRepo: UserRepo;

    constructor(userRepo: UserRepo){
        this.userRepo = userRepo;
    }

    async getUserById(userId: number){
        return await this.userRepo.findUserById(userId);
    }
}
