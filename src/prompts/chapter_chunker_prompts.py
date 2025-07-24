"""
Prompt templates for chapter chunking and narrative analysis.
Used by ChapterChunker for text processing and summarization.
"""

CHAPTER_SUMMARY_PROMPT = """Summarize this chapter in 2-3 sentences, focusing on key plot points, character development, and major themes:

Chapter: {chapter_text}

Summary:"""

SEMANTIC_CLASSIFICATION_PROMPT = """Classify this text as one of: {semantic_types}.

Text: "{text}..."

Classification (respond with just one word):"""

THEME_EXTRACTION_PROMPT = """Extract 2-3 main themes from this text. Choose from common literary themes like: magic, adventure, friendship, conflict, romance, mystery, power, sacrifice, redemption, nature, family, betrayal, courage, wisdom, etc.

Text: {text}...

Themes (comma-separated):"""

ENTITY_EXTRACTION_PROMPT = """Extract only the 3-5 most important character names and place names from this text. 
RESOLVE METAPHORS: Connect descriptions ("the old wizard"), roles ("the captain"), and relationships ("his apprentice") to their proper names using context.
Return as simple comma-separated list without categories or descriptions - use proper names only:

Text: {text}

Important entities (proper names only):"""