"""
Chainlit Frontend Application for SHL Assessment Recommendation System

This is the main Chainlit application that provides an interactive chat interface
for users to get assessment recommendations.
"""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chainlit as cl
from chainlit_app.handlers.message_handler import MessageHandler
from chainlit_app.handlers.session_handler import SessionHandler
from chainlit_app.components.progress_tracker import ProgressTracker
from app.database import init_db, init_chroma
from app.utils.logger import get_logger
from chainlit_app.components.table_renderer import render_assessment_table, render_summary_stats
logger = get_logger("chainlit_app")

# Initialize handlers
message_handler = MessageHandler()
session_handler = SessionHandler()
progress_tracker = ProgressTracker()


@cl.on_chat_start
async def on_chat_start():
    """
    Called when a new chat session starts
    """
    logger.info("New chat session started")
    
    # Initialize session
    session_id = await session_handler.create_session()
    
    # Store session ID in user session
    cl.user_session.set("session_id", session_id)
    
    # Send welcome message
    welcome_message = """# Welcome to SHL Assessment Recommendation System!

I'm here to help you find the perfect assessments for your hiring needs.

**What I can help with:**
-  Recommend assessments based on job descriptions
-  Extract and analyze job descriptions from URLs
-  Answer questions about SHL assessments
-  Provide information about different test types

**How to use:**
1. **For Recommendations**: Simply describe the role you're hiring for or paste a job description
   - Example: "I need assessments for a Java developer who can collaborate with teams"
   
2. **For Questions**: Ask me about specific assessments or the system
   - Example: "What is the Python assessment?"
   
3. **With URLs**: Include a job posting URL and I'll extract the description
   - Example: "Here's a JD: https://example.com/job/12345"

**Let's get started! What would you like help with today?**
"""
    
    await cl.Message(content=welcome_message).send()
    
    # Show hint about usage
    await cl.Message(
        content="💡 **Tip**: You can paste a full job description, provide a URL, or just describe what you're looking for!",
        author="System"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Called when a user sends a message
    
    Args:
        message: The user's message
    """
    user_query = message.content
    session_id = cl.user_session.get("session_id")
    
    logger.info(f"Received message from session {session_id}: {user_query[:100]}...")
    
    # Show processing message
    processing_msg = cl.Message(content="🔄 Processing your request...")
    await processing_msg.send()
    
    try:
        # Create progress tracker
        progress = await progress_tracker.create_tracker()
        
        # Update progress - Analyzing query
        await progress_tracker.update(progress, "Analyzing your query...", 20)
        
        # Process the message
        result = await message_handler.handle_message(
            query=user_query,
            session_id=session_id,
            progress_callback=lambda msg, pct: progress_tracker.update(progress, msg, pct)
        )
        
        # Remove processing message
        await processing_msg.remove()
        
        # Remove progress tracker
        await progress_tracker.remove(progress)
        
        # Send response based on result type
        if result['type'] == 'recommendations':
            await send_recommendations_response(result)
        elif result['type'] == 'general':
            await send_general_response(result)
        elif result['type'] == 'error':
            await send_error_response(result)
        else:
            await send_fallback_response(result)
        
        # Update session stats
        await session_handler.update_session_stats(session_id, result)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        
        # Remove processing message
        try:
            await processing_msg.remove()
        except:
            pass
        
        # Send error message
        await cl.Message(
            content=f"❌ **Error**: An unexpected error occurred: {str(e)}\n\nPlease try again or rephrase your query.",
            author="System"
        ).send()


async def send_recommendations_response(result: dict):
    """
    Send response with assessment recommendations
    
    Args:
        result: Result dictionary with recommendations
    """
    recommendations = result['recommendations']
    query_info = result.get('query_info', {})
    
    # Build response message
    response_parts = []
    
    # Add query understanding
    if query_info.get('skills'):
        response_parts.append(f"**Detected Skills**: {', '.join(query_info['skills'][:5])}")
    
    if query_info.get('test_types'):
        response_parts.append(f"**Required Test Types**: {', '.join(query_info['test_types'])}")
    
    if query_info.get('duration'):
        response_parts.append(f"**Duration Constraint**: {query_info['duration']} minutes")
    
    if response_parts:
        understanding_msg = "**Understanding Your Requirements:**\n" + "\n".join(f"- {part}" for part in response_parts)
        await cl.Message(content=understanding_msg, author="System").send()
    
    # Send recommendations header
    recommendations_msg = f"## ✅ Found {len(recommendations)} Relevant Assessments\n\nHere are my recommendations tailored to your requirements:\n"
    await cl.Message(content=recommendations_msg).send()
    

    
    # Render assessments as a table
    table_content = render_assessment_table(recommendations)
    await cl.Message(content=table_content).send()
    
    # Send summary statistics
    summary_content = render_summary_stats(recommendations)
    await cl.Message(content=summary_content, author="System").send()


async def send_general_response(result: dict):
    """
    Send response for general queries
    
    Args:
        result: Result dictionary with general answer
    """
    answer = result['answer']
    
    # Send answer
    await cl.Message(content=answer).send()
    
    # If there are related assessments, show them
    if result.get('related_assessments'):
        await cl.Message(
            content="\n**Related Assessments:**",
            author="System"
        ).send()
        
        from chainlit_app.components.table_renderer import render_assessment_list
        assessments_list = render_assessment_list(result['related_assessments'])
        await cl.Message(content=assessments_list).send()


async def send_error_response(result: dict):
    """
    Send error response
    
    Args:
        result: Result dictionary with error
    """
    error_msg = result.get('message', 'An error occurred')
    
    await cl.Message(
        content=f"❌ **Error**: {error_msg}\n\nPlease try:\n"
                "- Rephrasing your query\n"
                "- Providing more details\n"
                "- Checking if any URLs are accessible",
        author="System"
    ).send()


async def send_fallback_response(result: dict):
    """
    Send fallback response
    
    Args:
        result: Result dictionary
    """
    await cl.Message(
        content="I processed your request but couldn't generate a specific response. "
                "Please try rephrasing your query or provide more details.",
        author="System"
    ).send()


@cl.on_chat_end
async def on_chat_end():
    """
    Called when chat session ends
    """
    session_id = cl.user_session.get("session_id")
    logger.info(f"Chat session ended: {session_id}")
    
    # Get session stats
    stats = await session_handler.get_session_stats(session_id)
    
    if stats:
        farewell_msg = f"""## 👋 Thank you for using SHL Assessment Recommendation System!

**Session Summary:**
- Queries processed: {stats.get('total_queries', 0)}
- Assessments recommended: {stats.get('total_recommendations', 0)}

Have a great day! 🌟
"""
        await cl.Message(content=farewell_msg, author="System").send()


# Initialize databases on startup
@cl.on_settings_update
async def setup_databases():
    """Initialize databases when app starts"""
    logger.info("Initializing databases for Chainlit app...")
    try:
        init_db()
        init_chroma()
        logger.info("Databases initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")


if __name__ == "__main__":
    # Run with: chainlit run chainlit_app/app.py
    pass