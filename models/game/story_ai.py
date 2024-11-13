# ./models/game/story_ai.py

import logging
import random
from typing import Dict, List
from bson import ObjectId

import models.game.story_ai_utils as ai_utils
import models.game.story_ai_prompts as prompts
import models.game.story_ai_tools as tools
import models.game.character as character_module
import models.game.story as story_module
import models.game.life as life_module
from models.game.enums import LifeStage

logger = logging.getLogger(__name__)

@ai_utils.handle_openai_error
def begin_story(life: 'life_module.Life', custom_story_seed: str) -> ai_utils.StoryResponse:
    """Generate the first beat of a new story"""
    logger.info(f"Starting new story for life {life._id}")
    
    # Create OpenAI client
    client, model = ai_utils.create_openai_client(life)
    
    # Build prompt
    prompt = prompts.build_story_begin_prompt(life, custom_story_seed)
    
    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Begin a new story for this character."}
        ],
        tools=tools.STORY_TOOLS,
        tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
    )
    
    # Parse response
    result = ai_utils.parse_openai_response(response, "create_story_beat")
    
    # Create and return StoryResponse
    return ai_utils.StoryResponse(
        prompt=prompt,
        story_text=result["story_text"],
        options=result["options"],
        character_ids=[ObjectId(char_id) for char_id in result["character_ids"]]
    )

@ai_utils.handle_openai_error
def continue_story(life: 'life_module.Life', story: 'story_module.Story', selected_option: str) -> ai_utils.StoryResponse:
    """Generate the next beat of an ongoing story"""
    logger.info(f"Continuing story for life {life._id}")
    
    # Create OpenAI client
    client, model = ai_utils.create_openai_client(life)
    
    # Build the story context
    story_context = "\n\n".join([
        "Previous story beats:",
        *[f"Beat: {beat}\nResponse: {response if response else 'Current beat'}" 
          for beat, response in story.beats]
    ])
    
    # Build prompt
    prompt = prompts.build_story_continue_prompt(life, story)
    
    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"""
Story context:
{story_context}

Player chose: {selected_option}

Continue the story based on this choice."""}
        ],
        tools=tools.STORY_TOOLS,
        tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
    )
    
    # Parse response
    result = ai_utils.parse_openai_response(response, "create_story_beat")
    
    # Create and return StoryResponse
    return ai_utils.StoryResponse(
        prompt=None,
        story_text=result["story_text"],
        options=result["options"],
        character_ids=None
    )

@ai_utils.handle_openai_error
def conclude_story(life: 'life_module.Life', story: 'story_module.Story', selected_option: str) -> ai_utils.StoryResponse:
    """Generate the concluding beat of a story"""
    logger.info(f"Concluding story for life {life._id}")
    
    # Create OpenAI client
    client, model = ai_utils.create_openai_client(life)
    
    # Build the story context
    story_context = "\n\n".join([
        "Previous story beats:",
        *[f"Beat: {beat}\nResponse: {response if response else 'Current beat'}" 
          for beat, response in story.beats]
    ])
    
    # Build prompt
    prompt = prompts.build_story_conclusion_prompt(life, story)
    
    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"""
Story context:
{story_context}

Player chose: {selected_option}

Conclude the story based on this choice."""}
        ],
        tools=tools.STORY_TOOLS,
        tool_choice={"type": "function", "function": {"name": "create_story_beat"}}
    )
    
    # Parse response
    result = ai_utils.parse_openai_response(response, "create_story_beat")
    
    # Create and return StoryResponse
    return ai_utils.StoryResponse(
        prompt=None,
        story_text=result["story_text"],
        options=None,
        character_ids=None
    )

@ai_utils.handle_openai_error
def generate_memory_from_story(life: 'life_module.Life', story: 'story_module.Story') -> Dict:
    """Generate memory parameters from a concluded story"""
    logger.info(f"Generating memory for story {story._id}")
    
    # Create OpenAI client
    client, model = ai_utils.create_openai_client(life)
    
    # Build story context
    story_context = "\n\n".join([
        "Story progression:",
        *[f"Beat: {beat}\nResponse: {response if response else 'Final beat'}" 
          for beat, response in story.beats]
    ])
    
    # Build prompt
    prompt = prompts.build_memory_generation_prompt(life, story)
    
    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"""
Story context:
{story_context}

Generate a memory based on this story."""}
        ],
        tools=tools.MEMORY_TOOLS,
        tool_choice={"type": "function", "function": {"name": "create_memory"}}
    )
    
    # Parse response
    result = ai_utils.parse_openai_response(response, "create_memory")
    
    # Store memory parameters in story
    story.store_memory_params(
        title=result["title"],
        description=result["description"],
        params=result
    )
    
    return result

@ai_utils.handle_openai_error
def generate_initial_cast(life: 'life_module.Life') -> List['character_module.Character']:
    """Generate the initial cast of characters for a new life"""
    logger.info(f"Generating initial cast for life {life._id}")
    
    # Create OpenAI client
    client, model = ai_utils.create_openai_client(life)
    
    # Determine number of siblings
    num_siblings = random.randint(0, 2)
    
    # Build the prompt
    prompt = prompts.build_initial_cast_prompt(life, num_siblings)
    
    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Generate initial cast{' including ' + str(num_siblings) + ' sibling(s)' if num_siblings > 0 else ''}."}
        ],
        tools=tools.GENERATE_CAST_TOOLS,
        tool_choice={"type": "function", "function": {"name": "create_initial_cast"}}
    )
    
    # Parse response
    result = ai_utils.parse_openai_response(response, "create_initial_cast")
    
    # Create characters
    characters = []
    
    # Process parents
    for parent_data in result["parents"]:
        characters.append(character_module.Character(
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
        for sibling_data in result["siblings"][:num_siblings]:
            characters.append(character_module.Character(
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
        characters.append(character_module.Character(
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
        characters.append(character_module.Character(
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