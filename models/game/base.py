# ./models/game/base.py
from dataclasses import dataclass
from typing import Dict
import random

@dataclass
class Trait:
    name: str
    value: int = 0

    def __add__(self, other: 'Trait') -> 'Trait':
        """Add two Traits together, clamping value to [0, 100]"""
        if self.name != other.name:
            raise ValueError(f"Cannot add traits with different names: {self.name} and {other.name}")
        return Trait(
            name=self.name,
            value=max(0, min(100, self.value + other.value))
        )

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'value': self.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Trait':
        """Create Trait object from dictionary"""
        return cls(
            name=data['name'],
            value=data.get('value', 0)
        )

    @classmethod
    def random(cls, name: str) -> 'Trait':
        """Create a new Trait with a random value between 0 and 100"""
        return cls(
            name=name,
            value=random.randint(0, 100)
        )