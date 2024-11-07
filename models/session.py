# ./models/session.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pymongo import MongoClient
from config import Config
from .utils import validate_object_id, DatabaseError

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
sessions = db.sessions

class Session:
    def __init__(self,
                 session_id: str,
                 user_id: Any,
                 current_life_id: Optional[Any] = None,
                 created_at: Optional[datetime] = None,
                 last_accessed: Optional[datetime] = None,
                 ip_address: Optional[str] = None,
                 _id: Optional[Any] = None):
        self._id = _id if isinstance(_id, ObjectId) else ObjectId()
        self.session_id = session_id
        self.user_id = user_id if isinstance(user_id, ObjectId) else validate_object_id(str(user_id))
        self.current_life_id = (current_life_id if isinstance(current_life_id, ObjectId) 
                               else validate_object_id(str(current_life_id)) if current_life_id 
                               else None)
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = last_accessed or datetime.utcnow()
        self.ip_address = ip_address

    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> Optional['Session']:
        if data is None:
            return None
        # Convert string dates to datetime if needed
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_accessed'), str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)

    def to_db_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'current_life_id': self.current_life_id,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'ip_address': self.ip_address
        }

    @staticmethod
    def create(session_id: str, user_id: Any, ip_address: str) -> 'Session':
        # Clean up any existing sessions for this user
        Session.cleanup_user_sessions(user_id)
        
        session = Session(
            session_id=session_id,
            user_id=user_id if isinstance(user_id, ObjectId) else validate_object_id(str(user_id)),
            ip_address=ip_address
        )
        
        try:
            result = sessions.insert_one(session.to_db_dict())
            if not result.acknowledged:
                raise DatabaseError("Failed to create session")
            return session
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    @staticmethod
    def get_by_session_id(session_id: str) -> Optional['Session']:
        try:
            session_data = sessions.find_one({'session_id': session_id})
            session = Session.from_db_dict(session_data)
            
            if session and session.is_valid():
                session.update_access()
                return session
            
            if session:
                session.delete()
            return None
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def update_access(self) -> None:
        """Update the last accessed time"""
        try:
            new_time = datetime.utcnow()
            result = sessions.update_one(
                {'session_id': self.session_id},
                {
                    '$set': {
                        'last_accessed': new_time
                    }
                }
            )
            if result.matched_count > 0:
                self.last_accessed = new_time
            else:
                raise DatabaseError("Session not found in database")
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def is_valid(self) -> bool:
        """Check if the session is still valid (not expired)"""
        if not self.last_accessed:
            return False
        
        expiry_time = self.last_accessed + Config.SESSION_LIFETIME
        return datetime.utcnow() <= expiry_time

    @staticmethod
    def cleanup_user_sessions(user_id: Any) -> None:
        """Remove all existing sessions for a user"""
        if isinstance(user_id, str):
            user_id = validate_object_id(user_id)
        
        try:
            sessions.delete_many({'user_id': user_id})
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    @staticmethod
    def cleanup_expired_sessions() -> None:
        """Remove all expired sessions from the database"""
        try:
            expiry_time = datetime.utcnow() - Config.SESSION_LIFETIME
            sessions.delete_many({'last_accessed': {'$lt': expiry_time}})
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def update_current_life(self, life_id: Any) -> None:
        """Update the current life ID for this session"""
        if isinstance(life_id, str):
            life_id = validate_object_id(life_id)
            
        try:
            result = sessions.update_one(
                {'session_id': self.session_id},
                {
                    '$set': {
                        'current_life_id': life_id
                    }
                }
            )
            if not result.modified_count:
                raise DatabaseError("Failed to update current life")
            self.current_life_id = life_id
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

    def delete(self) -> None:
        """Delete this session from the database"""
        try:
            result = sessions.delete_one({'session_id': self.session_id})
            if not result.deleted_count:
                raise DatabaseError("Failed to delete session")
        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")