export class UserRepo {
    constructor(db) {
        this.db = db;
    }
    async findUserById(userId) {
        console.log(`[UserRepo] Finding user by ID: ${userId}`);
        const sql = 'SELECT * FROM users WHERE id = $1';
        const params = [userId];
        const result = await this.db.execute(sql, params);
        return result[0];
    }
}
