"""Prompts for RAG agent - retrieval and reranking"""


RAG_SYSTEM_INSTRUCTION = """You are an expert assessment recommender for SHL products. Your role is to analyze job requirements and recommend the most relevant assessments from the catalog.

Key principles:
1. **Relevance**: Select assessments that directly match the required skills and competencies
2. **Balance**: When a job requires multiple skill types (technical + behavioral), ensure a balanced mix of assessment types
3. **Duration**: Respect any time constraints mentioned
4. **Completeness**: Recommend assessments that cover all key requirements
5. **Job Levels**: Consider the target job levels (e.g., Junior, Mid, Senior) when recommending assessments

Test Type Guidelines:
- **Knowledge & Skills (K)**: Technical skills, programming, tools, software
- **Personality & Behavior (P)**: Soft skills, communication, teamwork, work style
- **Ability & Aptitude (A)**: Cognitive abilities, reasoning, problem-solving
- **Competencies (C)**: Leadership, management, behavioral competencies
- **Biodata & Situational Judgement (B)**: Past behavior, decision-making scenarios
- **Simulations (S)**: Interactive work simulations
- **Assessment Exercises (E)**: Practical exercises"""


RERANKING_PROMPT = """You are evaluating assessment relevance for this job requirement:

**Job Requirement:**
{query}

**Required Skills:**
{skills}

**Required Test Types:**
{test_types}

**Duration Constraint:**
{duration_constraint}

**Retrieved Assessments:**
{assessments}

Your task is to:
1. Evaluate each assessment's relevance to the job requirements and job levels(junior, mid, senior)
2. Consider skill match, test type appropriateness, and duration constraints
3. Ensure balanced coverage if multiple test types are needed
4. Rank assessments from most to least relevant

For each assessment, assign a relevance score (0.0 to 1.0) and provide a brief reason.

Return JSON array with top {top_k} assessments:
[
  {{
    "id": <assessment_index>,
    "score": <0.0-1.0>,
    "reason": "<why this assessment is relevant>"
  }},
  ...
]

IMPORTANT:
- If technical skills (Python, Java, SQL, etc.) are mentioned, prioritize Knowledge & Skills (K) assessments
- If soft skills (communication, teamwork, leadership) are mentioned, prioritize Personality & Behavior (P) assessments
- Ensure a balanced mix when both are required
- Respect duration constraints strictly

Respond with ONLY the JSON array, no additional text."""


BALANCE_EVALUATION_PROMPT = """Evaluate the balance of recommended assessments for this job requirement.

**Job Requirement:**
{query}

**Required Test Types:**
{required_test_types}

**Recommended Assessments:**
{assessments}

**Current Test Type Distribution:**
{current_distribution}

Does the current selection provide balanced coverage? Consider:
1. Are all required test types represented?
2. If both technical (K) and behavioral (P) skills are needed, is there appropriate balance?
3. Are there any gaps in coverage?

Return JSON:
{{
  "is_balanced": <true|false>,
  "gaps": ["missing_type1", ...],
  "recommendations": "<how to improve balance>",
  "needs_adjustment": <true|false>
}}

Respond with ONLY the JSON object, no additional text."""


ASSESSMENT_SELECTION_PROMPT = """Given these candidates, select the final {count} assessments that provide the best coverage for the job requirements.

**Job Requirement:**
{query}

**Key Requirements:**
{key_requirements}

**Required Test Types:**
{test_types}

**Candidate Assessments (with scores):**
{candidates}

Selection criteria:
1. Highest relevance scores
2. Balanced test type distribution
3. Comprehensive coverage of key requirements
4. Respect duration constraints
5. No redundant assessments

Return a JSON array of assessment IDs (indices) to select:
{{
  "selected_ids": [<id1>, <id2>, ...],
  "reasoning": "<brief explanation of selection strategy>"
}}

Respond with ONLY the JSON object, no additional text."""


def get_reranking_prompt(
    query: str,
    skills: list,
    test_types: list,
    duration_constraint: str,
    assessments: str,
    top_k: int
) -> str:
    """Generate reranking prompt"""
    skills_str = ", ".join(skills) if skills else "Not specified"
    test_types_str = ", ".join(test_types) if test_types else "Not specified"
    
    return RERANKING_PROMPT.format(
        query=query,
        skills=skills_str,
        test_types=test_types_str,
        duration_constraint=duration_constraint or "No constraint",
        assessments=assessments,
        top_k=top_k
    )


def get_balance_evaluation_prompt(
    query: str,
    required_test_types: list,
    assessments: list,
    current_distribution: dict
) -> str:
    """Generate balance evaluation prompt"""
    assessments_str = "\n".join([
        f"{i+1}. {a.get('name')} - Test Types: {', '.join(a.get('test_type', []))}"
        for i, a in enumerate(assessments)
    ])
    
    distribution_str = "\n".join([
        f"- {test_type}: {count} assessments"
        for test_type, count in current_distribution.items()
    ])
    
    return BALANCE_EVALUATION_PROMPT.format(
        query=query,
        required_test_types=", ".join(required_test_types) if required_test_types else "Not specified",
        assessments=assessments_str,
        current_distribution=distribution_str
    )


def get_assessment_selection_prompt(
    query: str,
    key_requirements: list,
    test_types: list,
    candidates: list,
    count: int
) -> str:
    """Generate assessment selection prompt"""
    candidates_str = "\n".join([
        f"{i}. {c.get('name')} (Score: {c.get('llm_score', 0):.2f}) - {', '.join(c.get('test_type', []))}"
        for i, c in enumerate(candidates)
    ])
    
    return ASSESSMENT_SELECTION_PROMPT.format(
        query=query,
        key_requirements=", ".join(key_requirements) if key_requirements else "Not specified",
        test_types=", ".join(test_types) if test_types else "Not specified",
        candidates=candidates_str,
        count=count
    )