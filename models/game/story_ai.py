# ./models/game/story_ai.py

import logging
from typing import Dict, List, Tuple, Optional
from .life import Life

logger = logging.getLogger(__name__)

class StoryResponse:
    def __init__(self, story_text: str, options: List[str]):
        self.story_text = story_text
        self.options = options

def story_begin(life: Life) -> StoryResponse:
    """Generate the first beat of a new story"""
    logger.info(f"Starting new story for life {life._id}")
    
    try:
        # TODO: Implement actual OpenAI API call here
        # For now, return dummy data
        return StoryResponse(
            story_text="You're sitting in class when you notice a folded piece of paper on your desk. It wasn't there a moment ago.",
            options=[
                "Quickly open it while the teacher isn't looking",
                "Wait until class is over to read it",
                "Look around to see who might have put it there"
            ]
        )
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise
