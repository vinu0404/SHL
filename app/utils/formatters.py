from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger("formatters")


def format_assessments_table(assessments: List[Dict[str, Any]]) -> str:
    """
    Format assessments as a readable table string for Chainlit display
    
    Args:
        assessments: List of assessment dictionaries
        
    Returns:
        str: Formatted table as markdown string
    """
    if not assessments:
        return "No assessments found."
    
    # Create markdown table
    table_lines = []
    
    # Header
    table_lines.append("| # | Assessment Name | Test Type | Duration | Remote | Adaptive | URL |")
    table_lines.append("|---|---|---|---|---|---|---|")
    
    # Rows
    for idx, assessment in enumerate(assessments, 1):
        name = assessment.get('name', 'N/A')
        test_types = ', '.join(assessment.get('test_type', [])) if assessment.get('test_type') else 'N/A'
        duration = f"{assessment.get('duration', 'N/A')} min" if assessment.get('duration') else 'N/A'
        remote = assessment.get('remote_support', 'N/A')
        adaptive = assessment.get('adaptive_support', 'N/A')
        url = assessment.get('url', 'N/A')
        
        # Truncate long names
        if len(name) > 40:
            name = name[:37] + "..."
        
        # Truncate long test types
        if len(test_types) > 30:
            test_types = test_types[:27] + "..."
        
        # Create clickable link
        url_link = f"[Link]({url})" if url != 'N/A' else 'N/A'
        
        table_lines.append(f"| {idx} | {name} | {test_types} | {duration} | {remote} | {adaptive} | {url_link} |")
    
    return '\n'.join(table_lines)


def format_assessment_response(assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format assessments for API response
    
    Args:
        assessments: List of assessment dictionaries
        
    Returns:
        List[Dict]: Formatted assessments
    """
    formatted = []
    
    for assessment in assessments:
        formatted_assessment = {
            "url": assessment.get('url', ''),
            "name": assessment.get('name', ''),
            "adaptive_support": assessment.get('adaptive_support', 'No'),
            "description": assessment.get('description', ''),
            "duration": assessment.get('duration'),
            "remote_support": assessment.get('remote_support', 'No'),
            "test_type": assessment.get('test_type', [])
        }
        formatted.append(formatted_assessment)
    
    return formatted


def format_detailed_assessment(assessment: Dict[str, Any]) -> str:
    """
    Format a single assessment with all details for display
    
    Args:
        assessment: Assessment dictionary
        
    Returns:
        str: Formatted assessment details
    """
    lines = []
    
    lines.append(f"**{assessment.get('name', 'Unknown Assessment')}**\n")
    
    if assessment.get('description'):
        lines.append(f"**Description:** {assessment['description']}\n")
    
    if assessment.get('test_type'):
        test_types = ', '.join(assessment['test_type'])
        lines.append(f"**Test Type:** {test_types}\n")
    
    if assessment.get('duration'):
        lines.append(f"**Duration:** {assessment['duration']} minutes\n")
    
    if assessment.get('job_levels'):
        lines.append(f"**Job Levels:** {assessment['job_levels']}\n")
    
    if assessment.get('languages'):
        lines.append(f"**Languages:** {assessment['languages']}\n")
    
    lines.append(f"**Remote Support:** {assessment.get('remote_support', 'N/A')}\n")
    lines.append(f"**Adaptive Support:** {assessment.get('adaptive_support', 'N/A')}\n")
    
    if assessment.get('url'):
        lines.append(f"**URL:** {assessment['url']}\n")
    
    return '\n'.join(lines)


def format_test_type_distribution(assessments: List[Dict[str, Any]]) -> str:
    """
    Format test type distribution for display
    
    Args:
        assessments: List of assessments
        
    Returns:
        str: Formatted distribution
    """
    from collections import Counter
    
    test_type_counts = Counter()
    
    for assessment in assessments:
        for test_type in assessment.get('test_type', []):
            test_type_counts[test_type] += 1
    
    if not test_type_counts:
        return "No test type information available."
    
    lines = ["**Test Type Distribution:**\n"]
    
    for test_type, count in test_type_counts.most_common():
        lines.append(f"- {test_type}: {count}")
    
    return '\n'.join(lines)


def format_error_message(error: str, context: str = None) -> str:
    """
    Format error message for user-friendly display
    
    Args:
        error: Error message
        context: Optional context information
        
    Returns:
        str: Formatted error message
    """
    message = f"❌ **Error:** {error}"
    
    if context:
        message += f"\n\n**Context:** {context}"
    
    return message


def format_success_message(message: str, details: str = None) -> str:
    """
    Format success message
    
    Args:
        message: Success message
        details: Optional details
        
    Returns:
        str: Formatted success message
    """
    formatted = f"✅ **Success:** {message}"
    
    if details:
        formatted += f"\n\n{details}"
    
    return formatted


def create_summary_stats(assessments: List[Dict[str, Any]]) -> str:
    """
    Create summary statistics for assessments
    
    Args:
        assessments: List of assessments
        
    Returns:
        str: Formatted summary
    """
    if not assessments:
        return "No assessments to summarize."
    
    total = len(assessments)
    
    # Count remote and adaptive support
    remote_count = sum(1 for a in assessments if a.get('remote_support') == 'Yes')
    adaptive_count = sum(1 for a in assessments if a.get('adaptive_support') == 'Yes')
    
    # Calculate average duration
    durations = [a.get('duration') for a in assessments if a.get('duration')]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    lines = [
        "**Summary Statistics:**\n",
        f"- Total Assessments: {total}",
        f"- Remote Support: {remote_count} ({remote_count/total*100:.1f}%)",
        f"- Adaptive Support: {adaptive_count} ({adaptive_count/total*100:.1f}%)",
    ]
    
    if avg_duration > 0:
        lines.append(f"- Average Duration: {avg_duration:.1f} minutes")
    
    return '\n'.join(lines)