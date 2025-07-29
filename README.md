# AI Resume Parser & Chat Assistant

A modern web application that uses AI to parse resumes and provides an intelligent chat assistant for career guidance. Built with Next.js, FastAPI, and PostgreSQL.

## Features

- 📄 **Resume Parsing**: Upload PDF, DOC, or DOCX files and extract structured data using VLM.run
- 🤖 **AI Chat Assistant**: Get personalized career advice using OpenAI's GPT models
- 📊 **Resume Analysis**: Visual completion analysis and missing field detection
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 🔄 **Real-time Updates**: Polling-based status updates during parsing
- 💬 **Interactive Chat**: Suggested questions and conversation history

## Tech Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client
- **React Dropzone** - File upload

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **OpenAI API** - Chat functionality
- **VLM.run API** - Resume parsing
- **Uvicorn** - ASGI server

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- VLM.run API key (optional, fallback to mock data)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume-parser
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
createdb resume_parser
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resume_parser"

# Run the server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── vlm.py           # VLM.run integration
│   │   ├── openai_chat.py   # OpenAI chat functionality
│   │   ├── db.py            # Database configuration
│   │   ├── models.py        # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   │   └── index.tsx        # Main application page
│   ├── components/
│   │   ├── ResumeViewer.tsx # Resume display component
│   │   └── ChatAssistant.tsx # Chat interface
│   ├── styles/
│   │   └── globals.css
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── README.md
└── .env.example
```

## API Endpoints

### Resume Processing
- `POST /upload-resume` - Upload and start parsing
- `GET /parsing-status/{job_id}` - Check parsing status
- `GET /resume/{job_id}` - Get parsed resume data

### Chat Assistant
- `POST /chat` - Send message to AI assistant

## Async Flow

1. **Upload**: User uploads resume file
2. **Processing**: Backend receives file and starts VLM parsing in background
3. **Polling**: Frontend polls parsing status every 2 seconds
4. **Completion**: When parsing completes, resume data is displayed
5. **Chat**: User can chat with AI assistant about their resume

## Sample Prompts

Here are some example questions you can ask the AI assistant:

- "What are the strongest points of this resume?"
- "What skills should I add to be more competitive?"
- "How can I improve my experience section?"
- "What are some good interview questions I should prepare for?"
- "How does my background compare to industry standards?"
- "What certifications would benefit my career?"
- "What projects should I build to strengthen my portfolio?"

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for chat functionality | Yes |
| `VLM_API_KEY` | VLM.run API key for resume parsing | No* |
| `VLM_API_URL` | VLM.run API endpoint | No |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | Yes |

*If VLM_API_KEY is not provided, the system will use mock data for demonstration.

## Development

### Adding New Features

1. **Backend**: Add new endpoints in `app/main.py`
2. **Database**: Create new models in `app/models.py`
3. **Frontend**: Add new components in `components/`

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm run test
```

## Deployment

The application is containerized and ready for deployment on any platform that supports Docker:

- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

### Production Considerations

1. Use production-grade PostgreSQL instance
2. Set up proper logging and monitoring
3. Configure HTTPS/SSL
4. Set up CI/CD pipeline
5. Use secrets management for API keys

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For questions or issues, please open a GitHub issue or contact the development team.
