"""Prompts for JD extraction and processing agents"""


JD_EXTRACTOR_SYSTEM_INSTRUCTION = """You are a URL extraction specialist. Your job is to identify and extract URLs from user queries, particularly those that might contain job descriptions."""


URL_EXTRACTION_PROMPT = """Extract any URLs from the following text. Look for both complete URLs (starting with http/https) and partial URLs.

Text:
{query}

If URLs are found, identify which one is most likely to contain a job description based on the URL structure.

Return JSON in this exact format:
{{
  "has_url": <true|false>,
  "urls": ["url1", "url2", ...],
  "primary_url": "<most likely JD URL or null>"
}}

Respond with ONLY the JSON object, no additional text."""


JD_PROCESSOR_SYSTEM_INSTRUCTION = """You are an expert at analyzing job descriptions and extracting key requirements for assessment recommendations.

Your task is to:
1. Parse job descriptions and identify key skills, qualifications, and requirements
2. Determine what types of assessments would be most appropriate
3. Extract duration constraints if mentioned
4. Identify job levels (entry, mid, senior, etc.)"""


JD_ENHANCEMENT_PROMPT = """Analyze the following job description or query and extract structured information that will help recommend appropriate assessments.

Query/Job Description:
{jd_text}

Extract and structure the following information:

1. **Technical Skills**: List all technical skills, programming languages, tools, frameworks mentioned
2. **Soft Skills**: List all soft skills, behavioral traits, personality attributes mentioned
3. **Job Level**: Determine the seniority level (Graduate, Mid-Professional, Senior, Executive, etc.)
4. **Duration Constraint**: Extract any time constraint mentioned (e.g., "30 minutes", "1 hour", "at most 90 minutes")
5. **Required Test Types**: Based on the requirements, determine which test types are needed:
   - Knowledge & Skills (K): Technical knowledge, programming, tools
   - Personality & Behavior (P): Soft skills, communication, teamwork
   - Ability & Aptitude (A): Cognitive abilities, problem-solving
   - Competencies (C): Leadership, management competencies
   - Other test types as appropriate

6. **Key Requirements**: List the 5-10 most important requirements that should drive assessment selection

Return JSON in this exact format:
{{
  "original_query": "<the original text>",
  "cleaned_query": "<cleaned version>",
  "extracted_skills": ["skill1", "skill2", ...],
  "extracted_duration": <integer in minutes or null>,
  "extracted_job_levels": ["level1", "level2", ...],
  "required_test_types": ["test_type1", "test_type2", ...],
  "key_requirements": ["requirement1", "requirement2", ...]
}}

Be thorough but concise. Focus on information that will help select the right assessments.

Respond with ONLY the JSON object, no additional text."""


QUERY_ENHANCEMENT_PROMPT = """Enhance this query for better assessment retrieval. Expand abbreviations, add context, and make it more descriptive while preserving the original meaning.

Original Query:
{query}

Create an enhanced version that:
- Expands technical abbreviations (SQL, JS, etc.)
- Adds relevant context
- Includes synonyms for key skills
- Makes implicit requirements explicit

Enhanced Query (single paragraph, 2-4 sentences):"""


def get_url_extraction_prompt(query: str) -> str:
    """Generate URL extraction prompt"""
    return URL_EXTRACTION_PROMPT.format(query=query)


def get_jd_enhancement_prompt(jd_text: str) -> str:
    """Generate JD enhancement prompt"""
    return JD_ENHANCEMENT_PROMPT.format(jd_text=jd_text)


def get_query_enhancement_prompt(query: str) -> str:
    """Generate query enhancement prompt"""
    return QUERY_ENHANCEMENT_PROMPT.format(query=query)