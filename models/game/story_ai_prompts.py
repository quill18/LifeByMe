# ./models/game/story_ai_prompts.py

import logging
import models.game.story_ai_templates as templates
import models.game.life as life_module
import models.game.memory as memory_module
import models.game.character as character_module
import models.game.story as story_module
from models.game.enums import Intensity, Difficulty
import random

logger = logging.getLogger(__name__)

def build_character_summary(life: 'life_module.Life') -> str:
    """Create a concise character summary for the AI"""
    gender_desc = life.custom_gender if life.gender == "Custom" else life.gender
    
    # Format traits with more detail and explicit values
    traits_desc = []
    for trait in life.primary_traits:
        interpretation = "very low" if trait.value < 20 else \
                        "low" if trait.value < 40 else \
                        "average" if trait.value < 60 else \
                        "high" if trait.value < 80 else "very high"
        traits_desc.append(f"{trait.name}: {trait.value}/100 ({interpretation})")
    
    # Build the summary parts
    summary_parts = [
        f"{life.name} is {life.age}-year-old",
        f"Gender: {gender_desc}",
        f"Life Stage: {life.life_stage.value}",
        f"Current Season and Year: {life.current_season.value} {life.current_year}",
        "Primary Traits:"
    ]
    
    # Add traits if they exist
    if traits_desc:
        summary_parts.extend(f"- {trait}" for trait in traits_desc)
    
    # Add stress level
    summary_parts.append(f"Current stress level: {life.current_stress}%")

    # Add custom directions if they exist
    if life.custom_directions:
        summary_parts.append(f"Special character notes: {life.custom_directions}")
        
    return "\n".join(summary_parts)

def build_intensity_guidelines(intensity: Intensity, difficulty: Difficulty) -> str:
    """Get detailed intensity guidelines based on user selection"""
    intensity_text = ""

    if intensity == Intensity.LIGHT:
        intensity_text = """This story should maintain a LIGHT intensity level. Keep the tone optimistic and uplifting. Focus on positive personal growth and achievements. Handle conflicts through communication and understanding. Avoid topics that could be triggering or distressing. Use humor and warmth appropriately. Keep any romance at a sweet, innocent level."""
    
    elif intensity == Intensity.MODERATE:
        intensity_text = """This story should maintain a MODERATE intensity level. Provide meaningful, realistic challenges. Allow for both success and setbacks. Include realistic interpersonal conflicts. Touch on serious topics. Show consequences for actions while maintaining hope. Handle romance at a realistic but tasteful level. Allow for anxiety and stress. Keep darker elements brief and resolution-focused."""
    
    else:  # GRITTY
        intensity_text = """This story should maintain a GRITTY intensity level. Present realistic challenges without guaranteed resolution. Allow for meaningful failures and their consequences. Explore complex emotional and interpersonal situations. Address serious real-world issues directly. Handle romance, relationships, and sexuality realistically. Include genuine struggles with identity and values. Don't shy away from internal conflicts and doubts. Remember that growth can come from difficulty."""

    if difficulty == Difficulty.STORY:
        intensity_text += """\n\nDifficulty is set to STORY mode. The character should generally succeed at their chosen actions, though the manner and consequences of success may vary. Failures should be rare and primarily serve character development rather than creating serious setbacks. Provide clear paths to achieve desired outcomes. If stress is below 30, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome"""

    elif difficulty == Difficulty.BALANCED:
        intensity_text += """\n\nDifficulty is set to BALANCED mode. Success should depend on how well the chosen action aligns with the character's traits and previous development. Actions that go against type should be notably harder to succeed at. Include a mix of successes and setbacks, with neither dominating the narrative. If stress is below 50, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome"""

    else:  # CHALLENGING
        intensity_text += """\n\nDifficulty is set to CHALLENGING mode. Success should be earned and never guaranteed. Actions that go against the character's established traits can still succeed, but at the cost of personal stress. Create meaningful obstacles that require careful choice selection. Let failures have lasting impact, though allow for eventual recovery and growth. If stress is below 70, try to generate a story that will generate stress, but judge actual stress generation based on the character's choices, traits, and story outcome."""

    return intensity_text

def build_stress_guidelines(life: 'life_module.Life') -> str:
    if(life.current_stress > 80):
        return f"   - {life.name} is currently extremely stressed ({life.curren_stress}/100), which makes challenges extremely dramatic. Consider offering options that represent a 'mental breakdown' inline with a character's traits that might provide a large stress relief even at the cost of a negative outcome to the story. (e.g. a high school student deciding to blow off studying for an exam to play video games instead)"
    elif(life.current_stress > 60):
        return f"   - {life.name} is currently moderately stressed ({life.curren_stress}/100), which makes challenges more dramatic. Consider offering one or two options that give the player a change to 'blow off steam' and relax, possibly at a cost of ignoring responsibilities."
    elif(life.current_stress < 30):
        return f"   - {life.name} is currently barely stressed ({life.curren_stress}/100). Consider offering an to the player that will be more bold and daring, representing a reduced anxiety. An option that represents more diligence and attention to detail could also be appropriate."
    
    return "   - {life.name} is currently experiencing average stress ({life.curren_stress}/100) levels."
    



def build_base_prompt(life: 'life_module.Life') -> str:
    """Build the base system prompt for all story interactions"""
    character_summary = build_character_summary(life)
    intensity_guidelines = build_intensity_guidelines(life.intensity, life.difficulty)
    memories_json = memory_module.Memory.format_memories_for_ai(life._id)
    stress_guidelines = build_stress_guidelines(life)
    
    return templates.BASE_PROMPT_TEMPLATE.format(
        character_summary=character_summary,
        intensity_guidelines=intensity_guidelines,
        memories_json=memories_json,
        stress_guidelines=stress_guidelines,
        name=life.name,
        season_and_year=f"{life.current_season} {life.current_year}"
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

def build_story_success_hint(life: 'life_module.Life') -> str:
    """Randomly determine if this story beat should be a failure based on difficulty setting"""
    
    failure_chance = 0.2 if life.difficulty == Difficulty.CHALLENGING else \
                    0.1 if life.difficulty == Difficulty.BALANCED else 0.05
    
    if random.random() < failure_chance:
        return "\n\nIMPORTANT: This story beat should represent a NEGATIVE OUTCOME for the character. Consider past memories for context and make sure that all characters still behave appropriately. This negative outcome could represent a failure by the player character, but it could also be a rejection or antipathy by another character, representing an obstacle in their relationship."
    
    return ""

def build_story_continue_prompt(life: 'life_module.Life', story: 'story_module.Story') -> str:
    """Build the prompt for continuing a story"""
    base_prompt = build_base_prompt(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    success_hint = build_story_success_hint(life)
    
    return base_prompt + templates.STORY_CONTINUE_TEMPLATE.format(
        characters_json=characters_json,
        name=life.name
    ) + success_hint

def build_story_conclusion_prompt(life: 'life_module.Life', story: 'story_module.Story') -> str:
    """Build the prompt for concluding a story"""
    base_prompt = build_base_prompt(life)
    characters_json = character_module.Character.format_characters_for_ai(life_id=life._id)
    success_hint = build_story_success_hint(life)
    
    return base_prompt + templates.STORY_CONCLUSION_TEMPLATE.format(
        characters_json=characters_json
    ) + success_hint

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