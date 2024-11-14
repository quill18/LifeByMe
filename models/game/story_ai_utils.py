# ./models/game/story_ai_utils.py

import logging
import traceback
from dataclasses import dataclass
from typing import List, Optional
from bson import ObjectId
from openai import OpenAI, OpenAIError
import json
from typing import Dict, List, Tuple

import models.user as user_module
import models.game.life as life_module
from models.game.enums import Difficulty

logger = logging.getLogger(__name__)

@dataclass
class StoryResponse:
    """Response object for story generation functions"""
    prompt: Optional[str]
    story_text: str
    options: Optional[List[str]]
    character_ids: Optional[List[ObjectId]]

def create_openai_client(life: 'life_module.Life') -> tuple[OpenAI, str]:
    """Create an OpenAI client for the given life's user
    
    Args:
        life: The Life object whose user's API key should be used
        
    Returns:
        tuple[OpenAI, str]: Configured OpenAI client and the model to use
        
    Raises:
        ValueError: If no API key is available
        OpenAIError: If client creation fails
    """
    try:
        user = user_module.User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")
            
        return OpenAI(api_key=user.openai_api_key), user.gpt_model
        
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}\n{traceback.format_exc()}")
        raise

def clean_text_for_json(text: str) -> str:
    """Clean text to ensure it's valid for JSON encoding
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    return text

def handle_openai_error(func):
    """Decorator to standardize OpenAI error handling with logging"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OpenAIError as e:
            logger.error(f"OpenAI API error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
            raise
        except ValueError as e:
            logger.error(f"Value error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
            raise
    return wrapper

def parse_openai_response(response, function_name: str) -> dict:
    """Parse OpenAI function call response
    
    Args:
        response: OpenAI API response
        function_name: Expected function name
        
    Returns:
        dict: Parsed response arguments
        
    Raises:
        ValueError: If response parsing fails
    """
    try:
        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.function.name != function_name:
            raise ValueError(f"Unexpected function name: {tool_call.function.name}")
            
        try:
            return json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error. Raw response: {tool_call.function.arguments}")
            logger.error(f"Error details: {str(e)}\n{traceback.format_exc()}")
            # Attempt to clean and retry
            cleaned_args = clean_text_for_json(tool_call.function.arguments)
            return json.loads(cleaned_args)
            
    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {str(e)}\n{traceback.format_exc()}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    
def calculate_weighted_trait_value(old_value: int, calculated_value: int, importance: int, permanence: int) -> int:
    """Calculate new trait value using weighted average.
    
    Args:
        old_value: Current trait value (0-100)
        calculated_value: AI calculated trait value from story (0-100)
        importance: Memory importance (1-3)
        permanence: Memory permanence (1-3)
        
    Returns:
        New trait value (0-100)
    """
    # Start with weight of 12 and subtract importance and permanence
    old_value_weight = 8 - importance - permanence
    
    # Weighted average
    new_value = (calculated_value + (old_value * old_value_weight)) / (1 + old_value_weight)
    
    # Ensure result is between 0 and 100
    return max(0, min(100, round(new_value)))

def calculate_trait_change_stress(primary_traits: Dict[str, int], analyzed_traits: List[Dict]) -> int:
    """Calculate stress from trait differences.
    
    Args:
        primary_traits: Dict of current trait values
        analyzed_traits: List of dicts with 'name' and 'calculated_value' keys
        
    Returns:
        Stress value from trait differences (0-100)
    """
    total_difference = 0
    for trait in analyzed_traits:
        current_value = primary_traits.get(trait['name'], 0)
        calculated_value = trait['calculated_value']
        difference = abs(current_value - calculated_value)
        total_difference += difference
    
    # Divide by 6 (number of primary traits) to normalize the stress value
    #return min(100, round(total_difference / 6))
    return total_difference

def adjust_trait_stress_for_difficulty(stress: int, difficulty: Difficulty) -> int:
    """Adjust trait-based stress based on difficulty setting.
    
    Args:
        stress: Base stress value (0-100)
        difficulty: Game difficulty setting
        
    Returns:
        Adjusted stress value (0-100)
    """
    if difficulty == Difficulty.STORY:
        return round(stress / 2)
    elif difficulty == Difficulty.CHALLENGING:
        return min(100, round(stress * 2))
    return stress  # No adjustment for BALANCED difficulty

def calculate_final_stress(current_stress: int, story_stress: int, 
                         trait_stress: int, difficulty: Difficulty) -> int:
    """Calculate final stress value using weighted average.
    
    Args:
        current_stress: Player's current stress level (0-100)
        story_stress: AI calculated story stress (0-100)
        trait_stress: Stress from trait differences (0-100)
        difficulty: Game difficulty setting
        
    Returns:
        New stress value (0-100)
    """
    # Adjust trait stress based on difficulty
    adjusted_trait_stress = adjust_trait_stress_for_difficulty(trait_stress, difficulty)
    
    # Weights: current_stress(5), story_stress(3), trait_stress(1)
    weighted_value = (
        (current_stress * 5) + 
        (story_stress * 3) + 
        (adjusted_trait_stress * 1)
    ) / 9
    
    return max(0, min(100, round(weighted_value)))

def process_trait_analysis(
    current_traits: Dict[str, int],
    analyzed_traits: List[Dict],
    importance: int,
    permanence: int
) -> Tuple[List[Dict], List[Dict]]:
    """Process trait analysis and calculate changes.
    
    Args:
        current_traits: Dict of current trait values
        analyzed_traits: List of dicts with trait analysis from AI
        importance: Memory importance (1-3)
        permanence: Memory permanence (1-3)
        
    Returns:
        Tuple of (calculated_traits, trait_changes)
        - calculated_traits: List of dicts with name, calculated_value, and reasoning
        - trait_changes: List of dicts with name and final change value
    """
    calculated_traits = []
    trait_changes = []
    
    logger.debug(f"Analyzing traits: {analyzed_traits}")
    logger.debug(f"Current traits: {current_traits}")

    try:
        for trait_analysis in analyzed_traits:
            if isinstance(trait_analysis, str):
                logger.error(f"Received string instead of dict for trait analysis: {trait_analysis}")
                continue
                
            if not isinstance(trait_analysis, dict):
                logger.error(f"Invalid trait analysis type: {type(trait_analysis)}")
                continue
                
            try:
                name = trait_analysis.get('name')
                calculated_value = trait_analysis.get('calculated_value')
                reasoning = trait_analysis.get('reasoning')
                
                if not all([name, calculated_value is not None, reasoning]):
                    logger.error(f"Missing required fields in trait analysis: {trait_analysis}")
                    continue
                
                current_value = current_traits.get(name, 0)
                
                # Calculate new value using weighted average
                new_value = calculate_weighted_trait_value(
                    current_value, 
                    calculated_value,
                    importance,
                    permanence
                )
                
                # Store the calculated trait analysis
                calculated_traits.append({
                    'name': name,
                    'calculated_value': calculated_value,
                    'reasoning': reasoning
                })
                
                # Store the actual change that will be applied
                trait_changes.append({
                    'name': name,
                    'value': new_value - current_value
                })
                
            except Exception as e:
                logger.error(f"Error processing trait analysis: {str(e)}\nTrait data: {trait_analysis}")
                continue
            
    except Exception as e:
        logger.error(f"Error in process_trait_analysis: {str(e)}")

    return calculated_traits, trait_changes

def process_memory_response(
    response: Dict,
    current_traits: Dict[str, int],
    current_stress: int,
    difficulty: Difficulty
) -> Dict:
    """Process memory generation response and calculate all changes.
    
    Args:
        response: Raw AI response
        current_traits: Dict of current trait values
        current_stress: Current stress level
        difficulty: Game difficulty setting
        
    Returns:
        Dict containing all processed values and changes
    """
    # Process trait analysis
    calculated_traits, trait_changes = process_trait_analysis(
        current_traits,
        response['trait_analysis']['analyzed_traits'],
        response['importance'],
        response['permanence']
    )
    
    # Calculate stress changes
    trait_stress = calculate_trait_change_stress(
        current_traits,
        response['trait_analysis']['analyzed_traits']
    )
    
    final_stress = calculate_final_stress(
        current_stress,
        response['story_stress'],
        trait_stress,
        difficulty
    )
    
    stress_change = final_stress - current_stress
    
    # Update response with calculated values
    processed_response = response.copy()
    processed_response.update({
        'calculated_traits': calculated_traits,
        'primary_trait_changes': trait_changes,
        'trait_change_stress': trait_stress,
        'final_stress': final_stress,
        'stress_change': stress_change
    })
    
    return processed_response
