import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from vlmrun.client import VLMRun
    VLM_AVAILABLE = True
    print("✅ VLM.run SDK imported successfully!")
except ImportError as e:
    print(f"❌ VLM.run SDK not available: {e}")
    print("Using mock data")
    VLM_AVAILABLE = False

async def parse_resume_with_vlm(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Parse resume using VLM.run SDK
    """
    
    # Check if VLM is available and API key is set
    vlm_api_key = os.getenv("VLMRUN_API_KEY") or os.getenv("VLM_API_KEY")
    
    if not VLM_AVAILABLE or not vlm_api_key:
        print("Warning: VLM.run SDK not available or API key not set, using mock data")
        return get_mock_resume_data()
    
    try:
        # Initialize VLM client
        os.environ["VLMRUN_API_KEY"] = vlm_api_key
        client = VLMRun()
        
        print(f"Processing resume with VLM.run: {filename}")
        
        try:
            # For PDF documents, use document.generate with file path
            if filename.lower().endswith('.pdf'):
                print(f"Processing PDF document: {filename}")
                
                # Save file content to temporary file for VLM processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Use the document.resume domain with file path (as Path object)
                    from pathlib import Path
                    response = client.document.generate(
                        file=Path(temp_file_path),  # Pass file path as Path object
                        domain="document.resume"
                    )
                    
                    print(f"VLM.run response status: {getattr(response, 'status', 'unknown')}")
                    print(f"VLM.run response type: {type(response)}")
                    print(f"VLM.run response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                    
                finally:
                    # Always clean up temp file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
            else:
                # For images or other formats, try image processing
                print(f"Processing as image: {filename}")
                from PIL import Image
                import io
                
                # Convert file content to PIL Image
                image = Image.open(io.BytesIO(file_content))
                response = client.image.generate(
                    images=[image],
                    domain="document.resume"
                )
                
                print(f"VLM.run response status: {getattr(response, 'status', 'unknown')}")
                print(f"VLM.run response type: {type(response)}")
                print(f"VLM.run response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            # Check if processing completed
            if hasattr(response, 'status') and response.status == "completed":
                print("VLM processing completed successfully!")
                # Extract structured data from response
                if hasattr(response, 'response'):
                    resume_data = response.response
                    print(f"VLM response data type: {type(resume_data)}")
                    print(f"VLM response data preview: {str(resume_data)[:500]}...")
                    
                    # Convert VLM response to our expected format
                    structured_data = convert_vlm_response_to_resume_format(resume_data)
                    print("Successfully parsed resume with VLM.run!")
                    return structured_data
                else:
                    print("VLM response completed but no data returned, using mock data")
                    return get_mock_resume_data()
            else:
                print(f"VLM processing status: {getattr(response, 'status', 'unknown')}")
                print(f"VLM response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                print("Using mock data due to non-completed status")
                return get_mock_resume_data()
                
        except Exception as e:
            print(f"VLM API error: {e}")
            print("Falling back to mock data")
            return get_mock_resume_data()
            
    except Exception as e:
        print(f"VLM API error: {e}")
        print("Falling back to mock data")
        return get_mock_resume_data()

def convert_vlm_response_to_resume_format(vlm_data) -> Dict[str, Any]:
    """
    Convert VLM.run response to our expected resume format
    """
    # VLM.run might return data in different formats
    # We'll try to extract and normalize it to our schema
    
    try:
        print(f"Converting VLM data: {type(vlm_data)}")
        
        # If vlm_data is already a dict, use it directly
        if isinstance(vlm_data, dict):
            data = vlm_data
        elif hasattr(vlm_data, '__dict__'):
            # Try to convert object to dict
            data = vlm_data.__dict__
        else:
            # Try to extract attributes from the response object
            data = {}
            for attr in dir(vlm_data):
                if not attr.startswith('_') and not callable(getattr(vlm_data, attr)):
                    try:
                        data[attr] = getattr(vlm_data, attr)
                    except:
                        continue
        
        print(f"Extracted data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Handle the VLM.run structured response format
        if isinstance(data, dict) and 'contact_info' in data:
            # This is the structured VLM response format
            contact_info = data.get('contact_info', {})
            
            print(f"DEBUG: contact_info = {contact_info}")
            print(f"DEBUG: data keys = {list(data.keys())}")
            
            # Map VLM response to our resume format
            resume_data = {
                "personal_info": {
                    "full_name": contact_info.get("full_name") or data.get("name") or data.get("applicant_name") or "",
                    "email": contact_info.get("email") or data.get("email") or data.get("email_address") or "",
                    "phone": contact_info.get("phone") or data.get("phone") or data.get("phone_number") or data.get("contact_number") or "",
                    "location": contact_info.get("address") or contact_info.get("location") or data.get("location") or data.get("address") or data.get("city") or "",
                    "linkedin": contact_info.get("linkedin") or data.get("linkedin") or data.get("linkedin_url") or "",
                    "github": contact_info.get("github") or data.get("github") or data.get("github_url") or "",
                    "portfolio": contact_info.get("portfolio") or contact_info.get("website") or data.get("website") or data.get("portfolio") or ""
                },
                "experience": extract_experience(data),
                "education": extract_education(data),
                "skills": extract_skills(data),
                "projects": extract_projects(data),
                "certifications": extract_certifications(data),
                "languages": extract_languages(data)
            }
            
            print(f"DEBUG: mapped personal_info = {resume_data['personal_info']}")
            print(f"DEBUG: mapped skills = {resume_data['skills'][:5] if resume_data['skills'] else 'No skills'}")
            print(f"DEBUG: raw technical_skills = {data.get('technical_skills', 'Not found')}")
            print(f"VLM parsing completed. Data type: {type(data)}")
            print(f"Parsed data keys: {list(resume_data.keys())}")
            
            # Check if we got any meaningful data
            has_data = any([
                resume_data["personal_info"]["full_name"],
                resume_data["personal_info"]["email"],
                resume_data["experience"],
                resume_data["education"],
                resume_data["skills"]
            ])
            
            if has_data:
                print("Successfully converted VLM response to resume format")
                return resume_data
            else:
                print("No meaningful data extracted from VLM response, using mock data")
                return get_mock_resume_data()
        
        # If the data looks like it might contain extracted text, try to parse it
        if isinstance(data, dict):
            # Look for common resume fields
            text_content = data.get('text') or data.get('content') or data.get('extracted_text') or str(data)
            
            # If we have text content, try to extract resume information from it
            if text_content and isinstance(text_content, str) and len(text_content) > 50:
                print(f"Found text content: {text_content[:200]}...")
                # For now, return a basic structure with the text - later we can enhance this
                return extract_resume_from_text(text_content)
        
        print("No structured data found, using mock data")
        return get_mock_resume_data()
        
    except Exception as e:
        print(f"Error converting VLM response: {e}")
        return get_mock_resume_data()

def extract_resume_from_text(text_content: str) -> Dict[str, Any]:
    """
    Extract resume information from raw text content
    """
    import re
    
    # Basic extraction patterns
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    
    # Extract email
    emails = re.findall(email_pattern, text_content)
    email = emails[0] if emails else ""
    
    # Extract phone
    phones = re.findall(phone_pattern, text_content)
    phone = phones[0] if phones else ""
    
    # Try to extract name (first line that's not email/phone)
    lines = text_content.split('\n')
    name = ""
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and not re.search(email_pattern, line) and not re.search(phone_pattern, line) and len(line.split()) <= 4:
            name = line
            break
    
    # Basic skills extraction (look for common tech terms)
    skill_keywords = ['python', 'javascript', 'react', 'node', 'sql', 'aws', 'docker', 'git', 'java', 'css', 'html']
    found_skills = []
    text_lower = text_content.lower()
    for skill in skill_keywords:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return {
        "personal_info": {
            "full_name": name,
            "email": email,
            "phone": phone,
            "location": "",
            "linkedin": "",
            "github": "",
            "website": ""
        },
        "experience": [],
        "education": [],
        "skills": found_skills,
        "projects": [],
        "certifications": [],
        "languages": []
    }

def extract_experience(data) -> list:
    """Extract work experience from VLM response"""
    experience = data.get("experience") or data.get("work_experience") or data.get("employment") or []
    
    if not isinstance(experience, list):
        return []
    
    formatted_exp = []
    for exp in experience:
        if isinstance(exp, dict):
            # Safe string concatenation with None checks
            start_date = exp.get("start_date") or ""
            end_date = exp.get("end_date") or ""
            duration = exp.get("duration") or exp.get("dates") or exp.get("period") or ""
            
            # Only concatenate dates if both exist
            if start_date and end_date and not duration:
                duration = f"{start_date} - {end_date}"
            
            formatted_exp.append({
                "position": exp.get("position") or exp.get("title") or exp.get("job_title") or exp.get("role") or "",
                "company": exp.get("company") or exp.get("employer") or exp.get("organization") or "",
                "duration": duration,
                "description": exp.get("description") or exp.get("responsibilities") or exp.get("summary") or "",
                "achievements": exp.get("achievements") or exp.get("accomplishments") or []
            })
    
    return formatted_exp

def extract_education(data) -> list:
    """Extract education from VLM response"""
    education = data.get("education") or data.get("academic_background") or []
    
    if not isinstance(education, list):
        return []
    
    formatted_edu = []
    for edu in education:
        if isinstance(edu, dict):
            formatted_edu.append({
                "degree": edu.get("degree") or edu.get("qualification") or "",
                "field": edu.get("field") or edu.get("major") or edu.get("subject") or edu.get("field_of_study") or "",
                "institution": edu.get("institution") or edu.get("school") or edu.get("university") or "",
                "graduation_year": edu.get("year") or edu.get("graduation_year") or edu.get("graduation_date") or "",
                "gpa": edu.get("gpa") or edu.get("grade") or ""
            })
    
    return formatted_edu

def extract_skills(data) -> list:
    """Extract skills from VLM response"""
    # VLM.run returns technical_skills
    skills = data.get("skills") or data.get("technical_skills") or data.get("competencies") or []
    
    # If technical_skills is a dict with categories, flatten it
    if isinstance(skills, dict):
        all_skills = []
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    if isinstance(skill, dict):
                        # If skill is an object with name/level, extract the name
                        skill_name = skill.get('name') or skill.get('skill') or str(skill)
                        all_skills.append(skill_name)
                    else:
                        all_skills.append(str(skill))
            elif isinstance(skill_list, str):
                all_skills.extend([s.strip() for s in skill_list.split(',') if s.strip()])
        return all_skills
    elif isinstance(skills, str):
        # If skills is a string, split by common separators
        return [skill.strip() for skill in skills.replace(',', '\n').replace(';', '\n').split('\n') if skill.strip()]
    elif isinstance(skills, list):
        # If it's already a list, clean it up
        flattened_skills = []
        for skill in skills:
            if isinstance(skill, str):
                flattened_skills.append(skill.strip())
            elif isinstance(skill, dict):
                # Sometimes skills come as objects with name/level/years_of_experience
                skill_name = skill.get('name') or skill.get('skill') or skill.get('technology') or str(skill)
                flattened_skills.append(skill_name)
            else:
                flattened_skills.append(str(skill))
        return [skill for skill in flattened_skills if skill and skill != 'None']
    
    return []

def extract_projects(data) -> list:
    """Extract projects from VLM response"""
    projects = data.get("projects") or data.get("portfolio") or []
    
    if not isinstance(projects, list):
        return []
    
    formatted_projects = []
    for proj in projects:
        if isinstance(proj, dict):
            # Extract technologies list
            tech_list = proj.get("technologies") or proj.get("tech_stack") or proj.get("tools") or []
            if isinstance(tech_list, str):
                tech_list = [t.strip() for t in tech_list.split(',') if t.strip()]
            
            formatted_projects.append({
                "name": proj.get("name") or proj.get("title") or proj.get("project_name") or "",
                "description": proj.get("description") or proj.get("summary") or proj.get("details") or "",
                "technologies": tech_list,
                "url": proj.get("url") or proj.get("link") or proj.get("github") or proj.get("github_url") or ""
            })
    
    return formatted_projects

def extract_certifications(data) -> list:
    """Extract certifications from VLM response"""
    certs = data.get("certifications") or data.get("certificates") or []
    
    if not isinstance(certs, list):
        return []
    
    formatted_certs = []
    for cert in certs:
        if isinstance(cert, dict):
            formatted_certs.append({
                "name": cert.get("name") or cert.get("title") or cert.get("certification") or "",
                "issuer": cert.get("issuer") or cert.get("organization") or cert.get("provider") or "",
                "date": cert.get("date") or cert.get("year") or cert.get("issued_date") or ""
            })
        elif isinstance(cert, str):
            formatted_certs.append({
                "name": cert,
                "issuer": "",
                "date": ""
            })
    
    return formatted_certs

def extract_languages(data) -> list:
    """Extract languages from VLM response"""
    languages = data.get("languages") or []
    
    if not isinstance(languages, list):
        return []
    
    formatted_langs = []
    for lang in languages:
        if isinstance(lang, dict):
            formatted_langs.append({
                "language": lang.get("language") or lang.get("name") or "",
                "proficiency": lang.get("proficiency") or lang.get("level") or lang.get("fluency") or ""
            })
        elif isinstance(lang, str):
            formatted_langs.append({
                "language": lang,
                "proficiency": "Not specified"
            })
    
    return formatted_langs

def get_mock_resume_data() -> Dict[str, Any]:
    """Mock resume data for testing"""
    return {
        "personal_info": {
            "full_name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/sarahjohnson",
            "github": "github.com/sarahjohnson",
            "portfolio": "sarahjohnson.dev"
        },
        "experience": [
            {
                "company": "Tech Innovations Inc",
                "position": "Senior Software Engineer",
                "duration": "2022 - Present",
                "description": "Lead development of scalable web applications using React, Node.js, and AWS cloud services. Mentor junior developers and collaborate with cross-functional teams.",
                "achievements": [
                    "Improved application performance by 40% through code optimization",
                    "Led a team of 5 developers on a major product redesign",
                    "Implemented CI/CD pipeline reducing deployment time by 60%"
                ]
            },
            {
                "company": "StartupXYZ",
                "position": "Full Stack Developer",
                "duration": "2020 - 2022",
                "description": "Developed and maintained full-stack applications using Python/Django and React. Worked in fast-paced startup environment.",
                "achievements": [
                    "Built MVP from scratch serving 10,000+ users",
                    "Reduced API response time by 50%"
                ]
            }
        ],
        "education": [
            {
                "institution": "University of California, Berkeley",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "graduation_year": "2020",
                "gpa": "3.8"
            }
        ],
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "Django", "FastAPI", 
            "PostgreSQL", "MongoDB", "AWS", "Docker", "Git", "TypeScript",
            "REST APIs", "GraphQL", "Redis", "Kubernetes"
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect Associate",
                "issuer": "Amazon Web Services",
                "date": "2023"
            },
            {
                "name": "Certified Kubernetes Administrator",
                "issuer": "Cloud Native Computing Foundation",
                "date": "2022"
            }
        ],
        "projects": [
            {
                "name": "AI Resume Parser",
                "description": "Full-stack application that uses AI to parse resumes and provide career insights. Built with Next.js, FastAPI, and OpenAI API.",
                "technologies": ["Next.js", "TypeScript", "FastAPI", "Python", "OpenAI API", "PostgreSQL"],
                "url": "github.com/sarahjohnson/ai-resume-parser"
            },
            {
                "name": "E-commerce Platform",
                "description": "Scalable e-commerce solution with real-time inventory management and payment processing.",
                "technologies": ["React", "Node.js", "Express", "MongoDB", "Stripe API"],
                "url": "github.com/sarahjohnson/ecommerce-platform"
            }
        ],
        "languages": [
            {
                "language": "English",
                "proficiency": "Native"
            },
            {
                "language": "Spanish",
                "proficiency": "Conversational"
            },
            {
                "language": "French",
                "proficiency": "Basic"
            }
        ]
    }
