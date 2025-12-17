export class UserController {
    userService;
    constructor(userService) {
        this.userService = userService;
    }
    async getUser(req, res) {
        const userId = Number(req.params.id);
        if (!Number.isInteger(userId) || userId <= 0) {
            return res.status(400).json({ message: 'User id must be a positive integer' });
        }
        try {
            const user = await this.userService.getUserById(userId);
            if (user) {
                res.status(200).json(user);
            }
            else {
                res.status(404).json({ message: 'User not found' });
            }
        }
        catch (error) {
            console.error(`[UserController] Error getting user ${userId}:`, error);
            res.status(500).json({ message: 'Internal server error', error: error.message });
        }
    }
    async updateUser(req, res) {
        const userId = Number(req.params.id);
        // Ensure user updates their own profile (or is admin)
        // Since we have authMiddleware attached to the route, req.user is available
        if (req.user?.id !== userId && req.user?.role !== 'admin') {
            return res.status(403).json({ message: 'Forbidden' });
        }
        try {
            const updatedUser = await this.userService.updateUser(userId, req.body);
            res.status(200).json(updatedUser);
        }
        catch (error) {
            if (error.statusCode) {
                return res.status(error.statusCode).json({ message: error.message });
            }
            console.error(`[UserController] Error updating user ${userId}:`, error);
            res.status(500).json({ message: 'Internal server error' });
        }
    }
}
