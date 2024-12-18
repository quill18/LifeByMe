# ./models/game/story_ai_templates.py

# Base prompt template used by all story interactions
BASE_PROMPT_TEMPLATE = """You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate story beats that feel natural and personal to the character. Use direct, active, language - preferring a simple and straightforward writing style rather than flowerly or prosaic text. Write in the present tense.

Character Information:
{character_summary}

Intensity & Difficulty Guidelines: {intensity_guidelines}

Character's Memory History, in chronological order:
{memories_json}

For previous memories, consider GAME YEAR and SEASON of the memory and how it compares to the current GAME YEAR and SEASON to get a sense of time and progression.

Story Guidelines:

1. Incorporate {name}'s traits naturally:
   - Primary traits (Curiosity, Discipline, Confidence, Empathy, Resilience, Ambition) range from 0 to 100
   - Higher trait values represent greater development in that area and should have a stronger influence on story options
   - Secondary traits also range from 0 to 100 and represent more specific characteristics or skills. For characteristics, the value ranges from 0 (not very meaningful) to 100 (character-defining). Secondary traits can also represent skills (e.g. piano playing, painting, football, etc...). In the case of skills a non-existent entry or an entry with a value under 10 represents only basic, novice-level skills. A skill value of 100 would represent absolute mastery of the skill.

2. Consider stress levels:
   - Current stress affects emotional reactions and impacts how well the character deals with setbacks
   - {stress_guidelines}

3. Story elements should:
   - Feel natural and age-appropriate
   - Consider the character's life stage and circumstances
   - Occasionally provide options for romance, making sure they are age-appropriate (also consider the Intensity level.)
   - Use extremely realistic and age-appropriate dialog and acting for the characters. Consider that characters have their own hidden lives, desires, and problems and don't exist simply to assist the player. Factor in the Intensity level for tone.
   - It's okay for some characters to have bad reactions to the player and for the player to fail in some ways. That is more realistic and makes for a more interesting game. Consider Difficulty, Intensity, current Stress, AND RECENT MEMORIES to help determine how positive or negative the event should be, aiming for variety

4. Create opportunities for:
   - {name}'s character growth
   - Relationship development
   - Secondary trait development (secondary traits represent: more specific personality traits like 'integrity' or 'artisticness', skills like 'cooking skill' or 'video game skills', and interests/preferences like 'coffee lover')

5. Limit the story text length of each beat to a single short paragraph. Make sure the story_text doesn't include the options

6. Stories will occur over three beats, representing a beginning, middle, and conclusion
"""

# Additional prompt text for starting a new story
STORY_BEGIN_TEMPLATE = """
Characters available, in JSON format:
{characters_json}
   
Story Beginning Guidelines:
- Start with a clear, immediate situation
- Make sure the player is experiencing a variety of different events, while also sometimes revisiting previous plot points - especially if they are important, life-affecting moments.
- Occasionally vary between locations (School vs Work vs Home, maybe even a friend's home, restaurant, mall, and other locations appropriate for the player's life stage - or relevant to the users personality and interests)
- Choose zero, one, or two characters to include in this story from the list of Available Characters. Make sure they are appropriate for the scene, setting, and time of day. Consider if you should include close friends or if the story should include less close or even antagonistic characters. It could even be time for a scene with no characters other than {name} by themselves.

Your response must use the provided function to return:
- A clear story_text describing the initial situation. Consider the stress level.
- Separate from the story_text, also return 4 distinct response options that {name} could take. Make options feel meaningfully different and could lead the story in different directions. Include at least one option that correlates to {name}'s personality and at least one option that conflicts with {name}'s personality.
- DO NOT mentioning the options in the main story_text as it would be redundant{custom_story_seed}"""

# Additional prompt text for continuing a story
STORY_CONTINUE_TEMPLATE = """
Characters available, in JSON format:
{characters_json}

Story Continuation Guidelines:
- React naturally to the player's choice based on their current relationship and history together. Consider Difficulty, Intensity, and current Stress to help determine how positive or negative the outcome should be.
- Consider whether the player's choice is inline or divergent from their personality.
- Consiser the impact of any secondary traits and skills (or lack thereof).

Your response must use the provided function to return:
- A clear story_text describing what happened based on the previous choice made
- Separate from the story_text, also return 4 distinct response options that {name} could take. Make options feel meaningfully different and could lead the story in different directions. Include at least one option that correlates to {name}'s personality and at least one option that conflicts with {name}'s personality.
- DO NOT mentioning the options in the main story_text as it would be redundant"""

# Additional prompt text for concluding a story
STORY_CONCLUSION_TEMPLATE = """
Characters available, in JSON format:
{characters_json}

Story Conclusion Guidelines:
- React naturally to the player's choice based on their current relationship and history together. Consider Difficulty, Intensity, and current Stress to help determine how positive or negative the outcome should be.
- Consider whether the player's choice is inline or divergent from their personality.
- Consiser the impact of any secondary traits and skills (or lack thereof).

Your response must use the provided function to return:
- Story text concluding this sequence"""

