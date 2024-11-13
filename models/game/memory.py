# ./models/game/memory.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from models.game.life import LifeStage
from config import Config
from .base import Trait
import json

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
memories = db.memories

import logging
logger = logging.getLogger(__name__)

@dataclass
class Memory:
    life_id: ObjectId
    title: str
    description: str
    importance: int  # 1-3
    permanence: int  # 1-3
    emotional_tags: List[str]
    context_tags: List[str]
    story_tags: List[str]  # e.g., "coming of age", "first love"
    primary_trait_impacts: List[Trait]
    secondary_trait_impacts: List[Trait]
    life_stage: LifeStage
    age_experienced: int
    impact_explanation: str
    stress_impact: int
    character_ids: List[ObjectId] = field(default_factory=list)
    source_story_id: Optional[ObjectId] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    recontextualized_at: Optional[datetime] = None
    _id: ObjectId = field(default_factory=ObjectId)

    def to_dict(self) -> Dict:
        """Convert Memory to dictionary for database storage"""
        return {
            '_id': self._id,
            'life_id': self.life_id,
            'title': self.title,
            'description': self.description,
            'importance': self.importance,
            'permanence': self.permanence,
            'emotional_tags': self.emotional_tags,
            'context_tags': self.context_tags,
            'story_tags': self.story_tags,
            'primary_trait_impacts': [trait.to_dict() for trait in self.primary_trait_impacts],
            'secondary_trait_impacts': [trait.to_dict() for trait in self.secondary_trait_impacts],
            'life_stage': self.life_stage.value,
            'age_experienced': self.age_experienced,
            'impact_explanation': self.impact_explanation,
            'stress_impact': self.stress_impact,
            'character_ids': [str(char_id) for char_id in self.character_ids],
            'source_story_id': str(self.source_story_id) if self.source_story_id else None,
            'created_at': self.created_at,
            'recontextualized_at': self.recontextualized_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """Create Memory object from dictionary"""
        return cls(
            _id=data.get('_id', ObjectId()),
            life_id=data['life_id'],
            title=data['title'],
            description=data['description'],
            importance=data['importance'],
            permanence=data['permanence'],
            emotional_tags=data['emotional_tags'],
            context_tags=data['context_tags'],
            story_tags=data['story_tags'],
            primary_trait_impacts=[Trait.from_dict(t) for t in data['primary_trait_impacts']],
            secondary_trait_impacts=[Trait.from_dict(t) for t in data['secondary_trait_impacts']],
            life_stage=data['life_stage'],
            age_experienced=data['age_experienced'],
            impact_explanation=data['impact_explanation'],
            stress_impact=data['stress_impact'],
            character_ids=[ObjectId(id_str) for id_str in data.get('character_ids', [])],
            source_story_id=ObjectId(data['source_story_id']) if data.get('source_story_id') else None,
            created_at=data.get('created_at', datetime.utcnow()),
            recontextualized_at=data.get('recontextualized_at')
        )

    def save(self) -> None:
        """Save memory to database"""
        memories.update_one(
            {'_id': self._id},
            {'$set': self.to_dict()},
            upsert=True
        )

    @staticmethod
    def get_by_id(memory_id: ObjectId) -> Optional['Memory']:
        """Get memory by ID"""
        memory_data = memories.find_one({'_id': memory_id})
        return Memory.from_dict(memory_data) if memory_data else None

    @staticmethod
    def get_by_life_id(life_id: ObjectId) -> List['Memory']:
        """Get all memories for a specific life"""
        memory_data = memories.find({'life_id': life_id}).sort('created_at', 1)  # 1 for ascending order (oldest first)
        return [Memory.from_dict(data) for data in memory_data]

    def add_character(self, character_id: ObjectId) -> None:
        """Add a character to this memory if not already present"""
        if character_id not in self.character_ids:
            self.character_ids.append(character_id)
            self.save()

    def get_characters(self) -> List['Character']:
        """Get all characters involved in this memory"""
        from .character import Character
        return [Character.get_by_id(char_id) for char_id in self.character_ids]

    def get_primary_trait_impact(self, trait_name: str) -> Optional[Trait]:
        """Get the impact on a specific primary trait"""
        return next((t for t in self.primary_trait_impacts if t.name == trait_name), None)

    def get_secondary_trait_impact(self, trait_name: str) -> Optional[Trait]:
        """Get the impact on a specific secondary trait"""
        return next((t for t in self.secondary_trait_impacts if t.name == trait_name), None)

    def has_trait_changes(self) -> bool:
        """Check if there are any trait changes in this memory"""
        # Check primary traits
        if any(trait.value != 0 for trait in self.primary_trait_impacts):
            return True
        # Check secondary traits
        if any(trait.value != 0 for trait in self.secondary_trait_impacts):
            return True
        return False

    @staticmethod
    def format_memories_for_ai(life_id: ObjectId) -> str:
        """Format all non-faded memories as JSON for the AI, sorted by creation date"""
        try:
            # Get all memories for this life where permanence > 0
            memory_data = memories.find({
                'life_id': life_id,
                'permanence': {'$gt': 0}
            }).sort('created_at', 1)  # 1 for ascending order (oldest first)
            
            memories_list = []
            for mem_data in memory_data:
                memory = Memory.from_dict(mem_data)
                # Handle life_stage which might be string or enum
                life_stage = memory.life_stage
                if isinstance(life_stage, LifeStage):
                    life_stage = life_stage.value
                
                # Format trait impacts for AI
                trait_impacts = {
                    "primary_traits": {t.name: t.value for t in memory.primary_trait_impacts if t.value != 0},
                    "secondary_traits": {t.name: t.value for t in memory.secondary_trait_impacts if t.value != 0}
                }
                
                memories_list.append({
                    'title': memory.title,
                    'description': memory.description,
                    'life_stage': life_stage,
                    'age_experienced': memory.age_experienced,
                    'emotional_tags': memory.emotional_tags,
                    'context_tags': memory.context_tags,
                    'trait_impacts': trait_impacts,
                    'stress_impact': memory.stress_impact
                })
            
            return json.dumps(memories_list, indent=2)
        except Exception as e:
            logger.error(f"Error formatting memories for AI: {str(e)}")
            return "[]"  # Return empty array in case of error