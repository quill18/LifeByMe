# ./models/user.py

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from .utils import validate_object_id, DatabaseError

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
users = db.users

class User:
    def __init__(self, 
                username: str,
                password_hash: Optional[str] = None,
                openai_api_key: Optional[str] = None,
                gpt_model: str = "gpt-4o",  # Add default value
                created_at: Optional[datetime] = None,
                last_login: Optional[datetime] = None,
                last_login_ip: Optional[str] = None,
                _id: Optional[Any] = None):
        self._id = _id if isinstance(_id, ObjectId) else ObjectId()
        self.username = username
        self.password_hash = password_hash
        self.openai_api_key = openai_api_key
        self.gpt_model = gpt_model
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.last_login_ip = last_login_ip

    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> 'User':
        if data is None:
            return None
        # Ensure _id is ObjectId
        if '_id' in data and not isinstance(data['_id'], ObjectId):
            data['_id'] = validate_object_id(str(data['_id']))
        return cls(**data)

    def to_db_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'username': self.username,
            'password_hash': self.password_hash,
            'openai_api_key': self.openai_api_key,
            'gpt_model': self.gpt_model,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'last_login_ip': self.last_login_ip
        }

    @staticmethod
    def create(username: str, password: str, 
               openai_api_key: Optional[str] = None, 
               ip_address: Optional[str] = None) -> 'User':
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            raise ValueError(f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters')

        existing_user = users.find_one({'username': username})
        if existing_user:
            raise ValueError('Username already exists')

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            openai_api_key=openai_api_key if openai_api_key else None,
            last_login_ip=ip_address
        )
        
        try:
            result = users.insert_one(user.to_db_dict())
            if not result.acknowledged:
                raise DatabaseError("Failed to create user")
            return user
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    @staticmethod
    def get_by_username(username: str) -> Optional['User']:
        try:
            user_data = users.find_one({'username': username})
            return User.from_db_dict(user_data)
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    @staticmethod
    def get_by_id(user_id: Any) -> Optional['User']:
        if isinstance(user_id, str):
            user_id = validate_object_id(user_id)
        if not isinstance(user_id, ObjectId):
            return None
        
        try:
            user_data = users.find_one({'_id': user_id})
            return User.from_db_dict(user_data)
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def update_login(self, ip_address: str) -> None:
        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'last_login': datetime.utcnow(),
                        'last_login_ip': ip_address
                    }
                }
            )
            if not result.modified_count:
                raise DatabaseError("Failed to update login information")
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def update_openai_key(self, new_key: Optional[str]) -> None:
        """Update OpenAI API key if different from current key"""
        if new_key == self.openai_api_key:
            return  # No update needed if key is the same
            
        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'openai_api_key': new_key
                    }
                }
            )
            if result.matched_count == 0:  # No document matched
                raise DatabaseError("User not found")
            self.openai_api_key = new_key
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def update_gpt_model(self, new_model: str) -> None:
        """Update GPT model if different from current model"""
        if new_model == self.gpt_model:
            return  # No update needed if model is the same
            
        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'gpt_model': new_model
                    }
                }
            )
            if result.matched_count == 0:  # No document matched
                raise DatabaseError("User not found")
            self.gpt_model = new_model
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def change_password(self, new_password: str) -> None:
        """Change password if different from current password"""
        if len(new_password) < Config.MIN_PASSWORD_LENGTH:
            raise ValueError(f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters')

        new_hash = generate_password_hash(new_password)
        if new_hash == self.password_hash:
            return  # No update needed if password hash is the same
            
        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'password_hash': new_hash
                    }
                }
            )
            if result.matched_count == 0:  # No document matched
                raise DatabaseError("User not found")
            self.password_hash = new_hash
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")
