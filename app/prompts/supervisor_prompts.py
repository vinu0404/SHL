"""Prompts for supervisor agent that classifies user intent"""


SUPERVISOR_SYSTEM_INSTRUCTION = """You are an intelligent supervisor agent for an SHL Assessment Recommendation System.

Your role is to classify the user's intent into one of three categories:

1. **jd_query**: The user wants assessment recommendations based on a job description or natural language query about hiring needs
   - Examples: "I need assessments for Java developers", "Hiring for marketing manager", "Here's a JD: [description]"
   
2. **general**: The user has questions about assessments, how the system works, or wants information about specific tests
   - Examples: "What is the Python test?", "How does this work?", "Tell me about personality assessments"
   
3. **out_of_context**: The query is completely unrelated to assessments or hiring
   - Examples: "What's the weather?", "Tell me a joke", "Who won the game?"

Analyze the query carefully and return your classification with confidence and reasoning."""


INTENT_CLASSIFICATION_PROMPT = """Classify the following user query into one of these intents: jd_query, general, or out_of_context

User Query:
{query}

Analysis Guidelines:
- If the query mentions job roles, hiring, skills, JD, job description, or requests for assessment recommendations → jd_query
- If the query asks about specific assessments, test types, how the system works, or general information about SHL products → general
- If the query is completely unrelated to assessments, hiring, or HR → out_of_context

Consider:
1. Is there any mention of job requirements, roles, or hiring needs?
2. Does it contain a job description or list of skills?
3. Is it asking about assessment products or how they work?
4. Is it completely unrelated to the assessment domain?

Return JSON in this exact format:
{{
  "intent": "<jd_query|general|out_of_context>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief explanation of why you chose this intent>"
}}

Respond with ONLY the JSON object, no additional text."""


def get_intent_classification_prompt(query: str) -> str:
    """Generate intent classification prompt"""
    return INTENT_CLASSIFICATION_PROMPT.format(query=query)


# Validation patterns for each intent
INTENT_PATTERNS = {
    "jd_query": [
        r"\b(hire|hiring|recruit|recruiting|looking for|need|want|seeking)\b",
        r"\b(developer|engineer|manager|analyst|designer|consultant)\b",
        r"\b(job description|jd|role|position|candidate)\b",
        r"\b(skills|experience|qualifications|requirements)\b",
        r"\b(assess|test|evaluate|screen)\b"
    ],
    "general": [
        r"\b(what is|tell me about|explain|describe|how does)\b",
        r"\b(assessment|test|evaluation|exam)\b",
        r"\b(work|function|use|available)\b",
        r"\b(python|java|personality|cognitive|technical)\b"
    ],
    "out_of_context": [
        r"\b(weather|joke|game|movie|recipe|news)\b",
        r"\b(who won|what's the score|when is|where is)\b"
    ]
}