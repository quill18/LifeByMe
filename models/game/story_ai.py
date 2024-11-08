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

gpt_model = "gpt-4o-mini"

@dataclass
class StoryResponse:
    story_text: str
    options: List[str]

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
                    "description": "List of 3 response options if the story continues, empty if this is the conclusion"
                }
            },
            "required": ["story_text", "options"]
        }
    }
}]

def begin_story(life: Life) -> StoryResponse:
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

        print(prompt)

        
        # Make API call
        response = client.chat.completions.create(
            model=gpt_model,
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
            options=[clean_text_for_json(opt) for opt in result["options"]]        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode error: {str(e)}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        print(result)
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
            model=gpt_model,
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
            options=[clean_text_for_json(opt) for opt in result["options"]]        )
        
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
            model=gpt_model,
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
            options=None
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode error: {str(e)}")
        raise ValueError(f"Failed to parse AI response: {str(e)}")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error concluding story: {str(e)}")
        raise


def build_character_summary(life: Life) -> str:
    """Create a concise character summary for the AI"""
    gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
    
    traits_desc = []
    for trait in life.ocean.to_dict().items():
        traits_desc.append(f"{trait[0]}: {trait[1]}")
    
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

def build_intensity_guidelines(intensity: Intensity) -> str:
    """Get detailed intensity guidelines based on user selection"""
    if intensity == Intensity.LIGHT:
        return """This story should maintain a LIGHT intensity level. Keep the tone optimistic and uplifting. Focus on positive personal growth and achievements. Handle conflicts through communication and understanding. Avoid topics that could be triggering or distressing. Use humor and warmth appropriately. Keep any romance at a sweet, innocent level."""
    
    elif intensity == Intensity.MODERATE:
        return """This story should maintain a MODERATE intensity level. Balance lighter moments with meaningful challenges. Allow for both success and setbacks. Include realistic interpersonal conflicts. Touch on serious topics without dwelling on them. Show consequences for actions while maintaining hope. Handle romance at a realistic but tasteful level. Allow for some anxiety and stress in reasonable amounts. Keep darker elements brief and resolution-focused."""
    
    else:  # GRITTY
        return """This story should maintain a GRITTY intensity level. Present realistic challenges without guaranteed resolution. Allow for meaningful failures and their consequences. Explore complex emotional and interpersonal situations. Address serious real-world issues directly. Handle romance, relationships, and sexuality realistically. Include genuine struggles with identity and values. Don't shy away from internal conflicts and doubts. Remember that growth can come from difficulty."""

def build_base_prompt(life: Life) -> str:
    """Build the base system prompt for all story interactions"""
    character_summary = build_character_summary(life)
    intensity_guidelines = build_intensity_guidelines(life.intensity)
    
    return f"""You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate story beats that feel natural and personal to the character. Use direct, active, language - preferring a simple and straightforward writing style rather than flowerly or prosaic text.

Character Information:
{character_summary}

Intensity Guidelines: {intensity_guidelines}

Story Guidelines:
1. Incorporate {life.name}'s personality traits naturally:
   - Traits range from +10 to -10
   - Traits closer to the extreme values of +10 or -10 should have a greater impact on story beat generation and the options available to the player.
   - Traits are not necessarily inheritently good or bad. Events that would encourage behaviour inline with or opposed to the character's trait values are neither good nor bad.
   - Actions that align with a character's traits represent the character's natural, instinctive response to events, but could represent complacency. Actions counter to a character's traits could be a tremendous source of stress, but could represent an opportunity to grow or change.

2. Consider stress levels:
   - Current stress affects emotional reactions
   - High stress (>70) makes challenges harder. When highly stress, consider offering options that represent a "mental breakdown" inline with a character's traits that might provide a large stress relief even at the cost of a negative outcome to the story. (e.g. a high school student deciding to blow off studying for an exame to play video games instead)
   - Low stress (<30) allows for more resilient responses, including opportunities to push the characters limits (even counter to traits) for greater success

3. Story elements should:
   - Feel natural and age-appropriate
   - Be creative and varied. Avoid duplicating events similar to those already in Memories
   - Include small details that make the scene feel real
   - Consider the character's life stage and circumstances

4. Create opportunities for:
   - {life.name}'s character growth
   - Relationship development
   - Skill improvement
   - Memory formation

5. Always maintain the selected intensity level - never exceed it

6. Limit the story text length of each beat to a single paragraph. Make sure the story_text doesn't include the options

7. Stories will occur over three beats, representing a beginning, middle, and conclusion"""


