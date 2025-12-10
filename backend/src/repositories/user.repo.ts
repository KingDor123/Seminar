import { Database } from '../config/databaseConfig.js';

export interface User {
    id: number;
    full_name: string;
    email: string;
    password_hash: string;
    role: 'user' | 'admin';
    created_at?: Date;
    updated_at?: Date;
}

export class UserRepo {
    private db: Database;

    constructor(db: any) {
        this.db = db;
    }
    
    async findUserById(userId: number): Promise<User | undefined> {
        const sql = 'SELECT * FROM users WHERE id = $1';
        const params = [userId];
        const result = await this.db.execute<User>(sql, params);
        return result[0];
    }

    async findUserByEmail(email: string): Promise<User | undefined> {
        const sql = 'SELECT * FROM users WHERE email = $1';
        const params = [email];
        const result = await this.db.execute<User>(sql, params);
        return result[0];
    }

    async createUser(user: Omit<User, 'id' | 'created_at' | 'updated_at'>): Promise<User> {
        const sql = `
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        `;
        const params = [user.full_name, user.email, user.password_hash, user.role];
        const result = await this.db.execute<User>(sql, params);
        return result[0];
    }

    async updateUser(userId: number, updates: Partial<User>): Promise<User | undefined> {
        const fields = Object.keys(updates).filter(key => ['full_name', 'email', 'password_hash'].includes(key));
        if (fields.length === 0) return undefined;

        const setClause = fields.map((field, index) => `${field} = $${index + 2}`).join(', ');
        const sql = `UPDATE users SET ${setClause} WHERE id = $1 RETURNING *`;
        
        const values = fields.map(key => (updates as any)[key]);
        const params = [userId, ...values];
        
        const result = await this.db.execute<User>(sql, params);
        return result[0];
    }
}