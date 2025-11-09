"""Prompts for general query agent"""


GENERAL_QUERY_SYSTEM_INSTRUCTION = """You are a knowledgeable assistant for the SHL Assessment Recommendation System.

Your role is to:
1. Answer questions about SHL assessments and products
2. Explain how the recommendation system works
3. Provide information about different test types
4. Help users understand assessment options

Test Types Available:
- **Ability & Aptitude (A)**: Measure cognitive abilities and reasoning
- **Biodata & Situational Judgement (B)**: Evaluate past behavior and decision-making
- **Competencies (C)**: Assess behavioral competencies and skills
- **Development & 360 (D)**: Development tools and feedback assessments
- **Assessment Exercises (E)**: Practical work exercises
- **Knowledge & Skills (K)**: Technical knowledge and skill tests
- **Personality & Behavior (P)**: Personality traits and behavioral styles
- **Simulations (S)**: Interactive work simulations

Be helpful, informative, and concise. If asked about specific assessments, use the provided context."""


GENERAL_ANSWER_PROMPT = """Answer the following question about SHL assessments or the recommendation system.

Question: {query}

{context}

Provide a clear, helpful answer. If the question is about specific assessments, reference the context provided. If you don't have enough information, acknowledge that and suggest how the user can get more details.

Keep your response concise (2-4 paragraphs) and user-friendly."""


ASSESSMENT_DETAILS_PROMPT = """The user is asking about a specific assessment or type of assessment.

User Query: {query}

Relevant Assessments from Catalog:
{assessments}

Provide detailed information about the assessment(s) they're asking about. Include:
- What it measures
- Who it's for (job levels)
- Duration if available
- Test type
- Remote/adaptive support

Be informative and help them understand if this assessment would be suitable for their needs."""


SYSTEM_EXPLANATION_PROMPT = """The user wants to know how the system works.

User Query: {query}

Explain:
1. How the recommendation system works
2. What inputs it accepts (natural language, JD text, URLs)
3. How it selects assessments
4. What information is provided in recommendations

Keep it simple and user-friendly. Focus on practical benefits."""


HOW_TO_USE_PROMPT = """The user needs help using the system.

User Query: {query}

Provide clear instructions on:
1. What kind of queries they can ask
2. How to format job descriptions
3. What information helps get better recommendations
4. Examples of good queries

Be practical and give examples."""


OUT_OF_CONTEXT_RESPONSE = """I appreciate your question, but I'm specifically designed to help with SHL assessment recommendations and queries related to hiring and talent evaluation.

I can help you with:
- Recommending assessments based on job descriptions
- Explaining different types of SHL assessments
- Answering questions about specific tests
- Understanding how to use this recommendation system

Please feel free to ask me anything related to assessments or hiring needs!"""


def get_general_answer_prompt(query: str, context: str = "") -> str:
    """Generate general answer prompt"""
    context_section = f"\nRelevant Context:\n{context}" if context else ""
    return GENERAL_ANSWER_PROMPT.format(query=query, context=context_section)


def get_assessment_details_prompt(query: str, assessments: str) -> str:
    """Generate assessment details prompt"""
    return ASSESSMENT_DETAILS_PROMPT.format(query=query, assessments=assessments)


def get_system_explanation_prompt(query: str) -> str:
    """Generate system explanation prompt"""
    return SYSTEM_EXPLANATION_PROMPT.format(query=query)


def get_how_to_use_prompt(query: str) -> str:
    """Generate how-to-use prompt"""
    return HOW_TO_USE_PROMPT.format(query=query)


# Common questions and answers
FAQ_RESPONSES = {
    "how does it work": """This system uses AI to recommend SHL assessments based on your hiring needs. Simply:
1. Describe the role you're hiring for or paste a job description
2. The system analyzes the requirements and skills needed
3. It recommends 5-10 most relevant assessments from the SHL catalog
4. Each recommendation includes details like test type, duration, job levels, and description

The system ensures balanced recommendations - if you need both technical and soft skills, you'll get a mix of Knowledge & Skills and Personality & Behavior assessments.""",
    
    "what can i ask": """You can ask about:
- Assessment recommendations: "I need tests for a Python developer"
- Specific assessments: "Tell me about the Python assessment"
- Test types: "What are personality assessments?"
- System usage: "How do I use this?"
- Job descriptions: Paste a full JD or provide a URL

Examples:
- "Hiring for Java developers who can collaborate with teams"
- "Need assessments for mid-level data analysts"
- "What is the Cognitive Ability test?"
- "Looking for tests that take less than 30 minutes\"""",
    
    "test types": """SHL offers 8 main test types:

1. **Knowledge & Skills (K)**: Technical tests (Python, Java, SQL, etc.)
2. **Personality & Behavior (P)**: Personality traits, work styles, soft skills
3. **Ability & Aptitude (A)**: Cognitive abilities, reasoning, problem-solving
4. **Competencies (C)**: Leadership, management, behavioral competencies
5. **Biodata & Situational Judgement (B)**: Past behavior, decision-making
6. **Simulations (S)**: Interactive work scenarios
7. **Assessment Exercises (E)**: Practical work exercises
8. **Development & 360 (D)**: Development and feedback tools

The system automatically recommends the right mix based on your job requirements."""
}


def get_faq_response(query_lower: str) -> str:
    """Get FAQ response if query matches common questions"""
    for key, response in FAQ_RESPONSES.items():
        if key in query_lower:
            return response
    return ""