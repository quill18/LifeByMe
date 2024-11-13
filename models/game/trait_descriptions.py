# ./models/game/trait_descriptions.py

TRAIT_DEFINITIONS = {
    "Curiosity": {
        "description": "Represents intellectual curiosity, creativity, and willingness to try new things. Higher levels mean more innovative thinking and adaptability. Influences learning speed and discovery of new opportunities.",
        "levels": {
            (0, 10): "Shows little interest in new experiences, strongly preferring familiar routines.",
            (11, 20): "Occasionally asks basic questions about immediate surroundings.",
            (21, 30): "Beginning to show interest in learning about specific topics of personal relevance.",
            (31, 40): "Willing to try new things when encouraged by others.",
            (41, 50): "Actively seeks out information about topics of interest.",
            (51, 60): "Regularly explores new ideas and experiences with enthusiasm.",
            (61, 70): "Deeply investigates topics of interest, often making novel connections.",
            (71, 80): "Constantly seeks new knowledge and experiences across many domains.",
            (81, 90): "Insatiable appetite for learning sometimes leads to scattered focus.",
            (91, 100): "Obsessively pursues knowledge, often at the expense of practical matters."
        }
    },
    "Discipline": {
        "description": "Represents self-control, organization, and dedication. Higher levels mean better planning and follow-through. Influences success in long-term goals and studies.",
        "levels": {
            (0, 10): "Acts purely on impulse with no regard for consequences.",
            (11, 20): "Occasionally follows through on commitments when motivated.",
            (21, 30): "Can maintain basic routines with external support.",
            (31, 40): "Beginning to develop consistent habits and basic organization.",
            (41, 50): "Reliably handles responsibilities, though may procrastinate.",
            (51, 60): "Maintains good organization and follows through on commitments.",
            (61, 70): "Highly structured approach to tasks with careful planning.",
            (71, 80): "Maintains exemplary order and consistently achieves goals.",
            (81, 90): "Rigid adherence to systems may create stress when plans change.",
            (91, 100): "Perfectionist tendencies dominate life, struggling with flexibility."
        }
    },
    "Confidence": {
        "description": "Represents self-assurance and social comfort. Higher levels mean better public speaking and leadership. Influences social interactions and career advancement.",
        "levels": {
            (0, 10): "Avoids all social interaction and deeply doubts own abilities.",
            (11, 20): "Extremely hesitant in social situations but can manage basic interactions.",
            (21, 30): "Gradually becoming more comfortable in familiar social settings.",
            (31, 40): "Can express opinions among friends but still uncertain in groups.",
            (41, 50): "Generally comfortable socially but may hesitate in new situations.",
            (51, 60): "Expresses self clearly and handles most social situations well.",
            (61, 70): "Projects strong self-assurance and easily takes initiative.",
            (71, 80): "Natural leader who readily takes charge of situations.",
            (81, 90): "Strong personality may inadvertently overshadow quieter voices.",
            (91, 100): "Dominates social situations, sometimes blindly dismissing others' views."
        }
    },
    "Empathy": {
        "description": "Represents emotional intelligence and understanding of others. Higher levels mean stronger relationships and conflict resolution. Influences friendship development and team dynamics.",
        "levels": {
            (0, 10): "Shows no recognition of others' emotional states.",
            (11, 20): "Recognizes obvious emotional displays but rarely responds.",
            (21, 30): "Beginning to understand and relate to others' basic feelings.",
            (31, 40): "Shows genuine concern for close friends' emotional states.",
            (41, 50): "Readily recognizes and responds to others' emotional needs.",
            (51, 60): "Naturally attunes to others' feelings and offers support.",
            (61, 70): "Deeply understands complex emotional situations and nuances.",
            (71, 80): "Provides remarkable emotional support and guidance to others.",
            (81, 90): "So attuned to others' emotions that it can be overwhelming.",
            (91, 100): "Completely absorbs others' emotional pain, often at personal cost."
        }
    },
    "Resilience": {
        "description": "Represents emotional stability and stress management. Higher levels mean better handling of setbacks. Influences stress recovery and mental health.",
        "levels": {
            (0, 10): "Completely overwhelmed by even minor setbacks.",
            (11, 20): "Struggles to cope with everyday challenges.",
            (21, 30): "Beginning to develop basic coping mechanisms.",
            (31, 40): "Can handle routine stress but easily rattled by bigger issues.",
            (41, 50): "Recovers from most setbacks with reasonable time.",
            (51, 60): "Maintains stability through most difficulties.",
            (61, 70): "Effectively manages stress and bounces back from hardship.",
            (71, 80): "Thrives under pressure and quickly overcomes obstacles.",
            (81, 90): "So comfortable with hardship they may take unnecessary risks.",
            (91, 100): "Almost disconnected from stress, may ignore genuine warning signs."
        }
    },
    "Ambition": {
        "description": "Represents drive, goal-setting, and determination. Higher levels mean more persistence and achievement orientation. Influences career progression and personal growth.",
        "levels": {
            (0, 10): "Shows no interest in personal growth or achievement.",
            (11, 20): "Occasionally expresses desires but rarely acts on them.",
            (21, 30): "Beginning to set basic personal goals.",
            (31, 40): "Pursues modest goals when path is clear.",
            (41, 50): "Actively works toward personal and professional development.",
            (51, 60): "Sets challenging goals and persistently works to achieve them.",
            (61, 70): "Driven to excel and consistently pushes personal boundaries.",
            (71, 80): "Achieves difficult goals through determined effort.",
            (81, 90): "Relentless pursuit of goals may strain relationships.",
            (91, 100): "Obsessively pursues success at the cost of personal well-being."
        }
    }
}

def get_trait_description(trait_name: str, value: int) -> str:
    """
    Get the description for a trait at a specific value level.
    
    Args:
        trait_name: The name of the trait (e.g., "Curiosity")
        value: The numeric value of the trait (0-100)
    
    Returns:
        A string describing how the trait manifests at that level
    
    Raises:
        KeyError: If trait_name is not recognized
        ValueError: If value is not between 0 and 100
    """
    if trait_name not in TRAIT_DEFINITIONS:
        raise KeyError(f"Unknown trait: {trait_name}")
        
    if not 0 <= value <= 100:
        raise ValueError(f"Trait value must be between 0 and 100, got {value}")
        
    # Find the correct level range
    for (min_val, max_val), description in TRAIT_DEFINITIONS[trait_name]["levels"].items():
        if min_val <= value <= max_val:
            return description
            
    return "Invalid trait level"  # Should never reach this due to value check above

def get_trait_base_description(trait_name: str) -> str:
    """
    Get the base description of what a trait represents.
    
    Args:
        trait_name: The name of the trait (e.g., "Curiosity")
    
    Returns:
        A string describing what the trait represents in general
    
    Raises:
        KeyError: If trait_name is not recognized
    """
    if trait_name not in TRAIT_DEFINITIONS:
        raise KeyError(f"Unknown trait: {trait_name}")
        
    return TRAIT_DEFINITIONS[trait_name]["description"]