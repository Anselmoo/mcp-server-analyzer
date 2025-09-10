// Example TypeScript file with interfaces and types
interface User {
    id: number;
    name: string;
    email: string;
    active: boolean;
}

interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

type UserPreferences = {
    theme: 'light' | 'dark';
    notifications: boolean;
    language: string;
}

class UserService {
    private apiUrl: string;
    
    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }
    
    async getUser(id: number): Promise<ApiResponse<User>> {
        const response = await fetch(`${this.apiUrl}/users/${id}`);
        return response.json();
    }
    
    async updateUserPreferences(userId: number, preferences: UserPreferences): Promise<boolean> {
        const response = await fetch(`${this.apiUrl}/users/${userId}/preferences`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        return response.ok;
    }
}

export { UserService, type User, type UserPreferences };