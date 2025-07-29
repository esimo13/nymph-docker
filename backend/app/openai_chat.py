import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import openai
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_chat_response(
    message: str, 
    resume_data: Dict[str, Any] = None, 
    chat_history: List[Dict[str, Any]] = []
) -> str:
    """
    Get chat response from OpenAI based on user message and resume context
    """
    
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Build context from resume data
    context = ""
    if resume_data:
        context = f"""
Here is the resume data for context:

Personal Information:
- Name: {resume_data.get('personal_info', {}).get('full_name', 'N/A')}
- Email: {resume_data.get('personal_info', {}).get('email', 'N/A')}
- Phone: {resume_data.get('personal_info', {}).get('phone', 'N/A')}
- Location: {resume_data.get('personal_info', {}).get('location', 'N/A')}

Experience:
"""
        for exp in resume_data.get('experience', []):
            context += f"- {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('duration', 'N/A')})\n"
        
        context += f"\nEducation:\n"
        for edu in resume_data.get('education', []):
            context += f"- {edu.get('degree', 'N/A')} in {edu.get('field', 'N/A')} from {edu.get('institution', 'N/A')}\n"
        
        context += f"\nSkills: {', '.join(resume_data.get('skills', []))}\n"
        
        if resume_data.get('projects'):
            context += f"\nProjects:\n"
            for project in resume_data.get('projects', []):
                context += f"- {project.get('name', 'N/A')}: {project.get('description', 'N/A')}\n"
    
    # Build conversation history
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful AI assistant that specializes in analyzing resumes and providing career advice. 

{context}

You can help with:
- Analyzing the resume for strengths and weaknesses
- Suggesting improvements to specific sections
- Identifying missing skills or experiences
- Providing interview preparation tips
- Comparing qualifications to job requirements
- Career guidance and next steps

