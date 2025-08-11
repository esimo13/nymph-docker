from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import sys
import uuid
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
# Database imports
from db import get_db, engine
from models import Base, Resume, ChatSession, ChatMessage
from vlm import parse_resume_with_vlm
from openai_chat import get_chat_response
from job_analysis import process_job_description, analyze_skill_match
from schemas import ChatRequest, ResumeResponse

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Parser API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3001",
        "https://nymph-frontend.onrender.com",  # Production frontend
        "https://*.onrender.com"  # Allow any Render subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for tracking parsing status (temporary until processing completes)
parsing_status = {}

@app.get("/")
async def root():
    return {"message": "Resume Parser API is running"}

@app.post("/upload-resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and parse resume using VLM"""
    
    print(f"=== UPLOAD RECEIVED ===")
    print(f"Filename: {file.filename}")
    print(f"Content type: {file.content_type}")
    print(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        print(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail="Only PDF, DOC, and DOCX files are supported"
        )
    
    # Generate unique job ID (will become resume ID later)
    job_id = str(uuid.uuid4())
    parsing_status[job_id] = {"status": "processing", "progress": 0}
    
    print(f"Generated job ID: {job_id}")
    
    # Read file content
    file_content = await file.read()
    print(f"File content size: {len(file_content)} bytes")
    
    # Start background parsing task
    background_tasks.add_task(
        process_resume, 
        job_id, 
        file_content, 
        file.filename
    )
    
    print(f"Background task started for job: {job_id}")
    return {"job_id": job_id, "status": "processing"}

@app.get("/parsing-status/{job_id}")
async def get_parsing_status(job_id: str, db: Session = Depends(get_db)):
    """Check the status of resume parsing"""
    
    # First check in-memory status for active processing
    if job_id in parsing_status:
        return parsing_status[job_id]
    
    # If not in memory, check if it's completed in database
    resume = db.query(Resume).filter(Resume.user_session == job_id).first()
    if resume:
        return {"status": "completed", "progress": 100, "resume_id": resume.id}
    
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/resume/{job_id}")
async def get_resume(job_id: str, db: Session = Depends(get_db)):
    """Get parsed resume data"""
    
    # Check if job is still processing
    if job_id in parsing_status:
        status_info = parsing_status[job_id]
        if status_info["status"] != "completed":
            raise HTTPException(status_code=400, detail="Resume parsing not completed")
        # If completed in memory, return the result
        return status_info.get("result", {})
    
    # Otherwise, fetch from database
    resume = db.query(Resume).filter(Resume.user_session == job_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return resume.parsed_data

@app.post("/chat")
async def chat_with_resume(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat about the resume using OpenAI with persistence"""
    try:
        # Get or create chat session
        session_id = getattr(request, 'session_id', None) or str(uuid.uuid4())
        
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not chat_session:
            # Create new chat session
            resume_id = None
            if hasattr(request, 'resume_id') and request.resume_id:
                resume_id = request.resume_id
            
            chat_session = ChatSession(
                session_id=session_id,
                resume_id=resume_id
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        # Get current message order
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.message_order.desc()).first()
        next_order = (last_message.message_order + 1) if last_message else 1
        
        # Store user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message,
            message_order=next_order
        )
        db.add(user_message)
        
        # Get chat history for context
        chat_history = []
        if hasattr(request, 'chat_history') and request.chat_history:
            chat_history = request.chat_history
        else:
            # Load from database
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.message_order < next_order
            ).order_by(ChatMessage.message_order).all()
            
            chat_history = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Get AI response
        response = await get_chat_response(
            request.message,
            request.resume_data,
            chat_history
        )
        
        # Store assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant", 
            content=response,
            message_order=next_order + 1
        )
        db.add(assistant_message)
        db.commit()
        
        return {
            "response": response, 
            "session_id": session_id,
            "message_count": next_order + 1
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.message_order).all()
    
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "order": msg.message_order
        }
        for msg in messages
    ]

@app.get("/chat-sessions")
async def get_chat_sessions(db: Session = Depends(get_db)):
    """Get all chat sessions with basic info"""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    
    result = []
    for session in sessions:
        # Get message count
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.session_id
        ).count()
        
        # Get last message
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.session_id
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        result.append({
            "session_id": session.session_id,
            "resume_id": session.resume_id,
            "created_at": session.created_at.isoformat(),
            "message_count": message_count,
            "last_message_time": last_message.timestamp.isoformat() if last_message else None
        })
    
    return result

async def process_resume(job_id: str, file_content: bytes, filename: str):
    """Background task to process resume and save to database"""
    from db import SessionLocal  # Import here to avoid dependency issues
    
    db = SessionLocal()
    try:
        print(f"=== PROCESSING RESUME ===")
        print(f"Job ID: {job_id}")
        print(f"Filename: {filename}")
        print(f"File size: {len(file_content)} bytes")
        
        # Update status
        parsing_status[job_id]["progress"] = 25
        
        print("Calling VLM.run parse function...")
        # Parse with VLM
        parsed_data = await parse_resume_with_vlm(file_content, filename)
        
        print(f"VLM parsing completed. Data type: {type(parsed_data)}")
        print(f"Parsed data keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dict'}")
        
        parsing_status[job_id]["progress"] = 75
        
        # Save to database
        try:
            resume = Resume(
                filename=filename,
                parsed_data=parsed_data,
                user_session=job_id,  # Use job_id as session identifier
                upload_timestamp=datetime.utcnow()
            )
            
            db.add(resume)
            db.commit()
            db.refresh(resume)
            
            print(f"Resume saved to database with ID: {resume.id}")
            
            # Update final status
            parsing_status[job_id] = {
                "status": "completed",
                "progress": 100,
                "result": parsed_data,
                "resume_id": resume.id
            }
            
            print(f"Job {job_id} completed successfully")
            
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            db.rollback()
            
            # Still mark as completed but log the DB error
            parsing_status[job_id] = {
                "status": "completed",
                "progress": 100,
                "result": parsed_data,
                "db_error": str(db_error)
            }
        
    except Exception as e:
        print(f"Processing error: {str(e)}")
        parsing_status[job_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }
        db.rollback()
    
    finally:
        db.close()

# Global storage for job analysis results
job_analysis_results = {}

@app.post("/upload-job-description")
async def upload_job_description(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and parse job description PDF using OpenAI"""
    
    print("=== JOB DESCRIPTION UPLOAD RECEIVED ===")
    print(f"Filename: {file.filename}")
    print(f"Content type: {file.content_type}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported for job descriptions"
        )
    
    # Generate job analysis ID
    analysis_id = str(uuid.uuid4())
    job_analysis_results[analysis_id] = {"status": "processing", "progress": 0}
    
    print(f"Generated analysis ID: {analysis_id}")
    
    # Read file content
    file_content = await file.read()
    print(f"File content size: {len(file_content)} bytes")
    
    # Start background processing task
    background_tasks.add_task(
        process_job_description_task,
        analysis_id,
        file_content,
        file.filename
    )
    
    print(f"Background task started for job analysis: {analysis_id}")
    return {"analysis_id": analysis_id, "status": "processing"}

@app.get("/job-analysis-status/{analysis_id}")
async def get_job_analysis_status(analysis_id: str):
    """Check the status of job description analysis"""
    
    if analysis_id in job_analysis_results:
        return job_analysis_results[analysis_id]
    
    return {"status": "not_found", "error": "Analysis ID not found"}

@app.post("/analyze-skills/{resume_job_id}/{analysis_id}")
async def analyze_skills_match(
    resume_job_id: str,
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Analyze skill match between resume and job description"""
    
    print(f"=== ANALYZING SKILLS MATCH ===")
    print(f"Resume Job ID: {resume_job_id}")
    print(f"Analysis ID: {analysis_id}")
    
    # Get resume data
    resume = db.query(Resume).filter(Resume.user_session == resume_job_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get job analysis data
    if analysis_id not in job_analysis_results:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    
    job_analysis = job_analysis_results[analysis_id]
    if job_analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job analysis not completed yet")
    
    # Extract skills from resume
    resume_data = resume.parsed_data if isinstance(resume.parsed_data, dict) else json.loads(resume.parsed_data)
    resume_skills = []
    
    if "skills" in resume_data:
        if isinstance(resume_data["skills"], list):
            resume_skills = resume_data["skills"]
        elif isinstance(resume_data["skills"], dict):
            # Handle different skill structures
            for category, skills in resume_data["skills"].items():
                if isinstance(skills, list):
                    resume_skills.extend(skills)
                elif isinstance(skills, str):
                    resume_skills.append(skills)
    
    # Get job requirements
    job_data = job_analysis["result"]["job_data"]
    job_required_skills = job_data.get("required_skills", [])
    job_preferred_skills = job_data.get("preferred_skills", [])
    
    # Perform skill matching analysis
    match_analysis = analyze_skill_match(
        resume_skills,
        job_required_skills,
        job_preferred_skills
    )
    
    # Combine results
    result = {
        "resume_info": {
            "job_id": resume_job_id,
            "filename": resume.filename,
            "skills": resume_skills
        },
        "job_info": {
            "analysis_id": analysis_id,
            "job_title": job_data.get("job_title", ""),
            "company": job_data.get("company", ""),
            "required_skills": job_required_skills,
            "preferred_skills": job_preferred_skills
        },
        "match_analysis": match_analysis,
        "recommendations": generate_recommendations(match_analysis)
    }
    
    print(f"Skills match analysis completed. Overall match: {match_analysis['overall_match_percentage']}%")
    
    return result

@app.get("/job-description/{analysis_id}")
async def get_job_description(analysis_id: str):
    """Get parsed job description data"""
    
    if analysis_id not in job_analysis_results:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    
    job_analysis = job_analysis_results[analysis_id]
    if job_analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job analysis not completed yet")
    
    return job_analysis["result"]

def generate_recommendations(match_analysis: dict) -> dict:
    """Generate recommendations based on skill match analysis"""
    
    overall_match = match_analysis["overall_match_percentage"]
    missing_required = match_analysis["required_skills"]["missing"]
    missing_preferred = match_analysis["preferred_skills"]["missing"]
    
    recommendations = {
        "overall_assessment": "",
        "priority_skills": [],
        "nice_to_have_skills": [],
        "action_items": []
    }
    
    # Overall assessment
    if overall_match >= 80:
        recommendations["overall_assessment"] = "Excellent match! You have most of the required skills for this position."
    elif overall_match >= 60:
        recommendations["overall_assessment"] = "Good match! You meet many requirements but could strengthen a few areas."
    elif overall_match >= 40:
        recommendations["overall_assessment"] = "Fair match. Consider developing additional skills before applying."
    else:
        recommendations["overall_assessment"] = "Limited match. Significant skill development needed for this role."
    
    # Priority skills (missing required)
    recommendations["priority_skills"] = missing_required[:5]  # Top 5
    
    # Nice to have skills (missing preferred)
    recommendations["nice_to_have_skills"] = missing_preferred[:5]  # Top 5
    
    # Action items
    if missing_required:
        recommendations["action_items"].append(f"Focus on learning {len(missing_required)} missing required skills")
    
    if missing_preferred:
        recommendations["action_items"].append(f"Consider learning {len(missing_preferred)} preferred skills to stand out")
    
    if overall_match >= 70:
        recommendations["action_items"].append("You're a strong candidate - consider applying!")
    
    return recommendations

async def process_job_description_task(analysis_id: str, file_content: bytes, filename: str):
    """Background task to process job description"""
    
    try:
        job_analysis_results[analysis_id] = {"status": "processing", "progress": 25}
        
        # Process the job description
        result = await process_job_description(file_content, filename)
        
        if result["success"]:
            job_analysis_results[analysis_id] = {
                "status": "completed",
                "progress": 100,
                "result": result
            }
            print(f"Job description analysis completed for: {analysis_id}")
        else:
            job_analysis_results[analysis_id] = {
                "status": "error",
                "progress": 0,
                "error": result.get("error", "Unknown error")
            }
            print(f"Job description analysis failed for: {analysis_id}")
    
    except Exception as e:
        print(f"Job description processing error: {str(e)}")
        job_analysis_results[analysis_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
