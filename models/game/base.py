# ./models/game/base.py
from dataclasses import dataclass
from typing import Dict
import random

@dataclass
class Ocean:
    openness: int = 0
    conscientiousness: int = 0
    extraversion: int = 0
    agreeableness: int = 0
    neuroticism: int = 0

    @classmethod
    def random(cls) -> 'Ocean':
        """Create a new Ocean object with random values between -10 and 10"""
        return cls(
            openness=random.randint(-10, 10),
            conscientiousness=random.randint(-10, 10),
            extraversion=random.randint(-10, 10),
            agreeableness=random.randint(-10, 10),
            neuroticism=random.randint(-10, 10)
        )

    def __add__(self, other: 'Ocean') -> 'Ocean':
        """Add two Ocean objects together, clamping values to [-10, 10]"""
        return Ocean(
            openness=max(-10, min(10, self.openness + other.openness)),
            conscientiousness=max(-10, min(10, self.conscientiousness + other.conscientiousness)),
            extraversion=max(-10, min(10, self.extraversion + other.extraversion)),
            agreeableness=max(-10, min(10, self.agreeableness + other.agreeableness)),
            neuroticism=max(-10, min(10, self.neuroticism + other.neuroticism))
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for database storage"""
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Ocean':
        """Create Ocean object from dictionary"""
        return cls(
            openness=data.get('openness', 0),
            conscientiousness=data.get('conscientiousness', 0),
            extraversion=data.get('extraversion', 0),
            agreeableness=data.get('agreeableness', 0),
            neuroticism=data.get('neuroticism', 0)
        )
    
    def has_changes(self) -> bool:
        """Check if any OCEAN values are non-zero"""
        return any(value != 0 for value in self.to_dict().values())

@dataclass
class Trait:
    name: str
    value: int = 0

    def __add__(self, other: 'Trait') -> 'Trait':
        """Add two Traits together, clamping value to [-10, 10]"""
        if self.name != other.name:
            raise ValueError(f"Cannot add traits with different names: {self.name} and {other.name}")
        return Trait(
            name=self.name,
            value=max(-10, min(10, self.value + other.value))
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