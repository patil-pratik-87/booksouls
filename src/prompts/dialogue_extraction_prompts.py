"""
Prompt templates for dialogue extraction from books.
Used by DialogueExtractor and other components.
"""

BASIC_DIALOGUE_EXTRACTION = """ 
You are extracting dialogue from a fantasy novel. Find ALL quoted speech and identify speakers.

KEY RULES:
1. Extract ALL dialogue in quotes ("..." or '...').
2. Combine multiple sentences from same speaker. 
3. Only identify individual speakers who speaks to whom.
4. Do not use pronouns like "he","she", "them" etc. as speaker, use the actual name of the character, skip the dialogue if you are not sure about the speaker.
5. Note emotions and actions.
6. RESOLVE METAPHORS: Connect descriptions ("the old woman"), roles ("the CEO"), and relationships ("her brother") to proper names using dialogue context and scene continuity. If "the [descriptor]" appears after "Sarah" speaks, likely same person - group them under the proper name.

Example:
'Hello there!' said Tom to Mary, smiling. 'How are you today?'
Mary replied nervously, 'I'm fine, thank you.'
The young woman then added, 'Please come visit soon.'

Expected JSON (note: "The young woman" = Mary):
{{
  "dialogues": [
    {{
      "speaker": "Tom",
      "dialogue": "Hello there! How are you today?",
      "addressee": "Mary", 
      "emotion": "friendly",
      "actions": ["smiling"],
      "context": "greeting Mary"
    }},
    {{
      "speaker": "Mary",
      "dialogue": "I'm fine, thank you. Please come visit soon.",
      "addressee": "Tom",
      "emotion": "nervous", 
      "actions": [],
      "context": "responding to Tom and inviting him"
    }}
  ],
  "scene_setting": "conversation between Tom and Mary",
  "participants": ["Tom", "Mary"]
}}

Extract from this text:

{text_chunk}

Return only valid JSON:"""

ADVANCED_DIALOGUE_EXTRACTION = """
You are extracting high-quality dialogue from a fantasy novel to capture character essence for AI mimicry.

EXTRACTION RULES:
1. Extract ONLY clear, confident dialogue (confidence >= 0.7)
2. Skip ambiguous speakers or unclear contexts
3. Combine consecutive quotes from same speaker
4. Focus on dialogue that reveals character depth
5. RESOLVE METAPHORS: Connect descriptions ("the old wizard"), roles ("the captain"), and relationships ("his apprentice") to proper names using dialogue context and scene continuity. Group descriptors with their proper names.

CAPTURE THESE TRAITS:
- Tone (wise/cynical/hopeful/stern)
- Character traits (brave/cunning/compassionate)
- Wisdom level (profound insights vs simple observations)
- Relationship dynamics (mentor/student, rivals, friends)
- Speech formality and unique patterns

QUALITY CRITERIA:
- Clear speaker identification
- Meaningful content (not just "yes" or "hmm")
- Reveals personality or relationships
- Contains wisdom, emotion, or character insight

Example JSON:
{{
  "dialogues": [
    {{
      "speaker": "Dumbledore",
      "dialogue": "It is our choices, Harry, that show what we truly are, far more than our abilities.",
      "addressee": "Harry",
      "confidence": 0.95,
      "traits": {{
        "tone": "wise and gentle",
        "personality": ["mentor", "philosophical", "caring"],
        "wisdom_level": "profound",
        "formality": "eloquent"
      }},
      "relationship": {{
        "type": "mentor_student",
        "dynamics": "guiding with compassion"
      }}
    }}
  ],
  "relationships": {{
    "Dumbledore_Harry": {{
      "type": "mentor_student",
      "characteristics": ["protective", "teaching", "respectful"]
    }}
  }},
  "excluded_count": 3,
  "exclusion_reason": "low confidence or trivial content"
}}

Extract from: {text_chunk}

IMPORTANT: Only include dialogues with confidence >= 0.7 and meaningful content.
Return only valid JSON.
"""