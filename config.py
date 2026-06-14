import json
import os
import hashlib

# User management file
USERS_FILE = "users.json"

def init_users():
    """Initialize users file if it doesn't exist"""
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "email": "admin@example.com",
                "name": "Admin User",
                "password": hash_password("admin123")
            }
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f)

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to file"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def authenticate(username, password):
    """Check if username and password are valid"""
    users = load_users()
    if username in users:
        return users[username]["password"] == hash_password(password)
    return False

def register_user(username, email, name, password):
    """Register a new user"""
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        "email": email,
        "name": name,
        "password": hash_password(password)
    }
    save_users(users)
    
    # Create user directory
    user_dir = f"data/users/{username}"
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(f"{user_dir}/knowledge", exist_ok=True)
    os.makedirs(f"{user_dir}/models", exist_ok=True)
    
    return True, "User registered successfully"

def get_user_data_dir(username):
    """Get user-specific data directory"""
    return f"data/users/{username}"

# Initialize users on import
init_users()
