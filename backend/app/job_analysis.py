import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import PyPDF2
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

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text content from PDF file
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Extract text using PyPDF2
        text = ""
        with open(temp_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

async def parse_job_description_with_openai(job_text: str) -> Dict[str, Any]:
    """
    Parse job description text using OpenAI to extract structured information
    """
    
    if not client.api_key:
        print("❌ OpenAI API key not found")
        print("🔄 Using mock job analysis...")
        return generate_mock_job_analysis(job_text)
    
    prompt = f"""
    Parse the following job description and extract structured information in JSON format.
    
    Job Description:
    {job_text}
    
    Please extract and return a JSON object with the following structure:
    {{
        "job_title": "extracted job title",
        "company": "company name if mentioned",
        "required_skills": ["skill1", "skill2", "skill3"],
        "preferred_skills": ["preferred_skill1", "preferred_skill2"],
        "experience_level": "entry/mid/senior level",
        "description": "brief summary of the role",
        "responsibilities": ["responsibility1", "responsibility2"],
        "qualifications": ["qualification1", "qualification2"]
    }}
    
    Focus on extracting technical skills, programming languages, frameworks, tools, and relevant technologies.
    Return only the JSON object, no additional text.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at parsing job descriptions and extracting structured information. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Parse the JSON response
        job_data = json.loads(response.choices[0].message.content)
        
        print(f"✅ Job description parsed successfully using OpenAI")
        return job_data
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing OpenAI JSON response: {e}")
        print("🔄 Falling back to mock job analysis...")
        return generate_mock_job_analysis(job_text)
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error calling OpenAI API: {e}")
        print(f"🔍 Error type: {type(e)}")
        print(f"🔍 Error string: {error_str}")
        
        # Check for specific OpenAI errors that indicate quota/billing issues
        if any(keyword in error_str.lower() for keyword in [
            "quota", "billing", "insufficient_quota", "rate_limit", 
            "exceeded", "usage", "credits", "payment", "429", "error code: 429"
        ]):
            print("🔄 OpenAI quota/billing issue detected. Using mock analysis...")
            return generate_mock_job_analysis(job_text)
        else:
            print("🔄 OpenAI API error. Falling back to mock analysis...")
            return generate_mock_job_analysis(job_text)

def generate_mock_job_analysis(job_text: str) -> Dict[str, Any]:
    """
    Generate a mock job analysis when OpenAI API is not available
    This provides a helpful fallback with realistic sample data
    """
    
    # Try to extract some basic information from the text
    text_lower = job_text.lower()
    
    # Simple job title detection
    job_title = "Software Engineer"  # Default
    if "senior" in text_lower and ("developer" in text_lower or "engineer" in text_lower):
        job_title = "Senior Software Engineer"
    elif "junior" in text_lower and ("developer" in text_lower or "engineer" in text_lower):
        job_title = "Junior Software Engineer"
    elif "lead" in text_lower or "principal" in text_lower:
        job_title = "Lead Software Engineer"
    elif "frontend" in text_lower or "front-end" in text_lower:
        job_title = "Frontend Developer"
    elif "backend" in text_lower or "back-end" in text_lower:
        job_title = "Backend Developer"
    elif "fullstack" in text_lower or "full-stack" in text_lower:
        job_title = "Full Stack Developer"
    elif "data" in text_lower and "scientist" in text_lower:
        job_title = "Data Scientist"
    elif "devops" in text_lower:
        job_title = "DevOps Engineer"
    
    # Detect common skills mentioned in the text
    skill_keywords = {
        "python": "Python", "javascript": "JavaScript", "java": "Java", 
        "react": "React", "angular": "Angular", "vue": "Vue.js",
        "node": "Node.js", "express": "Express.js", "django": "Django",
        "flask": "Flask", "sql": "SQL", "postgresql": "PostgreSQL",
        "mysql": "MySQL", "mongodb": "MongoDB", "redis": "Redis",
        "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS",
        "azure": "Azure", "gcp": "Google Cloud", "git": "Git",
        "ci/cd": "CI/CD", "jenkins": "Jenkins", "terraform": "Terraform",
        "typescript": "TypeScript", "html": "HTML", "css": "CSS",
        "sass": "SASS", "webpack": "Webpack", "babel": "Babel",
        "rest": "REST APIs", "graphql": "GraphQL", "microservices": "Microservices"
    }
    
    detected_skills = []
    for keyword, skill_name in skill_keywords.items():
        if keyword in text_lower:
            detected_skills.append(skill_name)
    
    # If no skills detected, provide common ones
    if not detected_skills:
        detected_skills = ["JavaScript", "Python", "React", "Node.js", "SQL", "Git"]
    
    # Split detected skills into required and preferred
    mid_point = len(detected_skills) // 2
    required_skills = detected_skills[:mid_point] if mid_point > 0 else detected_skills[:3]
    preferred_skills = detected_skills[mid_point:] if mid_point > 0 else ["Docker", "AWS", "TypeScript"]
    
    return {
        "job_title": job_title,
        "company": "[Demo Mode - Company Name]",
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "experience_level": "Mid-level",
        "description": f"**[DEMO MODE]** This is a mock analysis of the job description. "
                      f"The original text contained {len(job_text)} characters. "
                      f"For accurate AI-powered analysis, please configure OpenAI API credentials.",
        "responsibilities": [
            "[Demo] Develop and maintain software applications",
            "[Demo] Collaborate with cross-functional teams", 
            "[Demo] Write clean, maintainable code",
            "[Demo] Participate in code reviews"
        ],
        "qualifications": [
            f"[Demo] Experience with {', '.join(required_skills[:3])}",
            "[Demo] Strong problem-solving skills",
            "[Demo] Bachelor's degree in Computer Science or related field",
            "[Demo] Excellent communication skills"
        ]
    }

def generate_demo_skill_match(resume_skills: List[str]) -> Dict[str, Any]:
    """
    Generate a demo skill match when job analysis fails or returns empty skills
    """
    
    # Create demo job skills based on common software engineering skills
    demo_required_skills = ["JavaScript", "Python", "React", "Node.js"]
    demo_preferred_skills = ["Docker", "AWS", "TypeScript", "Git"]
    
    # Find matches with resume skills
    matched_required = []
    matched_preferred = []
    
    for resume_skill in resume_skills:
        # Check exact matches (case insensitive)
        for demo_skill in demo_required_skills:
            if resume_skill.lower() == demo_skill.lower():
                matched_required.append({
                    "resume_skill": resume_skill,
                    "job_skill": demo_skill,
                    "match_type": "exact"
                })
        
        for demo_skill in demo_preferred_skills:
            if resume_skill.lower() == demo_skill.lower():
                matched_preferred.append({
                    "resume_skill": resume_skill,
                    "job_skill": demo_skill,
                    "match_type": "exact"
                })
    
    # Calculate percentages
    required_match_percent = (len(matched_required) / len(demo_required_skills)) * 100 if demo_required_skills else 0
    preferred_match_percent = (len(matched_preferred) / len(demo_preferred_skills)) * 100 if demo_preferred_skills else 0
    overall_match_percent = (required_match_percent * 0.7 + preferred_match_percent * 0.3)
    
    # Missing skills
    matched_required_names = [m["job_skill"].lower() for m in matched_required]
    matched_preferred_names = [m["job_skill"].lower() for m in matched_preferred]
    
    missing_required = [skill for skill in demo_required_skills if skill.lower() not in matched_required_names]
    missing_preferred = [skill for skill in demo_preferred_skills if skill.lower() not in matched_preferred_names]
    
    return {
        "overall_match_percentage": round(overall_match_percent, 1),
        "required_skills": {
            "total": len(demo_required_skills),
            "matched": len(matched_required),
            "match_percentage": round(required_match_percent, 1),
            "exact_matches": matched_required,
            "partial_matches": [],
            "missing": missing_required
        },
        "preferred_skills": {
            "total": len(demo_preferred_skills),
            "matched": len(matched_preferred),
            "match_percentage": round(preferred_match_percent, 1),
            "exact_matches": matched_preferred,
            "partial_matches": [],
            "missing": missing_preferred
        },
        "resume_skills": resume_skills,
        "analysis_summary": {
            "strong_match": overall_match_percent >= 80,
            "good_match": 60 <= overall_match_percent < 80,
            "fair_match": 40 <= overall_match_percent < 60,
            "weak_match": overall_match_percent < 40
        },
        "demo_mode": True,
        "demo_note": "This is a demo analysis using sample job requirements. For accurate matching, please configure OpenAI API credentials."
    }

def analyze_skill_match(resume_skills: List[str], job_required_skills: List[str], job_preferred_skills: List[str]) -> Dict[str, Any]:
    """
    Analyze skill match between resume and job description
    """
    
    # Check if this looks like demo data (empty skills lists indicate failed OpenAI parsing)
    if not job_required_skills and not job_preferred_skills:
        print("🔄 No job skills found - generating demo skill match...")
        return generate_demo_skill_match(resume_skills)
    
    # Normalize skills to lowercase for comparison
    resume_skills_lower = [skill.lower().strip() for skill in resume_skills if skill]
    job_required_lower = [skill.lower().strip() for skill in job_required_skills if skill]
    job_preferred_lower = [skill.lower().strip() for skill in job_preferred_skills if skill]
    
    # Find exact matches
    matched_required = []
    matched_preferred = []
    
    for resume_skill in resume_skills:
        resume_skill_lower = resume_skill.lower().strip()
        
        # Check required skills
        for job_skill in job_required_skills:
            if resume_skill_lower == job_skill.lower().strip():
                matched_required.append({
                    "resume_skill": resume_skill,
                    "job_skill": job_skill,
                    "match_type": "exact"
                })
        
        # Check preferred skills
        for job_skill in job_preferred_skills:
            if resume_skill_lower == job_skill.lower().strip():
                matched_preferred.append({
                    "resume_skill": resume_skill,
                    "job_skill": job_skill,
                    "match_type": "exact"
                })
    
    # Find partial matches (contains)
    partial_matched_required = []
    partial_matched_preferred = []
    
    for resume_skill in resume_skills:
        resume_skill_lower = resume_skill.lower().strip()
        
        # Check if resume skill contains or is contained in job skills
        for job_skill in job_required_skills:
            job_skill_lower = job_skill.lower().strip()
            if (resume_skill_lower in job_skill_lower or job_skill_lower in resume_skill_lower) and \
               not any(m["resume_skill"].lower() == resume_skill.lower() for m in matched_required):
                partial_matched_required.append({
                    "resume_skill": resume_skill,
                    "job_skill": job_skill,
                    "match_type": "partial"
                })
        
        for job_skill in job_preferred_skills:
            job_skill_lower = job_skill.lower().strip()
            if (resume_skill_lower in job_skill_lower or job_skill_lower in resume_skill_lower) and \
               not any(m["resume_skill"].lower() == resume_skill.lower() for m in matched_preferred):
                partial_matched_preferred.append({
                    "resume_skill": resume_skill,
                    "job_skill": job_skill,
                    "match_type": "partial"
                })
    
    # Find missing skills
    matched_required_skills_lower = [m["job_skill"].lower() for m in matched_required + partial_matched_required]
    matched_preferred_skills_lower = [m["job_skill"].lower() for m in matched_preferred + partial_matched_preferred]
    
    missing_required = [skill for skill in job_required_skills 
                       if skill.lower() not in matched_required_skills_lower]
    missing_preferred = [skill for skill in job_preferred_skills 
                        if skill.lower() not in matched_preferred_skills_lower]
    
    # Calculate match percentages
    total_required = len(job_required_skills)
    total_preferred = len(job_preferred_skills)
    
    required_match_percent = (len(matched_required) + len(partial_matched_required)) / total_required * 100 if total_required > 0 else 0
    preferred_match_percent = (len(matched_preferred) + len(partial_matched_preferred)) / total_preferred * 100 if total_preferred > 0 else 0
    
    overall_match_percent = (required_match_percent * 0.7 + preferred_match_percent * 0.3) if total_preferred > 0 else required_match_percent
    
    return {
        "overall_match_percentage": round(overall_match_percent, 1),
        "required_skills": {
            "total": total_required,
            "matched": len(matched_required) + len(partial_matched_required),
            "match_percentage": round(required_match_percent, 1),
            "exact_matches": matched_required,
            "partial_matches": partial_matched_required,
            "missing": missing_required
        },
        "preferred_skills": {
            "total": total_preferred,
            "matched": len(matched_preferred) + len(partial_matched_preferred),
            "match_percentage": round(preferred_match_percent, 1),
            "exact_matches": matched_preferred,
            "partial_matches": partial_matched_preferred,
            "missing": missing_preferred
        },
        "resume_skills": resume_skills,
        "analysis_summary": {
            "strong_match": overall_match_percent >= 80,
            "good_match": 60 <= overall_match_percent < 80,
            "fair_match": 40 <= overall_match_percent < 60,
            "weak_match": overall_match_percent < 40
        }
    }

async def process_job_description(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Main function to process job description PDF and extract structured data
    """
    print(f"=== PROCESSING JOB DESCRIPTION ===")
    print(f"Filename: {filename}")
    print(f"File size: {len(file_content)} bytes")
    
    # Extract text from PDF
    job_text = extract_text_from_pdf(file_content)
    
    if not job_text:
        print("❌ Could not extract text from PDF")
        return {
            "success": False,
            "error": "Could not extract text from PDF file"
        }
    
    print(f"Extracted text length: {len(job_text)} characters")
    
    # Parse with OpenAI
    job_data = await parse_job_description_with_openai(job_text)
    
    return {
        "success": True,
        "job_data": job_data,
        "raw_text": job_text
    }
