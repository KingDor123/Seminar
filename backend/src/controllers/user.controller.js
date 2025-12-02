
export class UserController {
    constructor(userService){
        this.userService = userService;
    }

    async getUser(req, res){
        const userId = req.params.id;
        try {
            const user = await this.userService.getUserById(userId);
            if(user){
                res.status(200).json(user);
            } else {
                res.status(404).json({ message: 'User not found' });
            }
        } catch (error) {
            res.status(500).json({ message: 'Internal server error', error: error.message });
        }
    }
}
