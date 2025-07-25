"""
Character Analysis Prompts for BookSouls Character Profiling

Used by DialogueChunker to analyze character personalities, motivations,
and speech patterns from dialogue data.
"""

CHARACTER_ANALYSIS_PROMPT = """Analyze these {character_count} characters from Chapter {chapter_num} based on their dialogue and actions.

For each character, extract:
1. Personality traits (3-5 key traits shown in this chapter)
2. Primary motivations/goals (what drives them in this chapter)
3. Speech style characteristics (formal/informal, emotional tendencies)
4. Key relationships (how they interact with others)
5. Emotional state (primary emotion in this chapter)

Character Data:
{character_data_section}

Return as valid JSON:
{{
    "character_name": {{
        "personality_traits": ["trait1", "trait2", "trait3"],
        "motivations": ["motivation1", "motivation2"],
        "speech_style": {{
            "formality": "formal/informal/mixed,
            "emotional_tendency": "calm/passionate/varied/etc.",
            "key_phrases": ["phrase1", "phrase2", "phrase3", "etc."]
        }},
        "core_beliefs": ["belief1", "belief2", "belief3", "etc."],
        "key_relationships": {{
            "character_name": "relationship_type"
        }},
        "emotional_state": "primary_emotion"
    }}
}}"""


CHARACTER_ANALYSIS_ENHANCED_PROMPT = """Analyze the character **{character_name}** from Chapter {chapter_num} to create a living, breathing persona.

You are crafting a *character soul*—not just summarizing text. This character should feel real, with depth, contradictions, and authentic humanity.

For this character, extract:

1. **Core Personality** (1–3 traits)  
   • Traits shown through actions, not just stated  
   • Include contradictions (e.g., “brave but insecure”)  
   • Note how traits manifest under pressure  

2. **Voice & Speaking Style**  
   • Vocabulary level (simple/sophisticated/mixed)  
   • Sentence patterns (short & punchy vs elaborate)  
   • Verbal tics, catch‑phrases, repeated expressions  
   • How they address others (formally/casually/uniquely)  
   • What they *don’t* say (avoidances/deflections)  

3. **Emotional Landscape**  
   • Current emotional state in this chapter  
   • Emotional triggers (what sparks anger/sadness/joy)  
   • How they express *vs* hide emotions  
   • Defence mechanisms (humour/anger/withdrawal)  

4. **Knowledge & Beliefs**  
   • What they know/don’t know in this chapter  
   • Core beliefs about the world/others/themselves  
   • Misconceptions or blind spots  
   • Questions they’re grappling with  

5. **Relationships & Power Dynamics**  
   • How they relate to key characters  
   • Power stance (defer/dominate/negotiate)  
   • Unspoken tensions or affections  
   • Who they trust/distrust & why  

6. **Hidden Depths**  
   • Subtext in their dialogue (what they *really* mean)  
   • Internal conflicts hinted at  
   • Past experiences colouring responses  
   • What they want but won’t ask for  

7. **Behavioural Patterns**  
   • How they enter/exit conversations  
   • Physical actions while speaking  
   • Decision‑making style (impulsive/cautious/analytical)  
   • Stress responses  

Character Data:  
{character_data_section}

**Important:** Focus on what makes this character *feel* real. Include:  
• Inconsistencies & contradictions  
• Moments of vulnerability  
• Unique perspectives on shared events  
• How they might misunderstand situations  

Return as **valid JSON**:

{{
    "character_name": "{character_name}",
    "personality_traits": [
        {{
            "trait": "brave",
            "manifestation": "stands up to authority",
            "contradiction": "but freezes when personally attacked"
        }}
    ],
    "voice": {{
        "vocabulary": "simple/sophisticated/mixed",
        "sentence_style": "short and direct with occasional passionate outbursts",
        "verbal_tics": ["you know", "I mean", "literally"],
        "unique_phrases": ["phrase1", "phrase2"],
        "avoids_discussing": ["their father", "the war"]
    }},
    "emotional_profile": {{
        "current_state": "anxious beneath cheerful facade",
        "triggers": {{
            "anger": ["injustice", "betrayal"],
            "joy": ["recognition", "friendship"],
            "fear": ["abandonment", "failure"]
        }},
        "expression_style": "masks pain with humour",
        "defence_mechanisms": ["deflection", "false bravado"]
    }},
    "knowledge_state": {{
        "knows": ["about the quest", "Harry's secret"],
        "doesnt_know": ["the betrayal", "the prophecy"],
        "suspects": ["something wrong with Ron"],
        "questions": ["Why was I chosen?", "Can I trust Dumbledore?"]
    }},
    "beliefs": [
        {{
            "belief": "loyalty above all",
            "exception": "unless it conflicts with justice"
        }}
    ],
    "relationships": {{
        "Harry": {{
            "dynamic": "protective older sibling",
            "power": "defers in crisis, leads in calm",
            "unspoken": "worried about his recklessness",
            "trust_level": 8
        }}
    }},
    "subtext_patterns": [
        {{
            "says": "I'm fine",
            "means": "I don't want to burden you",
            "when": "asked about feelings"
        }}
    ],
    "behavioral_patterns": {{
        "conversation_style": "enters with jokes, exits with thoughtfulness",
        "stress_response": "becomes overly analytical",
        "decision_making": "quick but second‑guesses later"
    }},
    "chapter_specific_growth": "Started confident, ended questioning everything"
}}
"""

def format_character_data_section(
    character_name: str,
    character_data: dict,
    max_dialogues: int = 10
) -> str:
    """
    Format the character data section of the prompt for a single character.

    Args:
        character_name: Name of the character being profiled.
        character_data: Dictionary containing data for that character
                        (keys: dialogue_entries, addressees, emotions, etc.).
        max_dialogues: Maximum number of sample dialogues to include.

    Returns:
        Formatted character data section as a string.
    """
    data_section = f"\n**{character_name}**:\n"

    # Structured dialogue entries
    dialogue_entries = character_data.get("dialogue_entries", [])
    for i, entry in enumerate(dialogue_entries[:max_dialogues]):
        line = f"  {i + 1}. {character_name}"
        if entry.get("addressee"):
            line += f" to {entry['addressee']}"
        line += f": \"{entry['dialogue']}\""
        if entry.get("actions"):
            line += f" (while(actions) {', '.join(entry['actions'])})"
        if entry.get("emotion"):
            line += f" [emotion: {entry['emotion']}]"
        data_section += line + "\n"

    # Summary of interactions
    if character_data.get("addressees"):
        data_section += (
            f"  Interacts with: {', '.join(character_data['addressees'])}\n"
        )

    # Overall emotions
    if character_data.get("emotions"):
        unique_emotions = list(set(character_data["emotions"]))
        data_section += f"  Overall emotions: {unique_emotions}\n"

    return data_section