def build_story_begin_prompt(life: Life) -> str:
    """Build the complete prompt for starting a new story"""
    base_prompt = build_base_prompt(life)
    
    begin_specific = f"""
Story Beginning Guidelines:
- Start with a clear, immediate situation
- Present something slightly unusual or interesting
- Avoid starting with internal monologue

Your response must use the provided function to return:
- A clear story_text describing the initial situation. If {life.name} is highly stressed (> 70), the situation should reflect that and feel more challenging.
- Separate from the story_text, also return 3 distinct response options that {life.name} could take. Make options feel meaningfully different and could lead the story in different directions. Options that align with {life.name}'s traits may feel comfortable and reduce stress. Options that conflict with {life.name}'s traits may provide opportunites for change, but could cause stress. Include at least one option that correlates to {life.name}'s personality and at least one option that conflicts with {life.name}'s personality.
- DO NOT mentioning the options in the main story_text as it would be redundant"""

    return base_prompt + begin_specific

def build_story_continue_prompt(life: Life) -> str:
    """Build the prompt for continuing a story"""
    base_prompt = build_base_prompt(life)
    
    continue_specific = f"""
Story Continuation Guidelines:
- React naturally to the player's choice
- Show immediate and potential long-term consequences
- Keep the narrative flowing smoothly
- Consider previous story beats when crafting the response
- Maintain consistent characterization

Your response must use the provided function to return:
- A clear story_text describing what happened based on the previous choice made
- Separate from the story_text, also return 3 distinct response options that {life.name} could take. Make options feel meaningfully different and include a mix of options that both align with and run counter to various personality traits. Include one option that seems less likely to 'successfully' resolve the situation, but leans more heavily into the player characters's traits in a way that might reduce stress.
- DO NOT mentioning the options in the main story_text as it would be redundant"""
    return base_prompt + continue_specific


def build_story_conclusion_prompt(life: Life) -> str:
    """Build the prompt for concluding a story"""
    base_prompt = build_base_prompt(life)
    
    continue_specific = """
Story Conclusion Guidelines:
- React naturally to the player's choice
- Show immediate and potential long-term consequences
- Keep the narrative flowing smoothly
- Consider previous story beats when crafting the response
- Maintain consistent characterization

Your response must use the provided function to return:
- Story text concluding this sequence
- ZERO response options"""
    return base_prompt + continue_specific









MEMORY_TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_memory",
        "description": "Create a memory from a completed story",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short, specific title for the memory (e.g., 'First Day Speech Disaster', 'Standing Up to the Bully')"
                },
                "description": {
                    "type": "string",
                    "description": "Concise but detailed description of the memory"
                },
                "importance": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "How important this memory is (1-10)"
                },
                "permanence": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "How permanent this memory is (1-10)"
                },
                "emotional_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of emotions felt during this memory (e.g., 'proud', 'anxious', 'relieved')"
                },
                "context_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of situational/location tags (e.g., 'school', 'public speaking', 'exam')"
                },
                "story_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of story-type tags (e.g., 'coming of age', 'first love', 'overcoming fear')"
                },
                "ocean_changes": {
                    "type": "object",
                    "properties": {
                        "openness": {"type": "integer", "minimum": -2, "maximum": 2},
                        "conscientiousness": {"type": "integer", "minimum": -2, "maximum": 2},
                        "extraversion": {"type": "integer", "minimum": -2, "maximum": 2},
                        "agreeableness": {"type": "integer", "minimum": -2, "maximum": 2},
                        "neuroticism": {"type": "integer", "minimum": -2, "maximum": 2}
                    },
                    "required": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                },
                "trait_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer", "minimum": -2, "maximum": 2}
                        },
                        "required": ["name", "value"]
                    }
                },
                "skill_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer", "minimum": -2, "maximum": 2}
                        },
                        "required": ["name", "value"]
                    }
                },
                "character_changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character_id": {"type": "string"},
                            "friendship_change": {"type": "integer", "minimum": -2, "maximum": 2},
                            "romance_change": {"type": "integer", "minimum": -2, "maximum": 2},
                            "conflict_change": {"type": "integer", "minimum": -2, "maximum": 2}
                        },
                        "required": ["character_id"]
                    }
                },
                "stress_change": {
                    "type": "integer",
                    "minimum": -50,
                    "maximum": 50,
                    "description": "Change in stress level (-50 to +50)"
                }
            },
            "required": [
                "title", "description", "importance", "permanence", 
                "emotional_tags", "context_tags", "story_tags", 
                "ocean_changes", "stress_change"
            ]
        }
    }
}]


