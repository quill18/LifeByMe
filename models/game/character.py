# ./models/game/character.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from config import Config
from .enums import LifeStage
from enum import Enum
import json

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
characters = db.characters

class RelationshipStatus(Enum):
    ACTIVE = "Active"
    DEPARTED = "Departed"
    DECEASED = "Deceased"

@dataclass
class Character:
    life_id: ObjectId
    name: str
    age: int
    gender: str
    physical_description: str
    personality_description: str
    relationship_description: str
    first_met_context: str
    first_met_life_stage: LifeStage
    last_appearance_life_stage: LifeStage
    relationship_status: RelationshipStatus = RelationshipStatus.ACTIVE
    last_appearance_age: int = field(default=None)
    memory_ids: List[ObjectId] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    _id: ObjectId = field(default_factory=ObjectId)

    def to_dict(self) -> Dict:
        """Convert Character to dictionary for database storage"""
        return {
            '_id': self._id,
            'life_id': self.life_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'physical_description': self.physical_description,
            'personality_description': self.personality_description,
            'relationship_description': self.relationship_description,
            'first_met_context': self.first_met_context,
            'first_met_life_stage': self.first_met_life_stage.value,
            'last_appearance_life_stage': self.last_appearance_life_stage.value,
            'relationship_status': self.relationship_status.value,  # Add this line
            'last_appearance_age': self.last_appearance_age,
            'memory_ids': [str(id) for id in self.memory_ids],
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
            age=data['age'],
            gender=data['gender'],
            physical_description=data['physical_description'],
            personality_description=data['personality_description'],
            relationship_description=data['relationship_description'],
            first_met_context=data['first_met_context'],
            first_met_life_stage=LifeStage(data['first_met_life_stage']),
            last_appearance_life_stage=LifeStage(data['last_appearance_life_stage']),
            relationship_status=RelationshipStatus(data.get('relationship_status', 'Active')),  # Fix this line
            last_appearance_age=data.get('last_appearance_age'),
            memory_ids=[ObjectId(id) for id in data.get('memory_ids', [])],
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

    def add_memory(self, memory_id: ObjectId) -> None:
        """Add a memory ID to this character's memory list"""
        if memory_id not in self.memory_ids:
            self.memory_ids.append(memory_id)
            self.save()

    def update_status(self, new_status: RelationshipStatus, last_age: Optional[int] = None) -> None:
        """Update character's relationship status and optionally their last appearance age"""
        self.relationship_status = new_status
        if last_age is not None:
            self.last_appearance_age = last_age
        self.save()

    @staticmethod
    def format_characters_for_ai(character_ids: Optional[List[ObjectId]] = None, life_id: Optional[ObjectId] = None) -> str:
        """Format character information as JSON for the AI.
        If character_ids is None, return all active characters for the given life_id."""
        
        if not life_id and not character_ids:
            return "[]"  # Return empty array if no context provided
            
        query = {}
        if life_id:
            query['life_id'] = life_id
        if character_ids is not None:
            query['_id'] = {'$in': character_ids}
        else:
            query['relationship_status'] = 'Active'
        
        characters_data = []
        for char_data in characters.find(query):
            char = Character.from_dict(char_data)
            characters_data.append({
                'id': str(char._id),
                'name': char.name,
                'age': char.age,
                'last_appearance_age': char.last_appearance_age,
                'last_appearance_life_stage': char.last_appearance_life_stage.value if char.last_appearance_life_stage else None,
                'gender': char.gender,
                'physical_description': char.physical_description,
                'personality_description': char.personality_description,
                'relationship_description': char.relationship_description,
                'relationship_status': char.relationship_status.value
            })
        
        return json.dumps(characters_data, indent=2)
