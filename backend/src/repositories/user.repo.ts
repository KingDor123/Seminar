import { Database } from '../config/databaseConfig.js';

export interface User {
    id: number;
    name: string;
    email: string;
    // Add other fields as per your schema
}

export class UserRepo {
    private db: Database;

    constructor(db: any) {
        this.db = db;
    }
    
    async findUserById(userId: number): Promise<User | undefined> {
        console.log(`[UserRepo] Finding user by ID: ${userId}`);
        const sql = 'SELECT * FROM users WHERE id = $1';
        const params = [userId];
        const result = await this.db.execute<User>(sql, params);
        return result[0];
    }
}
