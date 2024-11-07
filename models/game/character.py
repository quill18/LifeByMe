# ./models/game/character.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient

from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
characters = db.characters

@dataclass
class Character:
   life_id: ObjectId
   name: str
   relationship_tags: List[str]
   friendship: int = 0  # 0-10
   romance: int = 0     # 0-10
   created_at: datetime = field(default_factory=datetime.utcnow)
   last_interaction: datetime = field(default_factory=datetime.utcnow)
   _id: ObjectId = field(default_factory=ObjectId)

   def to_dict(self) -> Dict:
       """Convert Character to dictionary for database storage"""
       return {
           '_id': self._id,
           'life_id': self.life_id,
           'name': self.name,
           'relationship_tags': self.relationship_tags,
           'friendship': self.friendship,
           'romance': self.romance,
           'created_at': self.created_at,
           'last_interaction': self.last_interaction
       }

   @classmethod
   def from_dict(cls, data: Dict) -> 'Character':
       """Create Character object from dictionary"""
       return cls(
           _id=data.get('_id', ObjectId()),
           life_id=data['life_id'],
           name=data['name'],
           relationship_tags=data['relationship_tags'],
           friendship=data.get('friendship', 0),
           romance=data.get('romance', 0),
           created_at=data.get('created_at', datetime.utcnow()),
           last_interaction=data.get('last_interaction', datetime.utcnow())
       )

   def save(self) -> None:
       """Save character to database"""
       self.last_interaction = datetime.utcnow()
       characters.update_one(
           {'_id': self._id},
           {'$set': self.to_dict()},
           upsert=True
       )

   @staticmethod
   def get_by_id(char_id: ObjectId) -> Optional['Character']:
       """Get character by ID"""
       char_data = characters.find_one({'_id': char_id})
       return Character.from_dict(char_data) if char_data else None

   @staticmethod
   def get_by_life_id(life_id: ObjectId) -> List['Character']:
       """Get all characters associated with a life"""
       char_data = characters.find({'life_id': life_id})
       return [Character.from_dict(data) for data in char_data]

   def update_relationship(self, friendship_change: int = 0, romance_change: int = 0) -> None:
       """Update relationship values, ensuring they stay within bounds"""
       self.friendship = max(0, min(10, self.friendship + friendship_change))
       self.romance = max(0, min(10, self.romance + romance_change))
       self.save()

   def add_relationship_tag(self, tag: str) -> None:
       """Add a new relationship tag if it doesn't already exist"""
       if tag not in self.relationship_tags:
           self.relationship_tags.append(tag)
           self.save()

   def remove_relationship_tag(self, tag: str) -> None:
       """Remove a relationship tag if it exists"""
       if tag in self.relationship_tags:
           self.relationship_tags.remove(tag)
           self.save()