# ./models/game/life.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from config import Config
from .enums import LifeStage, Intensity, Difficulty
from .base import Ocean, Trait, Skill
from .memory import Memory

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
lives = db.lives

@dataclass
class Life:
    user_id: ObjectId
    name: str
    age: int
    gender: str
    custom_gender: Optional[str]
    intensity: Intensity
    difficulty: Difficulty
    custom_directions: Optional[str]
    life_stage: LifeStage
    current_employment: Optional[str]
    ocean: Ocean
    traits: List[Trait]
    skills: List[Skill]
    current_stress: int = 0  # 0-100
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_played: datetime = field(default_factory=datetime.utcnow)
    archived: bool = False
    _id: ObjectId = field(default_factory=ObjectId)

    def to_dict(self) -> Dict:
        """Convert Life to dictionary for database storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'custom_gender': self.custom_gender,
            'intensity': self.intensity.value,
            'difficulty': self.difficulty.value,
            'custom_directions': self.custom_directions,
            'life_stage': self.life_stage.value,
            'current_employment': self.current_employment,
            'ocean': self.ocean.to_dict(),
            'traits': [trait.to_dict() for trait in self.traits],
            'skills': [skill.to_dict() for skill in self.skills],
            'current_stress': self.current_stress,
            'created_at': self.created_at,
            'last_played': self.last_played,
            'archived': self.archived
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Life':
        """Create Life object from dictionary"""
        return cls(
            _id=data.get('_id', ObjectId()),
            user_id=data['user_id'],
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            custom_gender=data.get('custom_gender'),
            intensity=Intensity(data['intensity']),
            difficulty=Difficulty(data['difficulty']),
            custom_directions=data.get('custom_directions'),
            life_stage=LifeStage(data['life_stage']),
            current_employment=data.get('current_employment'),
            ocean=Ocean.from_dict(data['ocean']),
            traits=[Trait.from_dict(t) for t in data['traits']],
            skills=[Skill.from_dict(s) for s in data['skills']],
            current_stress=data.get('current_stress', 0),
            created_at=data.get('created_at', datetime.utcnow()),
            last_played=data.get('last_played', datetime.utcnow()),
            archived=data.get('archived', False)
        )
        



    def save(self) -> None:
        """Save life to database"""
        self.last_played = datetime.utcnow()
        lives.update_one(
            {'_id': self._id},
            {'$set': self.to_dict()},
            upsert=True
        )

    @staticmethod
    def get_by_id(life_id: ObjectId) -> Optional['Life']:
        """Get life by ID"""
        life_data = lives.find_one({'_id': life_id})
        return Life.from_dict(life_data) if life_data else None

    @staticmethod
    def get_by_user_id(user_id: ObjectId) -> List['Life']:
        """Get all lives for a user"""
        life_data = lives.find({'user_id': user_id})
        return [Life.from_dict(data) for data in life_data]

    def get_memories(self) -> List[Memory]:
        """Get all memories for this life"""
        return Memory.get_by_life_id(self._id)

    def apply_memory(self, memory: Memory) -> None:
        """Apply a memory's impacts to the life"""
        # Update OCEAN traits
        self.ocean = self.ocean + memory.ocean_impact

        # Update or add secondary traits
        for impact in memory.trait_impacts:
            existing_trait = next(
                (t for t in self.traits if t.name == impact.name), 
                None
            )
            if existing_trait:
                existing_trait.value = (existing_trait + impact).value
            else:
                self.traits.append(Trait(impact.name, impact.value))

        # Update or add skills
        for impact in memory.skill_impacts:
            existing_skill = next(
                (s for s in self.skills if s.name == impact.name),
                None
            )
            if existing_skill:
                existing_skill.value = (existing_skill + impact).value
            else:
                self.skills.append(Skill(impact.name, impact.value))

        # Update stress
        self.current_stress = max(0, min(100, self.current_stress + memory.stress_impact))

        # Save changes
        self.save()