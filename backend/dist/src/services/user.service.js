export class UserService {
    constructor(userRepo) {
        this.userRepo = userRepo;
    }
    async getUserById(userId) {
        return await this.userRepo.findUserById(userId);
    }
}
