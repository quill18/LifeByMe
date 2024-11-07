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
                 created_at: Optional[datetime] = None,
                 last_login: Optional[datetime] = None,
                 last_login_ip: Optional[str] = None,
                 _id: Optional[Any] = None):
        self._id = _id if isinstance(_id, ObjectId) else ObjectId()
        self.username = username
        self.password_hash = password_hash
        self.openai_api_key = openai_api_key
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

    def change_password(self, new_password: str) -> None:
        if len(new_password) < Config.MIN_PASSWORD_LENGTH:
            raise ValueError(f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters')

        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'password_hash': generate_password_hash(new_password)
                    }
                }
            )
            if not result.modified_count:
                raise DatabaseError("Failed to change password")
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def update_openai_key(self, new_key: Optional[str]) -> None:
        try:
            result = users.update_one(
                {'_id': self._id},
                {
                    '$set': {
                        'openai_api_key': new_key
                    }
                }
            )
            if not result.modified_count:
                raise DatabaseError("Failed to update API key")
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")