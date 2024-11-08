# ./models/game/memory.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from models.game.life import LifeStage
from config import Config
from .base import Ocean, Trait, Skill

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
memories = db.memories

@dataclass
class Memory:
    life_id: ObjectId
    title: str
    description: str
    importance: int  # 1-10
    permanence: int  # 1-10
    emotional_tags: List[str]
    context_tags: List[str]
    story_tags: List[str]  # e.g., "coming of age", "first love"
    ocean_impact: Ocean
    trait_impacts: List[Trait]
    skill_impacts: List[Skill]
    life_stage: LifeStage
    age_experienced: int
    impact_explanation: str  # New field for AI's justification
    stress_impact: int      # Positive or negative impact on stress
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
            'ocean_impact': self.ocean_impact.to_dict(),
            'trait_impacts': [trait.to_dict() for trait in self.trait_impacts],
            'skill_impacts': [skill.to_dict() for skill in self.skill_impacts],
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
            ocean_impact=Ocean.from_dict(data['ocean_impact']),
            trait_impacts=[Trait.from_dict(t) for t in data['trait_impacts']],
            skill_impacts=[Skill.from_dict(s) for s in data['skill_impacts']],
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
        memory_data = memories.find({'life_id': life_id})
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