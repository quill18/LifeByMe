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

class Season(Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

    def next_season(self) -> 'Season':
        seasons = list(Season)
        current_index = seasons.index(self)
        next_index = (current_index + 1) % len(seasons)
        return seasons[next_index]

