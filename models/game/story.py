# ./models/game/story.py

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient

from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
stories = db.stories

@dataclass
class Story:
   life_id: ObjectId
   prompt: str
   # List of (story_beat, selected_response) tuples. Latest beat's response is None
   beats: List[Tuple[str, Optional[str]]]
   current_options: List[str]  # Response options for the latest beat
   created_at: datetime = field(default_factory=datetime.utcnow)
   last_updated: datetime = field(default_factory=datetime.utcnow)
   _id: ObjectId = field(default_factory=ObjectId)

   def to_dict(self) -> Dict:
       """Convert Story to dictionary for database storage"""
       return {
           '_id': self._id,
           'life_id': self.life_id,
           'prompt': self.prompt,
           'beats': [(beat, response) for beat, response in self.beats],
           'current_options': self.current_options,
           'created_at': self.created_at,
           'last_updated': self.last_updated
       }

   @classmethod
   def from_dict(cls, data: Dict) -> 'Story':
       """Create Story object from dictionary"""
       return cls(
           _id=data.get('_id', ObjectId()),
           life_id=data['life_id'],
           prompt=data['prompt'],
           beats=[(beat, response) for beat, response in data['beats']],
           current_options=data['current_options'],
           created_at=data.get('created_at', datetime.utcnow()),
           last_updated=data.get('last_updated', datetime.utcnow())
       )

   def save(self) -> None:
       """Save story to database"""
       self.last_updated = datetime.utcnow()
       stories.update_one(
           {'_id': self._id},
           {'$set': self.to_dict()},
           upsert=True
       )

   @staticmethod
   def get_by_id(story_id: ObjectId) -> Optional['Story']:
       """Get story by ID"""
       story_data = stories.find_one({'_id': story_id})
       return Story.from_dict(story_data) if story_data else None

   @staticmethod
   def get_by_life_id(life_id: ObjectId) -> Optional['Story']:
       """Get active story for a life (there should only be one)"""
       story_data = stories.find_one({'life_id': life_id})
       return Story.from_dict(story_data) if story_data else None

   def add_player_response(self, selected_response: str) -> None:
       """Add player's selected response to the current beat"""
       if not self.beats:
           raise ValueError("No story beats exist")
       if not selected_response in self.current_options:
           raise ValueError("Invalid response option")
       
       # Update the last beat with the selected response
       last_beat, _ = self.beats[-1]
       self.beats[-1] = (last_beat, selected_response)
       self.save()

   def add_story_beat(self, new_beat: str, new_options: List[str]) -> None:
       """Add a new story beat with its response options"""
       self.beats.append((new_beat, None))
       self.current_options = new_options
       self.save()

   def delete(self) -> None:
       """Delete this story from database"""
       stories.delete_one({'_id': self._id})