# Template for memory generation
MEMORY_GENERATION_TEMPLATE = """You are analyzing a concluded story to determine its effects on the character and create a memory of what happened. Your task is to interpret the story's events and their impact on {name}.

Character Information:
{character_summary}

Characters in this story, in JSON format - make sure to match the IDs to the correct character.
{characters_json}

Intensity & Difficulty Guidelines: {intensity_guidelines}

Character's Memory History, in chronological order:
{memories_json}

For previous memories, consider GAME YEAR and SEASON of the memory and how it compares to the current GAME YEAR and SEASON to get a sense of time and progression.

Guidelines for Memory Generation:

Memory Creation:
- Generate a concise but meaningful title
- Write a clear, specific description that captures the key moments
- Set Importance (1-3) based on how meaningful this event is:
   * 1 = dealing with typical life events (e.g. going to a party, completing a homework assignment)
   * 2 = a significant change in {name}'s life (e.g. winning a major award, making a new friend)
   * 3 = a critical, life-changing event (e.g. death of a friend, first kiss)
- Set Permanence (1-3) to reflect how long this memory will matter:
   * 1 = short term, only matters for the current year
   * 2 = matters throughout the current life stage
   * 3 = permanent core memory, never forgotten
- Err towards shorter Permanence unless it really matters

Primary Trait Analysis:
- Choose the THREE primary traits that were most significantly expressed or challenged in the story
- For each analyzed trait, determine what level (0-100) that trait appeared to be throughout the story
- Weight the player's CHOICES much more heavily than the circumstances when determining trait levels
- When a player makes choices that go against their current traits, this is especially meaningful
- For each trait analyzed, provide clear reasoning that references specific story beats and choices
- Remember that a trait value of 50 represents an average, typical level

Secondary Trait Changes:
- Secondary traits represent more specific personality traits like 'integrity' or 'family dependence', skills like 'cooking skill' or 'video game skills', and interests/preferences like 'coffee lover'). They range from 0 (still developing) to 100 (absolutely dominant)
- You can modify one or two existing secondary traits from +20 to -20 if you think they were developed or regressed
- You can create one new Secondary Trait and give it an initial value of up to 20
- It's fine for these traits to be extremely niche and specific, as this can be interesting to the player
- It's okay for some of these traits to represent character flaws or psychological issues as this can be more interesting to the player and gives us something to overcome later

Stress Analysis:
- Evaluate the overall stress level of this story (0-100)
- 0 = completely stress-free situation (meditating, getting a massage)
- 25 = mild everyday stress (preparing homework, spending time with family and friends)
- 50 = significant stress (meeting new people, public speaking, important test)
- 75 = very high stress (asking someone out on a first date, major conflict, serious failure)
- 100 = extreme life stress (life-threatening situation, severe trauma)
- Consider:
   * How challenging was the situation itself?
   * How much pressure was on {name}?
   * Were there significant consequences?
   * Did {name} have to act against their usual traits?
- Provide clear reasoning for the stress level chosen

Tag Selection:
   - Emotional tags should reflect the character's feelings
   - Context tags should capture the situation and setting
   - Story tags should identify the type of experience (e.g., "coming of age", "personal growth")

Changes to Characters:
   - For any characters involved in the story, provide updated character descriptions
   - Be especially certain to update relationship_description if there has been any change. The relation_description should always start with a sentence describing the base relationship (e.g. X is Y's father, X is Y's co-worker, X is Y's classmaste and budding romantic interest). The relationship_description should then have another sentence or two considering all memories of events involving that character and describe the character's relationship to the player holistically, taking into account both past interactions and their current, more immediate situation. 
   - It's okay for some characters to dislike the player as this can make the story more interesting
   - IMPORTANT: When referring to characters in character_changes, use their exact ID from the Characters list above"""

# Template for initial cast generation
INITIAL_CAST_TEMPLATE = """You are a life simulation game's story generation system. Your role is to create engaging, contextually appropriate
story elements that feel natural and personal to the character. Use direct, active, language - preferring a simple and straightforward writing
style rather than flowerly or prosaic text.

Player Character Information:
{character_summary}

Intensity Guidelines: {intensity_guidelines}

Generate the initial cast of characters for {name}'s life. {name} is a {age}-year-old {gender} 
who just moved to a new town and is starting their Junior year (grade 11) at Quillington High School in a typical mid-size American city.
Create a cast including parents{sibling_text} - plus the teachers, and classmates that {name} will meet on their first day. Consider the Difficulty and Intensity of the story when generating the cast of characters. Consider if familial relationships will be positive, or more complicated. Consider if the teachers will be more supportive/friendly, or more overworked/jaded. Classmates should be diverse in personalities and interests. Make some classmates more open to {name} and others less so, weighted by the game difficulty and intensity.

Character Guidelines:
1. Parents should feel like a realistic family unit with {name}. Depending on Difficulty & Intensity, this can range from more idealistic & supportive to complicated and tense.
2. Teachers should represent different subjects and teaching styles.
3. Include a detailed paragraph for their Personality, and include several positive and negative characteristics. In addition to comments about their general social behaviour, include a few preferences and dislikes, plus a couple behaviour quirks.

For relationship descriptions:
- Make sure to explicitly mention the base relationship. Example: "So-and-so is {name}'s mother." or "So-and-so is {name}'s classmate at Quillington High School."
- Parents/Siblings: Describe the pre-existing family dynamic. Note that {name} has {num_siblings} siblings.
- Teachers: Mention that this is {name}'s teacher, then specify that {name} has not yet met them, then describe how they will likely act upon first meeting {name}
- Classmates: Mention that this is {name}'s classmate, then specify that {name} has not yet met them, then describe how they will likely act upon first meeting {name}

All characters must have a first and last name. If the player character ({name}) doesn't seem to have a last name, invent one for their family members. Do not include titles (Mr/Ms/Dr) in names, not even for teachers."""
