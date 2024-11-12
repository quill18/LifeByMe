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
from models.game.character import Character, RelationshipStatus
from bson import ObjectId
from .memory import Memory
import random
import re


logger = logging.getLogger(__name__)

@dataclass
class StoryResponse:
    prompt: str
    story_text: str
    options: List[str]
    character_ids: List[ObjectId]

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
                    "description": "List of 4 response options if the story continues, empty if this is the conclusion"
                },
                "character_ids": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of character IDs for characters who appear in this story, chosen from the list of Available Characters"
                }
            },
            "required": ["story_text", "options", "character_ids"]
        }
    }
}]

def begin_story(life: Life, custom_story_seed: str) -> StoryResponse:
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
        prompt = build_story_begin_prompt(life, custom_story_seed)

        print(prompt)
        
        # Make API call
        response = client.chat.completions.create(
            model=user.gpt_model,
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
        
        # Create Story object
        #story = Story(
        #    life_id=life._id,
        #    prompt=prompt,
        #    beats=[(clean_text_for_json(result["story_text"]), None)],
        #    current_options=[clean_text_for_json(opt) for opt in result["options"]],
        #    character_ids=[ObjectId(char_id) for char_id in result["character_ids"]]
        #)
        #story.save()
        
        # Create and return StoryResponse
        return StoryResponse(
            prompt=prompt,
            story_text=clean_text_for_json(result["story_text"]),
            options=[clean_text_for_json(opt) for opt in result["options"]],
            character_ids=[ObjectId(char_id) for char_id in result["character_ids"]]
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
        prompt = build_story_continue_prompt(life, story)
        
        print("Making API Call")
        print(prompt)
        # Make API call
        response = client.chat.completions.create(
            model=user.gpt_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""
Story context:
{story_context}

Player chose: {clean_text_for_json(selected_option)}

Continue the story based on this choice."""}
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
            prompt=None,
            story_text=clean_text_for_json(result["story_text"]),
            options=[clean_text_for_json(opt) for opt in result["options"]],
            character_ids=None
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
        prompt = build_story_conclusion_prompt(life, story)
        
        # Make API call
        response = client.chat.completions.create(
            model=user.gpt_model,
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
            prompt=None,
            story_text=clean_text_for_json(result["story_text"]),
            options=None,
            character_ids=None
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
        f"{life.name} is {life.age}-year-old",
        f"Gender: {gender_desc}",
        f"Life Stage: {life.life_stage.value}",
        f"Personality: {', '.join(traits_desc)}" if traits_desc else None,
        f"Current stress level: {life.current_stress}%"
    ]


    if life.custom_directions:
        summary.append(f"Special character notes: {life.custom_directions}")
        
    return "\n".join(filter(None, summary))

def build_intensity_guidelines(intensity: Intensity, difficulty: Difficulty) -> str:
    """Get detailed intensity guidelines based on user selection"""

    intensity_text = ""

    if intensity == Intensity.LIGHT:
        intensity_text =  """This story should maintain a LIGHT intensity level. Keep the tone optimistic and uplifting. Focus on positive personal growth and achievements. Handle conflicts through communication and understanding. Avoid topics that could be triggering or distressing. Use humor and warmth appropriately. Keep any romance at a sweet, innocent level."""
    
    elif intensity == Intensity.MODERATE:
        intensity_text =  """This story should maintain a MODERATE intensity level. Provide meaningful, realistic challenges. Allow for both success and setbacks. Include realistic interpersonal conflicts. Touch on serious topics. Show consequences for actions while maintaining hope. Handle romance at a realistic but tasteful level. Allow for anxiety and stress. Keep darker elements brief and resolution-focused."""
    
    else:  # GRITTY
        intensity_text =  """This story should maintain a GRITTY intensity level. Present realistic challenges without guaranteed resolution. Allow for meaningful failures and their consequences. Explore complex emotional and interpersonal situations. Address serious real-world issues directly. Handle romance, relationships, and sexuality realistically. Include genuine struggles with identity and values. Don't shy away from internal conflicts and doubts. Remember that growth can come from difficulty."""

    if difficulty == Difficulty.STORY:
        intensity_text += """\n\nDifficulty is set to STORY mode. The character should generally succeed at their chosen actions, though the manner and consequences of success may vary. Failures should be rare and primarily serve character development rather than creating serious setbacks. Provide clear paths to achieve desired outcomes. If stress is below 30, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome"""

    elif difficulty == Difficulty.BALANCED:
        intensity_text += """\n\nDifficulty is set to BALANCED mode. Success should depend on how well the chosen action aligns with the character's traits and previous development. Actions that go against type should be notably harder to succeed at. Include a mix of successes and setbacks, with neither dominating the narrative. If stress is below 50, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome"""

    else:  # CHALLENGING
        intensity_text += """\n\nDifficulty is set to CHALLENGING mode. Success should be earned and never guaranteed. Actions that go against the character's established traits can still succeed, but at the cost of personal stress. Create meaningful obstacles that require careful choice selection. Let failures have lasting impact, though allow for eventual recovery and growth. If stress is below 70, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome."""


    return intensity_text

def build_base_prompt(life: Life) -> str:
    """Build the base system prompt for all story interactions"""
    character_summary = build_character_summary(life)
    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    memories_json = Memory.format_memories_for_ai(life._id)
    
    return f"""You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate story beats that feel natural and personal to the character. Use direct, active, language - preferring a simple and straightforward writing style rather than flowerly or prosaic text. Write in present tense.

Character Information:
{character_summary}

Intensity & Difficulty Guidelines: {intensity_guidelines}

Character's Memory History, in chronological order:
{memories_json}

Make sure the player is experiencing a variety of different events, while also sometimes revisiting previous plot points - especially if they are important, life-affecting moments.

Story Guidelines:
1. Incorporate {life.name}'s personality traits naturally:
   - Traits range from +10 to -10
   - Traits closer to the extreme values of +10 or -10 should have a greater impact on story beat generation and the options available to the player.
   - Actions that align with a character's traits represent the character's natural, instinctive response to events, but could represent complacency. Actions counter to a character's traits could be a tremendous source of stress, but could represent an opportunity to grow or change.

2. Consider stress levels:
   - Current stress affects emotional reactions
   - High stress (>70) makes challenges more dramatic. When highly stress, consider offering options that represent a "mental breakdown" inline with a character's traits that might provide a large stress relief even at the cost of a negative outcome to the story. (e.g. a high school student deciding to blow off studying for an exame to play video games instead)

3. Story elements should:
   - Feel natural and age-appropriate
   - Consider the character's life stage and circumstances
   - Occasionally provide options for romance, making sure they are age-appropriate (also consider the Intensity level.)

4. Create opportunities for:
   - {life.name}'s character growth
   - Relationship development
   - Secondary trait development (secondary traits represent: more specific personality traits like 'integrity' or 'artisticness', skills like 'cooking skill' or 'video game skills', and interests/preferences like 'coffee lover')

5. Limit the story text length of each beat to a single short paragraph. Make sure the story_text doesn't include the options

6. Stories will occur over three beats, representing a beginning, middle, and conclusion"""


def build_story_begin_prompt(life: Life, custom_story_seed:str) -> str:
    """Build the complete prompt for starting a new story"""
    base_prompt = build_base_prompt(life)
    
    # Get character information
    characters_json = Character.format_characters_for_ai(life_id=life._id)

    if custom_story_seed:
        custom_story_seed = f"\n\nSTORY SCENARIO: {custom_story_seed}"
    else:
        custom_story_seed = ""
        

    begin_specific = f"""

Available Characters, in JSON format:
{characters_json}
   
Story Beginning Guidelines:
- Start with a clear, immediate situation
- Choose zero, one, or two characters to include in this story from the list of Available Characters. Make sure they are appropriate for the scene, setting, and time of day. Consider if you should include close friends or if the story should include less close or even antagonistic characters. It could even be time for a scene with no characters other than {life.name} by themselves.
- It's okay for some characters to have bad reactions to the player and for the player to fail in some ways. That is more realistic and makes for a more interesting game. Consider Difficulty, Intensity, current Stress, AND RECENT MEMORIES to help determine how positive or negative the event should be, aiming for variety
- Vary between locations (School or Work vs Home, maybe even a friend's home, restaurant, mall, and other locations appropriate for the player's life stage - or relevant to the users personality and interests)

Your response must use the provided function to return:
- A clear story_text describing the initial situation. If {life.name} is highly stressed (> 70), the situation should reflect that and feel more challenging.
- Separate from the story_text, also return 4 distinct response options that {life.name} could take. Make options feel meaningfully different and could lead the story in different directions. Include at least one option that correlates to {life.name}'s personality and at least one option that conflicts with {life.name}'s personality.
- DO NOT mentioning the options in the main story_text as it would be redundant{custom_story_seed}"""

    return base_prompt + begin_specific

def build_story_continue_prompt(life: Life, story: Story) -> str:
    """Build the prompt for continuing a story"""
    base_prompt = build_base_prompt(life)

    # Get character information for characters involved in this story
    #characters_json = Character.format_characters_for_ai(story.character_ids, life_id=life._id)
    characters_json = Character.format_characters_for_ai(life_id=life._id)

    
    continue_specific = f"""
Characters in this story, in JSON format:
{characters_json}

Story Continuation Guidelines:
- React naturally to the player's choice
- It's okay for some characters to have bad reactions to the player and for the player to fail in some ways. That is more realistic and makes for a more interesting game. Consider Difficulty, Intensity, and current Stress to help determine how positive or negative the outcome is
- Consider whether the player's choice is inline or divergent from their personality

Your response must use the provided function to return:
- A clear story_text describing what happened based on the previous choice made
- Separate from the story_text, also return 4 distinct response options that {life.name} could take. Make options feel meaningfully different and could lead the story in different directions. Include at least one option that correlates to {life.name}'s personality and at least one option that conflicts with {life.name}'s personality.
- DO NOT mentioning the options in the main story_text as it would be redundant"""
    return base_prompt + continue_specific


def build_story_conclusion_prompt(life: Life, story: Story) -> str:
    """Build the prompt for concluding a story"""
    base_prompt = build_base_prompt(life)

    #characters_json = Character.format_characters_for_ai(story.character_ids, life_id=life._id)
    characters_json = Character.format_characters_for_ai(life_id=life._id)
    
    continue_specific = """
Characters in this story, in JSON format:
{characters_json}

Story Conclusion Guidelines:
- React naturally to the player's choice
- It's okay for some characters to have bad reactions to the player and for the player to fail in some ways. That is more realistic and makes for a more interesting game. Consider Difficulty, Intensity, and current Stress to help determine how positive or negative the outcome is
- Consider whether the player's choice is inline or divergent from their personality

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
                    "maximum": 3,
                    "description": "How important this memory is (1-3)"
                },
                "permanence": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3,
                    "description": "How permanent this memory is (1-3)"
                },
                "emotional_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of emotions felt during this memory"
                },
                "context_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of situational/location tags"
                },
                "story_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of story-type tags"
                },
                "impact_explanation": {
                    "type": "string",
                    "description": "Brief explanation of why the memory affects primary traits, secondary traits, relationships, and stress levels the way it does - and why you choose the Importance and Permanence you did"
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
                    "description": "One or two secondary traits that have been created or modified by this memory",
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
                    "description": "Characters present in the story that should have their details updated (especially relationship_description)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "The database ID of the character being updated (not their name)"
                            },
                            "physical_description": {
                                "type": "string",
                                "description": "Updated physical description of the character"
                            },
                            "personality_description": {
                                "type": "string",
                                "description": "Updated personality description based on interactions"
                            },
                            "relationship_description": {
                                "type": "string",
                                "description": "Updated description of relationship to the player character. Always begin the relationship description with a sentence specifying the base type of relationship, like 'Father', 'Mother', 'Sister', 'Brother', 'Friend', 'Boss', 'Teacher', 'Girlfriend', 'Husband', and so on - and then a sentence which describes the current state of the relationship."
                            },
                            "relationship_status": {
                                "type": "string",
                                "enum": ["Active", "Departed", "Deceased"],
                                "description": "Updated status of this character"
                            }
                        },
                        "required": ["id", "relationship_description"]
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
                "impact_explanation", "ocean_changes", "stress_change",  "character_changes"
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
        prompt = build_memory_generation_prompt(life, story)

        print(prompt)
        
        # Make API call
        response = client.chat.completions.create(
            model=user.gpt_model,
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


def build_memory_generation_prompt(life: Life, story: Story) -> str:
    """Build the prompt for memory generation from a story"""
    # Modify the character summary function first
    def build_character_summary(life: Life) -> str:
        """Create a concise character summary for the AI"""
        gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
        
        traits_desc = []
        for trait in life.ocean.to_dict().items():
            traits_desc.append(f"{trait[0]}: {trait[1]}")
        
        summary = [
            f"{life.name} is {life.age}-year-old",
            f"Gender: {gender_desc}",
            f"Life Stage: {life.life_stage.value}",
            f"Personality: {', '.join(traits_desc)}" if traits_desc else None,
            f"Current stress level: {life.current_stress}%"
        ]
        
        if life.custom_directions:
            summary.append(f"Special character notes: {life.custom_directions}")
            
        return "\n".join(filter(None, summary))

    character_summary = build_character_summary(life)

    # Get character information for characters involved in this story
    characters_json = Character.format_characters_for_ai(life_id=life._id)

    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    memories_json = Memory.format_memories_for_ai(life._id)
    
    return f"""You are analyzing a concluded story to determine its effects on the character and create a memory of what happened. Your task is to interpret the story's events and their impact on {life.name}.

Character Information:
{character_summary}

Characters in this story, in JSON format - make sure to match the IDs to the correct character.
{characters_json}

Intensity & Difficulty Guidelines: {intensity_guidelines}

Character's Memory History, in chronological order:
{memories_json}

Guidelines for Memory Generation:

1. Memory Creation:
   - Generate a concise but meaningful title
   - Write a clear, specific description that captures the key moments
   - Importance (1-3) should reflect how much this event matters to {life.name}. 1=dealing with typical life events (e.g. going to a party, completing a homework assignment). 2=a significant change in {life.name}'s life (e.g. winning a major award, making a new friend). 3=a critical, life-changing event (e.g. death of a friend, first kiss)
   - Permanence (1-3) should reflect how long this memory will matter. 1=short term, only matters for the current year. 2=matters throughout the current life stage. 3=permanent core memory, never forgotten. Err towards shorter Permanence unless it really matters.
   - Tags should be specific and meaningful

2. Ocean and Secondary Trait Changes Guidelines:
   - Focus on the player's choices for their character. Consider if the player made choices that were inline with or in opposition to their current traits.
   - Consider only one or two Ocean traits that were most significant in the scene
   - Ocean trait changes cannot exceed +2 or -2
   - Modify or create one or two secondary traits. Change (or initalize) the value from +2 to -2. Secondary traits represent more specific personality traits like 'integrity' or 'artistic', skills like 'cooking skill' or 'video game skills', and interests/preferences like 'coffee lover'. Be creative when coming up with secondary traits, but stay within the context of the story.
   - Stress changes can range from -50 to +50. Consider the choices the player made, their risk level, and how much they diverge from the character's traits. Decisions counter to the player's personality traits should generate more stress, even if the event was resolved successfully. The player's current stress is {life.current_stress}%.
   - Account for the difficulty & intensity settings

3. Tag Selection:
   - Emotional tags should reflect the character's feelings
   - Context tags should capture the situation and setting
   - Story tags should identify the type of experience (e.g., "coming of age", "first love", "personal triumph")

4. Changes to Characters:
   - For any characters involved in the story, provide updated character descriptions that reflect how this interaction affected them
   - Be especially certain to update relationship_description if there has been any change or development in the relationship with the player 
   - It's okay for some characters to have bad reactions to the player. That is more realistic and makes for a more interesting game
   - IMPORTANT: When referring to characters in character_changes, use their exact ID from the Characters list above

Process the story and create a memory that captures both what happened and how it affected {life.name}."""

GENERATE_CAST_TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_initial_cast",
        "description": "Create the initial cast of characters for a new life",
        "parameters": {
            "type": "object",
            "properties": {
                "parents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "FirstName LastName"},
                            "age": {"type": "integer", "minimum": 35, "maximum": 55},
                            "gender": {"type": "string"},
                            "physical_description": {"type": "string"},
                            "personality_description": {"type": "string"},
                            "relationship_description": {
                                "type": "string",
                                "description": "The description of relationship to the player character. Always begin the relationship description with a sentence explaining the base type of relationship, like 'Father', 'Mother', 'Sister', 'Brother', 'Friend from School', 'Boss', 'Teacher', 'Girlfriend', 'Husband', and so on - and then a sentence which describes the state of the relationship."
                            }
                        },
                        "required": ["name", "age", "gender", "physical_description", 
                                   "personality_description", "relationship_description"]
                    },
                    "minItems": 2,
                    "maxItems": 2
                },
                "siblings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "FirstName LastName"},
                            "age": {"type": "integer", "minimum": 13, "maximum": 19},
                            "gender": {"type": "string"},
                            "physical_description": {"type": "string"},
                            "personality_description": {"type": "string"},
                            "relationship_description": {"type": "string"}
                        },
                        "required": ["name", "age", "gender", "physical_description", 
                                   "personality_description", "relationship_description"]
                    }
                },
                "teachers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "FirstName LastName"},
                            "age": {"type": "integer", "minimum": 25, "maximum": 65},
                            "gender": {"type": "string"},
                            "physical_description": {"type": "string"},
                            "personality_description": {"type": "string"},
                            "relationship_description": {"type": "string"}
                        },
                        "required": ["name", "age", "gender", "physical_description", 
                                   "personality_description", "relationship_description"]
                    },
                    "minItems": 3,
                    "maxItems": 3
                },
                "classmates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer", "minimum": 15, "maximum": 17},
                            "gender": {"type": "string"},
                            "physical_description": {"type": "string"},
                            "personality_description": {"type": "string"},
                            "relationship_description": {"type": "string"}
                        },
                        "required": ["name", "age", "gender", "physical_description", 
                                   "personality_description", "relationship_description"]
                    },
                    "minItems": 6,
                    "maxItems": 6
                }
            },
            "required": ["parents", "teachers", "classmates"]
        }
    }
}]

def generate_initial_cast(life: Life) -> List[Character]:
    """Generate the initial cast of characters for a new life"""
    logger.info(f"Generating initial cast for life {life._id}")
    
    try:
        # Get API key from user profile
        user = User.get_by_id(life.user_id)
        if not user or not user.openai_api_key:
            raise ValueError("No OpenAI API key available")

        # Initialize OpenAI client
        client = OpenAI(api_key=user.openai_api_key)
        
        # Determine number of siblings
        num_siblings = random.randint(0, 2)

        character_summary = build_character_summary(life)
        intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    

        
        # Build the prompt
        sibling_text = f" and {num_siblings} sibling{'s' if num_siblings != 1 else ''}" if num_siblings > 0 else ""
        prompt = f"""You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate
story elements that feel natural and personal to the character. Use direct, active, language - preferring a simple and straightforward writing
style rather than flowerly or prosaic text.

Player Character Information:
{character_summary}

Intensity Guidelines: {intensity_guidelines}

Generate the initial cast of characters for {life.name}'s life. {life.name} is a {life.age}-year-old {life.gender} 
who just moved to a new town and is starting their Junior year (grade 11) at Quillington High School in a typical mid-size American city.
Create a cast including parents{sibling_text}, teachers, and classmates that {life.name} will meet on their first day. Consider the Difficulty and Intensity of the story when generating the cast of characters. Consider if familial relationships will be positive, or more complicated. Consider if the teachers will be more supportive/friendly, or more overworked/jaded. Classmates should be diverse in personalities and interests. Make some classmates more open to {life.name} and others less so, weighted by the game difficulty and intensity.

Character Guidelines:
1. Parents should feel like a realistic family unit with {life.name}. Depending on Difficulty & Intensity, this can range from more idealistic & supportive to complicated and tense.
2. Teachers should represent different subjects and teaching styles.

For relationship descriptions:
- Make sure to explicitly mention the base relationship. Example: "So-and-so is {life.name}'s mother." or "So-and-so is {life.name}'s classmate at Quillington High School."
- Parents/Siblings: Describe the pre-existing family dynamic. Note that {life.name} has {num_siblings} siblings.
- Teachers: Mention that this is {life.name}'s teacher, then specify that {life.name} has not yet met them, then describe how they will likely act upon first meeting {life.name}
- Classmates: Mention that this is {life.name}'s classmate, then specify that {life.name} has not yet met them, then describe how they will likely act upon first meeting {life.name}

All characters must have a first and last name. If the player character ({life.name}) doesn't seem to have a last name, invent one for their family members. Do not include titles (Mr/Ms/Dr) in names, not even for teachers."""

        print(prompt)

        # Make API call
        response = client.chat.completions.create(
            model=user.gpt_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate initial cast{' including ' + str(num_siblings) + ' sibling(s)' if num_siblings > 0 else ''}."}
            ],
            tools=GENERATE_CAST_TOOLS,
            tool_choice={"type": "function", "function": {"name": "create_initial_cast"}}
        )

        # Parse response
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)

        print(result)

        # Create characters
        characters = []
        
        # Process parents
        for parent_data in result["parents"]:
            characters.append(Character(
                life_id=life._id,
                name=parent_data["name"],
                age=parent_data["age"],
                gender=parent_data["gender"],
                physical_description=parent_data["physical_description"],
                personality_description=parent_data["personality_description"],
                relationship_description=parent_data["relationship_description"],
                first_met_context="Family",
                first_met_life_stage=LifeStage.CHILDHOOD,
                last_appearance_age=parent_data["age"],
                last_appearance_life_stage=LifeStage.HIGH_SCHOOL
            ))

        # Process siblings if any
        if num_siblings > 0 and "siblings" in result:
            for sibling_data in result["siblings"][:num_siblings]:  # Limit to requested number
                characters.append(Character(
                    life_id=life._id,
                    name=sibling_data["name"],
                    age=sibling_data["age"],
                    gender=sibling_data["gender"],
                    physical_description=sibling_data["physical_description"],
                    personality_description=sibling_data["personality_description"],
                    relationship_description=sibling_data["relationship_description"],
                    first_met_context="Family",
                    first_met_life_stage=LifeStage.CHILDHOOD,
                    last_appearance_age=sibling_data["age"],
                    last_appearance_life_stage=LifeStage.HIGH_SCHOOL
                ))

        # Process teachers
        for teacher_data in result["teachers"]:
            characters.append(Character(
                life_id=life._id,
                name=teacher_data["name"],
                age=teacher_data["age"],
                gender=teacher_data["gender"],
                physical_description=teacher_data["physical_description"],
                personality_description=teacher_data["personality_description"],
                relationship_description=teacher_data["relationship_description"],
                first_met_context="First day of school at Quillington High",
                first_met_life_stage=LifeStage.HIGH_SCHOOL,
                last_appearance_age=teacher_data["age"],
                last_appearance_life_stage=LifeStage.HIGH_SCHOOL
            ))

        # Process classmates
        for classmate_data in result["classmates"]:
            characters.append(Character(
                life_id=life._id,
                name=classmate_data["name"],
                age=classmate_data["age"],
                gender=classmate_data["gender"],
                physical_description=classmate_data["physical_description"],
                personality_description=classmate_data["personality_description"],
                relationship_description=classmate_data["relationship_description"],
                first_met_context="First day of school at Quillington High",
                first_met_life_stage=LifeStage.HIGH_SCHOOL,
                last_appearance_age=classmate_data["age"],
                last_appearance_life_stage=LifeStage.HIGH_SCHOOL
            ))

        # Save all characters
        for character in characters:
            character.save()

        return characters

    except Exception as e:
        logger.error(f"Error generating initial cast: {str(e)}")
        raise
