# ./models/game/story_ai_prompts.py

import logging
import models.game.story_ai_templates as templates
import models.game.life as life_module
import models.game.memory as memory_module
import models.game.character as character_module
import models.game.story as story_module
from models.game.enums import Intensity, Difficulty

logger = logging.getLogger(__name__)

def build_character_summary(life: 'life_module.Life') -> str:
    """Create a concise character summary for the AI"""
    gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
    
    traits_desc = []
    for trait in life.primary_traits:
        traits_desc.append(f"{trait.name}: {trait.value}/100")
    
    summary = [
        f"{life.name} is {life.age}-year-old",
        f"Gender: {gender_desc}",
        f"Life Stage: {life.life_stage.value}",
        f"Primary Traits: {', '.join(traits_desc)}" if traits_desc else None,
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

def build_base_prompt(life: 'life_module.Life') -> str:
    """Build the base system prompt for all story interactions"""
    character_summary = build_character_summary(life)
    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    memories_json = memory_module.Memory.format_memories_for_ai(life._id)
    
    return templates.BASE_PROMPT_TEMPLATE.format(
        character_summary=character_summary,
        intensity_guidelines=intensity_guidelines,
        memories_json=memories_json,
        name=life.name
    )

def build_story_begin_prompt(life: 'life_module.Life', custom_story_seed: str) -> str:
    """Build the complete prompt for starting a new story"""
    base_prompt = build_base_prompt(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    
    if custom_story_seed:
        custom_story_seed = f"\n\nSTORY SCENARIO: {custom_story_seed}"

    return base_prompt + templates.STORY_BEGIN_TEMPLATE.format(
        characters_json=characters_json,
        name=life.name,
        custom_story_seed=custom_story_seed
    )

def build_story_continue_prompt(life: 'life_module.Life', story: 'story_module.Story') -> str:
    """Build the prompt for continuing a story"""
    base_prompt = build_base_prompt(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    
    return base_prompt + templates.STORY_CONTINUE_TEMPLATE.format(
        characters_json=characters_json,
        name=life.name
    )

def build_story_conclusion_prompt(life: 'life_module.Life', story: 'story_module.Story') -> str:
    """Build the prompt for concluding a story"""
    base_prompt = build_base_prompt(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    
    return base_prompt + templates.STORY_CONCLUSION_TEMPLATE.format(
        characters_json=characters_json
    )

def build_memory_generation_prompt(life: 'life_module.Life', story: 'story_module.Story') -> str:
    """Build the prompt for memory generation from a story"""
    character_summary = build_character_summary(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    memories_json = memory_module.Memory.format_memories_for_ai(life._id)
    
    return templates.MEMORY_GENERATION_TEMPLATE.format(
        name=life.name,
        character_summary=character_summary,
        characters_json=characters_json,
        intensity_guidelines=intensity_guidelines,
        memories_json=memories_json,
        current_stress=life.current_stress
    )

def build_initial_cast_prompt(life: 'life_module.Life', num_siblings: int) -> str:
    """Build the prompt for generating initial cast of characters"""
    character_summary = build_character_summary(life)
    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    sibling_text = f" and {num_siblings} sibling{'s' if num_siblings != 1 else ''}" if num_siblings > 0 else ""
    
    return templates.INITIAL_CAST_TEMPLATE.format(
        character_summary=character_summary,
        intensity_guidelines=intensity_guidelines,
        name=life.name,
        age=life.age,
        gender=life.gender,
        sibling_text=sibling_text,
        num_siblings=num_siblings
    )