def generate_memory_from_story(life: Life, story: Story) -> Dict:
    """Generate memory parameters from a concluded story"""
    logger.info(f"Generating memory for story {story._id}")
    
    try:
        # Get API key from user profile
        user = User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")

        # Initialize OpenAI client
        client = OpenAI(api_key=user.openai_api_key)
        
        # Build story context
        story_context = "\n\n".join([
            "Story progression:",
            *[f"Beat: {clean_text_for_json(beat)}\nResponse: {clean_text_for_json(response) if response else 'Final beat'}" 
              for beat, response in story.beats]
        ])
        
        # Build prompt
        prompt = build_memory_generation_prompt(life)
        
        # Make API call
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""
Story context:
{story_context}

Generate a memory based on this story."""}
            ],
            tools=MEMORY_TOOLS,
            tool_choice={"type": "function", "function": {"name": "create_memory"}}
        )
        
        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)
        
        # Store memory parameters in story
        story.store_memory_params(
            title=result["title"],
            description=result["description"],
            params=result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating memory: {str(e)}")
        raise


def build_memory_generation_prompt(life: Life) -> str:
    """Build the prompt for memory generation from a story"""
    # Modify the character summary function first
    def build_character_summary(life: Life) -> str:
        """Create a concise character summary for the AI"""
        gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
        
        traits_desc = []
        for trait in life.ocean.to_dict().items():
            traits_desc.append(f"{trait[0]}: {trait[1]}")
        
        summary = [
            f"{life.name} is a {life.age}-year-old {gender_desc} in {life.life_stage.value}.",  # Use .value here
            f"Personality: {', '.join(traits_desc)}" if traits_desc else None,
            f"Current stress level: {life.current_stress}/100",
            f"Game intensity: {life.intensity.value}",  # Use .value here
            f"Game difficulty: {life.difficulty.value}"  # Use .value here
        ]
        
        if life.custom_directions:
            summary.append(f"Special character notes: {life.custom_directions}")
            
        return "\n".join(filter(None, summary))

    character_summary = build_character_summary(life)
    
    return f"""You are analyzing a concluded story to determine its effects on the character and create a memory of what happened. Your task is to interpret the story's events and their impact on {life.name}.

Character Information:
{character_summary}

Guidelines for Memory Generation:

1. Memory Creation:
   - Generate a concise but meaningful title
   - Write a clear, specific description that captures the key moments
   - Importance (1-10) should reflect how much this event matters to {life.name}. 1=absolute triviality that is only worth noting for story consistency. 5=something that might surface one a month. 10=something of critical importance that weighs heavily on the mind even if only temporarily
   - Permanence (1-10) should reflect how long this memory will matter. 1=short term, only matters for the current season (e.g. an upcoming test, a recent insult). 5=matters throughout the current life stage (e.g. meeting someone new, winning a school debate). 10=permanent core memory, never forgotten (e.g. death of a friend, first kiss)
   - For example: Failing or passing an exam at school could be immediately very important (Importance 10), but be a fleeting memory that won't matter next season (Permanence 1). Getting a pet would be relatively meaningful but not affect many day-to-day events (Importance 6) and be something with fairly long-term effects (Permanence 8).
   - Tags should be specific and meaningful

2. Impact Guidelines:
   - Individual trait changes cannot exceed +2 or -2
   - Consider both direct effects and subtle influences
   - Not every story needs to affect every aspect
   - Changes should feel natural given the story events
   - One new secondary trait can be suggested if appropriate, and it can start from a value from +2 to -2
   - Stress changes can range from -50 to +50. Success level of the conclusion has an impact on stress, but the biggest consideration should be if the choices the players made were aligned with the characters traits (doing what comes "naturally" isn't stressful) or if the choices run counter to the character's traits (especially the OCEAN traits), because going against one's nature is stressful even if it leads to character development.

3. Tag Selection:
   - Emotional tags should reflect the character's feelings
   - Context tags should capture the situation and setting
   - Story tags should identify the type of experience (e.g., "coming of age", "first love", "personal triumph")

4. Character Development:
   - Consider how choices aligned with or challenged current traits
   - Account for the difficulty and intensity settings
   - Consider current stress levels when determining impact
   - Think about long-term character development

Process the story and create a memory that captures both what happened and how it affected {life.name}."""
