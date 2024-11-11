# ./models/game/story.py

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from enum import Enum

from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
stories = db.stories

class StoryStatus(Enum):
    ACTIVE = "active"
    CONCLUDED = "concluded"
    COMPLETED = "completed"
    DELETED = "deleted"

@dataclass
class Story:
    life_id: ObjectId
    prompt: str
    beats: List[Tuple[str, Optional[str]]]  # List of (story_beat, selected_response) tuples
    current_options: List[str]  # Response options for the latest beat
    status: StoryStatus = StoryStatus.ACTIVE
    memory_title: Optional[str] = None
    memory_description: Optional[str] = None
    memory_params: Optional[Dict] = None  # Temporary storage for memory generation
    resulting_memory_id: Optional[ObjectId] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    _id: ObjectId = field(default_factory=ObjectId)
    character_ids: List[ObjectId] = field(default_factory=list)


    def to_dict(self) -> Dict:
        """Convert Story to dictionary for database storage"""
        base_dict = {
            '_id': self._id,
            'life_id': self.life_id,
            'prompt': self.prompt,
            'beats': [(beat, response) for beat, response in self.beats],
            'current_options': self.current_options,
            'status': self.status.value,
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'character_ids': [str(char_id) for char_id in self.character_ids]
        }
        
        if self.memory_title:
            base_dict['memory_title'] = self.memory_title
        if self.memory_description:
            base_dict['memory_description'] = self.memory_description
        if self.memory_params:
            base_dict['memory_params'] = self.memory_params
        if self.resulting_memory_id:
            base_dict['resulting_memory_id'] = self.resulting_memory_id
            
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict) -> 'Story':
        """Create Story object from dictionary"""
        return cls(
            _id=data.get('_id', ObjectId()),
            life_id=data['life_id'],
            prompt=data['prompt'],
            beats=[(beat, response) for beat, response in data['beats']],
            current_options=data['current_options'],
            status=StoryStatus(data.get('status', 'active')),
            memory_title=data.get('memory_title'),
            memory_description=data.get('memory_description'),
            memory_params=data.get('memory_params'),
            resulting_memory_id=data.get('resulting_memory_id'),
            created_at=data.get('created_at', datetime.utcnow()),
            last_updated=data.get('last_updated', datetime.utcnow()),
            character_ids=[ObjectId(id_str) for id_str in data.get('character_ids', [])]
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
        """Get active or concluded story for a life"""
        story_data = stories.find_one({
            'life_id': life_id,
            'status': {
                '$in': [StoryStatus.ACTIVE.value, StoryStatus.CONCLUDED.value]
            }
        })
        return Story.from_dict(story_data) if story_data else None

    def add_player_response(self, selected_response: str) -> None:
        """Add player's selected response to the current beat"""
        if self.status != StoryStatus.ACTIVE:
            raise ValueError("Cannot add response to non-active story")
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
        if self.status != StoryStatus.ACTIVE:
            raise ValueError("Cannot add beat to non-active story")
            
        self.beats.append((new_beat, None))
        self.current_options = new_options
        self.save()

    def conclude_story(self, final_beat: str) -> None:
        """Add final beat and mark story as concluded"""
        if self.status != StoryStatus.ACTIVE:
            raise ValueError("Can only conclude an active story")
            
        self.beats.append((final_beat, None))
        self.current_options = []
        self.status = StoryStatus.CONCLUDED
        self.save()

    def delete_story(self) -> None:
        """Mark story as deleted"""
        self.status = StoryStatus.DELETED
        self.save()

    def store_memory_params(self, title: str, description: str, params: Dict) -> None:
        """Store generated memory parameters"""
        if self.status != StoryStatus.CONCLUDED:
            raise ValueError("Can only store memory params for a concluded story")
            
        self.memory_title = title
        self.memory_description = description
        self.memory_params = params
        self.save()

    def complete_with_memory(self, memory_id: ObjectId) -> None:
        """Mark story as completed with associated memory"""
        if self.status != StoryStatus.CONCLUDED:
            raise ValueError("Can only complete a concluded story")
        if not self.memory_params:
            raise ValueError("No memory parameters stored")
            
        self.resulting_memory_id = memory_id
        self.status = StoryStatus.COMPLETED
        self.save()

    def get_current_beat(self) -> Optional[Tuple[str, List[str]]]:
        """Get the current beat text and options"""
        if not self.beats:
            return None
        return (self.beats[-1][0], self.current_options)

    def delete(self) -> None:
        """Delete this story from database"""
        stories.delete_one({'_id': self._id})