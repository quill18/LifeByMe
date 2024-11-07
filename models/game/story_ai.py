# ./models/game/story_ai.py

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from openai import OpenAI, OpenAIError
from .life import Life
from .memory import Memory
from models.user import User
from models.game.enums import LifeStage, Intensity, Difficulty
from models.game.story import Story
import re


logger = logging.getLogger(__name__)

@dataclass
class StoryResponse:
    story_text: str
    options: List[str]
    completed: bool

def get_character_summary(life: Life) -> str:
    """Create a concise character summary for the AI"""
    gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
    
    traits_desc = []
    for trait in life.ocean.to_dict().items():
        if trait[1] != 0:  # Only include non-zero traits
            level = "high" if trait[1] > 5 else "low" if trait[1] < -5 else "moderate"
            if trait[1] < 0:
                level = f"low ({trait[1]})"
            else:
                level = f"high ({trait[1]})"
            traits_desc.append(f"{trait[0]}: {level}")
    
    summary = [
        f"{life.name} is a {life.age}-year-old {gender_desc} in {life.life_stage.value}.",
        f"Personality: {', '.join(traits_desc)}" if traits_desc else None,
        f"Current stress level: {life.current_stress}/100",
        f"Game intensity: {life.intensity.value}",
        f"Game difficulty: {life.difficulty.value}"
    ]
    
    if life.custom_directions:
        summary.append(f"Special character notes: {life.custom_directions}")
        
    return "\n".join(filter(None, summary))

def get_intensity_guidelines(intensity: Intensity) -> str:
    """Get detailed intensity guidelines based on user selection"""
    if intensity == Intensity.LIGHT:
        return """This story should maintain a LIGHT intensity level:
- Keep the tone optimistic and uplifting
- Focus on positive personal growth and achievements
- Handle conflicts through communication and understanding
- Avoid topics that could be triggering or distressing
- Include gentle challenges that can be overcome
- Focus on friendship, family, and personal discovery
- Use humor and warmth appropriately
- Keep any romance at a sweet, innocent level
- Resolve situations without lasting negative consequences"""
    
    elif intensity == Intensity.MODERATE:
        return """This story should maintain a MODERATE intensity level:
- Balance lighter moments with meaningful challenges
- Allow for both success and setbacks
- Include realistic interpersonal conflicts
- Touch on serious topics without dwelling on them
- Show consequences for actions while maintaining hope
- Handle romance at a realistic but tasteful level
- Include emotional growth through moderate challenges
- Allow for some anxiety and stress in reasonable amounts
- Keep darker elements brief and resolution-focused"""
    
    else:  # GRITTY
        return """This story should maintain a GRITTY intensity level:
- Present realistic challenges without guaranteed resolution
- Allow for meaningful failures and their consequences
- Explore complex emotional and interpersonal situations
- Address serious real-world issues directly
- Show the impact of choices on relationships and future
- Handle romance, relationships, and sexuality realistically
- Include genuine struggles with identity and values
- Don't shy away from internal conflicts and doubts
- Remember that growth can come from difficulty"""

def build_story_system_prompt(life: Life) -> str:
    """Build the base system prompt for all story interactions"""
    character_summary = get_character_summary(life)
    intensity_guidelines = get_intensity_guidelines(life.intensity)
    
    return f"""You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate story beats that feel natural and personal to the character.

Character Information:
{character_summary}

Intensity Guidelines:
{intensity_guidelines}

Story Guidelines:
1. Incorporate {life.name}'s personality traits naturally:
   - Traits range from +10 to -10
   - Positive trait values should influence behavior and reactions
   - Negative trait values should create interesting internal conflicts
   - Neutral traits (0) should not be emphasized

2. Consider stress levels:
   - Current stress affects emotional reactions
   - High stress (>70) makes challenges harder
   - Low stress (<30) allows for more resilient responses

3. Story elements should:
   - Feel natural and age-appropriate
   - Avoid clichéd or overly dramatic scenarios
   - Include small details that make the scene feel real
   - Consider the character's life stage and circumstances

4. Create opportunities for:
   - {life.name}'s character growth
   - Relationship development
   - Skill improvement
   - Memory formation

5. Always maintain the selected intensity level - never exceed it.

6. Limit the story text length of each beat to a single paragraph.

7. Create natural decision points"""


def build_story_begin_prompt(life: Life) -> str:
    """Build the complete prompt for starting a new story"""
    base_prompt = build_story_system_prompt(life)
    
    begin_specific = """
Story Beginning Guidelines:
- Start with a clear, immediate situation
- Present something slightly unusual or interesting
- Avoid starting with internal monologue

Your response must use the provided function to return:
- A clear story text describing the initial situation
- You must include 3 distinct response options that {life.name} could take. Make options feel meaningfully different. Options that align with {life.name}'s traits may feel comfortable and reduce stress. Options that conflict with {life.name}'s traits may provide opportunites for change, but could cause stress.
- Include at least one option that correlates to {life.name}'s personality and at least one option that conflicts with {life.name}'s personality."""

    return base_prompt + begin_specific

def build_story_continue_prompt(life: Life) -> str:
    """Build the prompt for continuing a story"""
    base_prompt = build_story_system_prompt(life)
    
    continue_specific = """
Story Continuation Guidelines:
- React naturally to the player's choice
- Show immediate and potential long-term consequences
- Keep the narrative flowing smoothly
- Consider previous story beats when crafting the response
- Maintain consistent characterization
- Create natural opportunities for the story to conclude when appropriate
- Consider if this is a good place to conclude the story

Your response must use the provided function to return:
- Story text describing what happens next
- Unless the story is concluding, you must include 3 distinct response options that {life.name} could take. Make options feel meaningfully different
- Whether this beat concludes the story. The story must complete no later than the 3rd beat."""
    return base_prompt + continue_specific