Be conversational, helpful, and specific in your responses. Use the resume data to provide personalized advice."""
        }
    ]
    
    # Add chat history
    for chat in chat_history[-10:]:  # Keep last 10 messages for context
        # Handle both dict and ChatMessageSchema objects
        if hasattr(chat, 'role'):
            # ChatMessageSchema object
            role = chat.role
            content = chat.content
        else:
            # Dictionary
            role = chat.get("role", "user")
            content = chat.get("content", "")
        
        messages.append({
            "role": role,
            "content": content
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": message
    })
    
    try:
        # Check if API key is available and valid
        if not client.api_key or client.api_key.strip() == "":
            print("OpenAI API key not available, using mock response")
            return get_mock_chat_response(message, resume_data, chat_history)
        
        # Make OpenAI API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Log the error for debugging
        print(f"OpenAI API error: {str(e)}")
        
        # Check for various types of API errors and provide a mock response
        error_msg = str(e).lower()
        if any(term in error_msg for term in [
            "quota", "insufficient_quota", "exceeded", "billing", "limit", 
            "rate limit", "credits", "usage", "insufficient", "payment",
            "authentication", "invalid api key", "unauthorized"
        ]):
            print("OpenAI API quota/auth issue detected, falling back to mock response")
            return get_mock_chat_response(message, resume_data, chat_history)
        else:
            # For any other error, also fall back to mock response to keep the app working
            print("OpenAI API error, falling back to mock response")
            return get_mock_chat_response(message, resume_data, chat_history)

def get_mock_chat_response(
    message: str, 
    resume_data: Dict[str, Any] = None, 
    chat_history: List[Dict[str, Any]] = []
) -> str:
    """
    Provide a mock response when OpenAI API is not available
    """
    message_lower = message.lower()
    
    # Get basic info from resume
    name = resume_data.get('personal_info', {}).get('full_name', 'your') if resume_data else 'your'
    skills = resume_data.get('skills', []) if resume_data else []
    experience_count = len(resume_data.get('experience', [])) if resume_data else 0
    
    # Generate contextual responses based on the message
    if any(word in message_lower for word in ['hello', 'hi', 'hey']) and len(message.split()) <= 3:
        return f"Hello! I'm here to help you analyze {name}'s resume and provide career guidance. I can see you have {len(skills)} technical skills listed and {experience_count} work experiences. What would you like to know about the resume or career development?"
    
    elif any(word in message_lower for word in ['strength', 'strong', 'good', 'positive']):
        if skills:
            return f"Based on {name}'s resume, I can see several strengths:\n\n• **Technical Skills**: You have a solid foundation with {', '.join(skills[:3])}{'...' if len(skills) > 3 else ''}\n• **Experience**: {experience_count} work experiences show professional growth\n• **Project Portfolio**: The projects demonstrate practical application of skills\n\nThese are valuable assets in today's competitive job market!"
        else:
            return "I'd be happy to analyze the strengths of this resume! Could you share the resume data so I can provide more specific feedback?"
    
    elif any(word in message_lower for word in ['improve', 'better', 'enhance', 'weakness']):
        return f"Here are some areas where {name}'s resume could be enhanced:\n\n• **Skills Section**: Consider adding more specific technologies or frameworks\n• **Project Descriptions**: Include quantifiable results and impact\n• **Certifications**: Industry certifications can strengthen credibility\n• **Keywords**: Optimize for ATS systems with relevant industry terms\n\nWould you like me to elaborate on any of these areas?"
    
    elif any(word in message_lower for word in ['skill', 'technology', 'learn']):
        return f"Based on current market trends and {name}'s background, I'd recommend focusing on:\n\n• **Cloud Technologies**: AWS, Azure, or Google Cloud\n• **DevOps Tools**: Docker, Kubernetes, CI/CD pipelines\n• **Modern Frameworks**: React, Node.js, or similar based on your field\n• **Data Skills**: SQL, Python for data analysis\n\nWhich area interests you most for skill development?"
    
    elif any(word in message_lower for word in ['interview', 'prepare', 'question']):
        return f"Great question! Based on {name}'s background, here are key interview areas to prepare:\n\n• **Technical Questions**: Be ready to explain your projects in detail\n• **Behavioral Questions**: Prepare STAR method examples\n• **Problem-Solving**: Practice coding challenges or case studies\n• **Company Research**: Know the role requirements and company culture\n\nWould you like me to suggest specific questions for any of these areas?"
    
    elif any(word in message_lower for word in ['project', 'portfolio', 'build']):
        return f"Excellent! Building projects is crucial for career development. Here are project ideas that align with {name}'s skills:\n\n• **Full-Stack Application**: Combine frontend and backend technologies\n• **API Development**: Build and document a RESTful API\n• **Data Visualization**: Create interactive dashboards\n• **Open Source Contribution**: Contribute to existing projects\n\nFocus on projects that solve real problems and showcase your best skills!"
    
    else:
        return f"I'm currently running in **demo mode** (OpenAI API not available), but I can still help analyze {name}'s resume!\n\nBased on your question: \"{message}\"\n\nI can provide guidance on:\n• Resume analysis and improvements\n• Skill recommendations  \n• Interview preparation tips\n• Project suggestions\n• Career development advice\n\n*Note: For full AI-powered responses, please check your OpenAI API configuration.*\n\nWhat specific aspect of the resume would you like me to focus on?"

def get_suggested_questions(resume_data: Dict[str, Any]) -> List[str]:
    """
    Generate suggested questions based on resume data
    """
    suggestions = [
        "What are the strongest points of this resume?",
        "What skills should I add to be more competitive?",
        "How can I improve my experience section?",
        "What are some good interview questions I should prepare for?",
        "How does my background compare to industry standards?"
    ]
    
    # Add specific suggestions based on resume content
    if resume_data:
        if not resume_data.get('certifications'):
            suggestions.append("What certifications would benefit my career?")
        
        if len(resume_data.get('projects', [])) < 3:
            suggestions.append("What projects should I build to strengthen my portfolio?")
        
        if not resume_data.get('personal_info', {}).get('github'):
            suggestions.append("How important is having a GitHub profile?")
    
    return suggestions[:6]  # Return top 6 suggestions
