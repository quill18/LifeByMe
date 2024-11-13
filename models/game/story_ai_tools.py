# ./models/game/story_ai_tools.py

# Tool definition for story generation
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
                "primary_trait_changes": {
                    "type": "array",
                    "description": "Changes to primary character traits",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer", "minimum": -10, "maximum": 10}
                        },
                        "required": ["name", "value"]
                    }
                },
                "secondary_trait_changes": {
                    "type": "array",
                    "description": "One or two secondary traits that have been created or modified by this memory",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer", "minimum": -10, "maximum": 10}
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
                "impact_explanation", "primary_trait_changes", "stress_change", "character_changes"
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
