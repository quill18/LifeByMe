# ./models/game/life.py

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from pymongo import MongoClient
from config import Config
from .enums import LifeStage, Intensity, Difficulty
from .base import Trait
from .memory import Memory
from models.utils import DatabaseError

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]
lives = db.lives

# Define primary traits
PRIMARY_TRAITS = [
    "Curiosity",    # intellectual curiosity, creativity, and willingness to try new things
    "Discipline",   # self-control, organization, and dedication
    "Confidence",   # self-assurance and social comfort
    "Empathy",      # emotional intelligence and understanding of others
    "Resilience",   # emotional stability and stress management
    "Ambition"      # drive, goal-setting, and determination
]

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
    primary_traits: List[Trait]
    secondary_traits: List[Trait]
    current_stress: int = 0  # 0-100
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_played: datetime = field(default_factory=datetime.utcnow)
    archived: bool = False
    _id: ObjectId = field(default_factory=ObjectId)

    def to_dict(self) -> Dict:
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
            'primary_traits': [trait.to_dict() for trait in self.primary_traits],
            'secondary_traits': [trait.to_dict() for trait in self.secondary_traits],
            'current_stress': self.current_stress,
            'created_at': self.created_at,
            'last_played': self.last_played,
            'archived': self.archived
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Life':
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
            primary_traits=[Trait.from_dict(t) for t in data['primary_traits']],
            secondary_traits=[Trait.from_dict(t) for t in data['secondary_traits']],
            current_stress=data.get('current_stress', 0),
            created_at=data.get('created_at', datetime.utcnow()),
            last_played=data.get('last_played', datetime.utcnow()),
            archived=data.get('archived', False)
        )

    @staticmethod
    def generate_random_primary_traits() -> List[Trait]:
        """Generate a list of random primary traits"""
        return [Trait.random(name) for name in PRIMARY_TRAITS]

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
        # Update or add primary traits
        for primary_trait_impact in memory.primary_trait_impacts:
            # Find matching primary trait if it exists
            if primary_trait_impact.name in PRIMARY_TRAITS:
                primary_trait = next(
                    (t for t in self.primary_traits if t.name == primary_trait_impact.name),
                    None
                )
                if primary_trait:
                    primary_trait.value = (primary_trait + primary_trait_impact).value
        # Handle secondary trait
        for secondary_trait_impact in memory.secondary_trait_impacts:
            existing_trait = next(
                (t for t in self.secondary_traits if t.name == secondary_trait_impact.name),
                None
            )
            if existing_trait:
                existing_trait.value = (existing_trait + secondary_trait_impact).value
            else:
                self.secondary_traits.append(Trait(secondary_trait_impact.name, secondary_trait_impact.value))

        # Update stress
        self.current_stress = max(0, min(100, self.current_stress + memory.stress_impact))

        # Save changes
        self.save()

    def delete(self) -> None:
        """Delete life and all associated data from database"""
        try:
            # Delete associated data first
            from .memory import memories
            from .character import characters
            from .story import stories
            
            # Delete all associated memories
            memories.delete_many({'life_id': self._id})
            
            # Delete all associated characters
            characters.delete_many({'life_id': self._id})
            
            # Delete all associated stories
            stories.delete_many({'life_id': self._id})
            
            # Finally delete the life itself
            lives.delete_one({'_id': self._id})
            
        except Exception as e:
            raise DatabaseError(f"Error deleting life: {str(e)}")