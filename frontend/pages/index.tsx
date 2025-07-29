import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { Upload, FileText, CheckCircle, AlertCircle, MessageCircle } from 'lucide-react'
import ResumeViewer from '@/components/ResumeViewer'
import ChatAssistant from '@/components/ChatAssistant'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

interface ParsedResume {
  personal_info: {
    full_name: string
    email: string
    phone: string
    location: string
    linkedin?: string
    github?: string
    portfolio?: string
  }
  experience: Array<{
    company: string
    position: string
    duration: string
    description: string
    achievements: string[]
  }>
  education: Array<{
    institution: string
    degree: string
    field: string
    graduation_year: string
    gpa?: string
  }>
  skills: string[]
  certifications: Array<{
    name: string
    issuer: string
    date: string
  }>
  projects: Array<{
    name: string
    description: string
    technologies: string[]
    url?: string
  }>
  languages: Array<{
    language: string
    proficiency: string
  }>
}

interface ParsingStatus {
  status: 'processing' | 'completed' | 'error'
  progress: number
  error?: string
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [parsingStatus, setParsingStatus] = useState<ParsingStatus | null>(null)
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)
  const [activeTab, setActiveTab] = useState<'upload' | 'resume' | 'chat'>('upload')

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    setFile(file)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: false
  })

  const uploadResume = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const { job_id } = response.data
      setJobId(job_id)
      setParsingStatus({ status: 'processing', progress: 0 })

      // Start polling for status
      pollParsingStatus(job_id)
    } catch (error) {
      console.error('Upload failed:', error)
      setParsingStatus({ status: 'error', progress: 0, error: 'Upload failed' })
    }
  }

  const pollParsingStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/parsing-status/${jobId}`)
        const status = response.data

        setParsingStatus(status)

        if (status.status === 'completed') {
          clearInterval(interval)
          // Fetch the parsed resume data
          const resumeResponse = await axios.get(`${API_BASE_URL}/resume/${jobId}`)
          setParsedResume(resumeResponse.data)
          setActiveTab('resume')
        } else if (status.status === 'error') {
          clearInterval(interval)
        }
      } catch (error) {
        console.error('Error polling status:', error)
        clearInterval(interval)
        setParsingStatus({ status: 'error', progress: 0, error: 'Failed to check status' })
      }
    }, 2000)
  }

  const resetUpload = () => {
    setFile(null)
    setJobId(null)
    setParsingStatus(null)
    setParsedResume(null)
    setActiveTab('upload')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Resume Parser & Chat Assistant
          </h1>
          <p className="text-gray-600">
            Upload your resume to get AI-powered insights and career guidance
          </p>
        </header>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="flex space-x-1 bg-white rounded-lg p-1 shadow-sm">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'bg-primary-500 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload
            </button>
            <button
              onClick={() => setActiveTab('resume')}
              disabled={!parsedResume}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                !parsedResume
                  ? 'text-gray-400 cursor-not-allowed'
                  : activeTab === 'resume'
                  ? 'bg-primary-500 text-white'
                  : 'text-gray-600 hover:text-gray-800 cursor-pointer'
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Resume
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              disabled={!parsedResume}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                !parsedResume
                  ? 'text-gray-400 cursor-not-allowed'
                  : activeTab === 'chat'
                  ? 'bg-primary-500 text-white'
                  : 'text-gray-600 hover:text-gray-800 cursor-pointer'
              }`}
            >
              <MessageCircle className="w-4 h-4 inline mr-2" />
              Chat
            </button>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'upload' && (
          <div className="max-w-2xl mx-auto">
            {!file && !parsingStatus && (
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
                  isDragActive
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-300 hover:border-primary-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Upload Your Resume
                </h3>
                <p className="text-gray-500 mb-4">
                  Drag and drop your resume here, or click to browse
                </p>
                <p className="text-sm text-gray-400">
                  Supports PDF, DOC, and DOCX files
                </p>
              </div>
            )}

            {file && !parsingStatus && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <FileText className="w-8 h-8 text-primary-500 mr-3" />
                    <div>
                      <h3 className="font-semibold text-gray-900">{file.name}</h3>
                      <p className="text-sm text-gray-500">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={resetUpload}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
                <button
                  onClick={uploadResume}
                  className="w-full bg-primary-500 text-white py-3 rounded-lg font-semibold hover:bg-primary-600 transition-colors"
                >
                  Parse Resume with AI
                </button>
              </div>
            )}

            {parsingStatus && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  {parsingStatus.status === 'processing' && (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mr-3"></div>
                  )}
                  {parsingStatus.status === 'completed' && (
                    <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
                  )}
                  {parsingStatus.status === 'error' && (
                    <AlertCircle className="w-6 h-6 text-red-500 mr-3" />
                  )}
                  <h3 className="font-semibold text-gray-900">
                    {parsingStatus.status === 'processing' && 'Parsing Resume...'}
                    {parsingStatus.status === 'completed' && 'Resume Parsed Successfully!'}
                    {parsingStatus.status === 'error' && 'Parsing Failed'}
                  </h3>
                </div>

                {parsingStatus.status === 'processing' && (
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                    <div
                      className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${parsingStatus.progress}%` }}
                    ></div>
                  </div>
                )}

                {parsingStatus.status === 'error' && (
                  <div className="text-red-600 mb-4">{parsingStatus.error}</div>
                )}

                {parsingStatus.status === 'completed' && (
                  <p className="text-green-600 mb-4">
                    Your resume has been successfully parsed! Click on the Resume tab to view the results.
                  </p>
                )}

                <button
                  onClick={resetUpload}
                  className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Upload Another Resume
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'resume' && parsedResume && jobId && (
          <ResumeViewer resume={parsedResume} jobId={jobId} />
        )}

        {activeTab === 'chat' && parsedResume && (
          <ChatAssistant resume={parsedResume} />
        )}
      </div>
    </div>
  )
}
