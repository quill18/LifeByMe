# ./models/game/story_ai_utils.py

import logging
import traceback
from dataclasses import dataclass
from typing import List, Optional
from bson import ObjectId
from openai import OpenAI, OpenAIError
import json

import models.user as user_module
import models.game.life as life_module

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