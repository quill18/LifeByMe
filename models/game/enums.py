# ./models/game/enums.py
from enum import Enum

class LifeStage(Enum):
    HIGH_SCHOOL = "High School"
    COLLEGE = "College"
    CAREER = "Career"
    RETIRED = "Retired"
    CHILDHOOD = "Childhood"

class Intensity(Enum):
    LIGHT = "Light"
    MODERATE = "Moderate"
    GRITTY = "Gritty"

class Difficulty(Enum):
    STORY = "Story"
    BALANCED = "Balanced"
    CHALLENGING = "Challenging"
