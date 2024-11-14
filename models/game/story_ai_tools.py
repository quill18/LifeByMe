# ./models/game/story_ai_tools.py

# Base story tools without options
STORY_TOOLS = [{
    "type": "function",
    "function": {
        "name": "create_story_beat",
        "description": "Create a story beat with text",
        "parameters": {
            "type": "object",
            "properties": {
                "story_text": {
                    "type": "string",
                    "description": "The narrative text describing what happens in this story beat"
                },
                "character_ids": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of character IDs for characters who appear in this story, chosen from the list of Available Characters"
                }
            },
            "required": ["story_text", "character_ids"]
        }
    }
}]

# Extended version with options
STORY_TOOLS_WITH_OPTIONS = [{
    "type": "function",
    "function": {
        **STORY_TOOLS[0]["function"],  # Copy base function properties
        "parameters": {
            "type": "object",
            "properties": {
                **STORY_TOOLS[0]["function"]["parameters"]["properties"],  # Copy base properties
                "options": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of exactly 4 response options for how the story continues",
                    "minItems": 4,
                    "maxItems": 4
                }
            },
            "required": ["story_text", "options", "character_ids"]
        }
    }
}]

# Tool definition for memory generation
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
                    "description": "How important this memory is (1-3). This also determines how many primary traits should be analyzed"
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
                "trait_analysis": {
                    "type": "object",
                    "description": "Analysis of 1-3 primary traits (equal to importance) that were most relevant to this story",
                    "properties": {
                        "analyzed_traits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "enum": ["Curiosity", "Discipline", "Confidence", "Empathy", "Resilience", "Ambition"]
                                    },
                                    "calculated_value": {
                                        "type": "integer",
                                        "minimum": 0,
                                        "maximum": 100,
                                        "description": "What value (0-100) this trait appeared to be throughout the story, heavily weighted towards player choices"
                                    },
                                    "reasoning": {
                                        "type": "string",
                                        "description": "Brief explanation of why this trait was chosen and how the value was determined"
                                    }
                                },
                                "required": ["name", "calculated_value", "reasoning"]
                            },
                            "minItems": 1,
                            "maxItems": 3
                        }
                    },
                    "required": ["analyzed_traits"]
                },
                "story_stress": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "How stressful this story was (0-100). 0 is completely stress-free, 100 is one of the most stressful situations a person could experience"
                },
                "stress_reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why the story_stress value was chosen"
                },
                "impact_explanation": {
                    "type": "string",
                    "description": "Brief explanation of why the memory is important and permanent (or not)"
                },
                "secondary_trait_changes": {
                    "type": "object",
                    "properties": {
                        "modifications": {
                            "type": "array",
                            "description": "Changes to existing secondary traits (up to 2)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {"type": "integer", "minimum": -20, "maximum": 20}
                                },
                                "required": ["name", "value"]
                            },
                            "maxItems": 2
                        },
                        "additions": {
                            "type": "array",
                            "description": "New secondary traits to create (up to 1)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {"type": "integer", "minimum": 0, "maximum": 20}
                                },
                                "required": ["name", "value"]
                            },
                            "maxItems": 1
                        }
                    },
                    "required": []
                },
                "character_changes": {
                    "type": "array",
                    "description": "Characters present in the story that should have their details updated",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "The database ID of the character being updated"
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
                                "description": "Updated description of relationship to the player character"
                            },
                            "relationship_status": {
                                "type": "string",
                                "enum": ["Active", "Departed", "Deceased"],
                                "description": "Updated status of this character"
                            }
                        },
                        "required": ["id", "relationship_description"]
                    }
                }
            },
            "required": [
                "title", "description", "importance", "permanence", 
                "emotional_tags", "context_tags", "story_tags",
                "impact_explanation", "trait_analysis", "story_stress", 
                "stress_reasoning", "character_changes"
            ]
        }
    }
}]

# Tool definition for initial cast generation
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