def build_story_conclusion_prompt(life: Life) -> str:
    """Build the prompt for concluding a story"""
    base_prompt = build_story_system_prompt(life)
    
    continue_specific = """
Story Conclusion Guidelines:
- React naturally to the player's choice
- Show immediate and potential long-term consequences
- Keep the narrative flowing smoothly
- Consider previous story beats when crafting the response
- Maintain consistent characterization

Your response must use the provided function to return:
- Story text concluding this sequence
- ZERO response options
- completed must be set to true"""
    return base_prompt + continue_specific

# Tool definition for OpenAI's function calling
STORY_TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_story_beat",
        "description": "Create a story beat with text and response options",
        "parameters": {
            "type": "object",
            "properties": {
                "story_text": {
                    "type": "string",
                    "description": "The narrative text describing what happens in this story beat"
                },
                "options": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of 3 response options if the story continues, empty if complete"
                },
                "completed": {
                    "type": "boolean",
                    "description": "Whether this beat concludes the story"
                }
            },
            "required": ["story_text", "options", "completed"]
        }
    }
}]

def story_begin(life: Life) -> StoryResponse:
    """Generate the first beat of a new story"""
    logger.info(f"Starting new story for life {life._id}")
    
    try:
        # Get API key from user profile
        user = User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")

        # Initialize OpenAI client
        client = OpenAI(api_key=user.openai_api_key)
        
        # Build prompt
        prompt = build_story_begin_prompt(life)
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o",  # or whatever model you prefer
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Begin a new story for this character."}
            ],
            tools=STORY_TOOLS,
            tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
        )
        
        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        
        try:
            result = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error. Raw response: {tool_call.function.arguments}")
            logger.error(f"Error details: {str(e)}")
            # Attempt to clean and retry
            cleaned_args = clean_text_for_json(tool_call.function.arguments)
            result = json.loads(cleaned_args)
        
        # Create and return StoryResponse - clean the text values
        return StoryResponse(
            story_text=clean_text_for_json(result["story_text"]),
            options=[clean_text_for_json(opt) for opt in result["options"]],
            completed=result["completed"]
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode error: {str(e)}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise



def clean_text_for_json(text: str) -> str:
    """Clean text to ensure it's valid for JSON encoding"""
    if not text:
        return ""
    
    # Testing to see if this is still required:
    return text
    
    # Replace common problematic characters
    text = text.replace('\n', '<p>')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    
    # Remove other control characters except newlines we just escaped
    text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', '', text)
    
    return text

def continue_story(life: Life, story: Story, selected_option: str) -> StoryResponse:
    """Generate the next beat of an ongoing story"""
    logger.info(f"Continuing story for life {life._id}")
    
    try:
        # Get API key from user profile
        user = User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")

        # Initialize OpenAI client
        client = OpenAI(api_key=user.openai_api_key)
        
        # Build the story context - clean the text
        story_context = "\n\n".join([
            "Previous story beats:",
            *[f"Beat: {clean_text_for_json(beat)}\nResponse: {clean_text_for_json(response) if response else 'Current beat'}" 
              for beat, response in story.beats]
        ])
        
        # Build prompt
        prompt = build_story_continue_prompt(life)
        
        print("Making API Call")
        print(prompt)
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o",  # or whatever model you prefer
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""
Story context:
{story_context}

Player chose: {clean_text_for_json(selected_option)}

Continue or conclude the story based on this choice."""}
            ],
            tools=STORY_TOOLS,
            tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
        )
        
        print("API call complete")
        print(response)
        
        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        
        try:
            result = json.loads(tool_call.function.arguments, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error. Raw response: {tool_call.function.arguments}")
            logger.error(f"Error details: {str(e)}")
            # Attempt to clean and retry
            cleaned_args = clean_text_for_json(tool_call.function.arguments)
            result = json.loads(cleaned_args, strict=False)
        
        # Create and return StoryResponse - clean the text values
        return StoryResponse(
            story_text=clean_text_for_json(result["story_text"]),
            options=[clean_text_for_json(opt) for opt in result["options"]],
            completed=result["completed"]
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode error: {str(e)}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error continuing story: {str(e)}")
        raise

def conclude_story(life: Life, story: Story, selected_option: str) -> StoryResponse:
    """Generate the concluding beat of a story"""
    logger.info(f"Concluding story for life {life._id}")
    
    try:
        # Get API key from user profile
        user = User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")

        # Initialize OpenAI client
        client = OpenAI(api_key=user.openai_api_key)
        
        # Build the story context - clean the text
        story_context = "\n\n".join([
            "Previous story beats:",
            *[f"Beat: {clean_text_for_json(beat)}\nResponse: {clean_text_for_json(response) if response else 'Current beat'}" 
              for beat, response in story.beats]
        ])
        
        # Build prompt
        prompt = build_story_conclusion_prompt(life)
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o",  # or whatever model you prefer
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""
Story context:
{story_context}

Player chose: {clean_text_for_json(selected_option)}

Conclude the story based on this choice."""}
            ],
            tools=STORY_TOOLS,
            tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
        )
        
        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        
        try:
            result = json.loads(tool_call.function.arguments, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error. Raw response: {tool_call.function.arguments}")
            logger.error(f"Error details: {str(e)}")
            # Attempt to clean and retry
            cleaned_args = clean_text_for_json(tool_call.function.arguments)
            result = json.loads(cleaned_args, strict=False)
        
        # Create and return StoryResponse - clean the text values
        return StoryResponse(
            story_text=clean_text_for_json(result["story_text"]),
            options=[clean_text_for_json(opt) for opt in result["options"]],
            completed=result["completed"]
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode error: {str(e)}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error continuing story: {str(e)}")
        raise
