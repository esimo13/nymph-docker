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
        return {
            "job_title": "",
            "company": "",
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "",
            "description": job_text,
            "responsibilities": [],
            "qualifications": []
        }
    
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
        return {
            "job_title": "",
            "company": "",
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "",
            "description": job_text[:500] + "..." if len(job_text) > 500 else job_text,
            "responsibilities": [],
            "qualifications": []
        }
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        return {
            "job_title": "",
            "company": "",
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "",
            "description": job_text[:500] + "..." if len(job_text) > 500 else job_text,
            "responsibilities": [],
            "qualifications": []
        }

def analyze_skill_match(resume_skills: List[str], job_required_skills: List[str], job_preferred_skills: List[str]) -> Dict[str, Any]:
    """
    Analyze skill match between resume and job description
    """
    
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
