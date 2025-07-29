import React, { useState, useEffect } from 'react'
import { useChat } from 'ai/react'
import { Send, User, Bot, Lightbulb, History, Plus } from 'lucide-react'

interface ResumeData {
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

interface ChatSession {
  session_id: string
  resume_id: number
  created_at: string
  message_count: number
  last_message_time?: string
}

interface ChatAssistantProps {
  resume: ResumeData
}

const ChatAssistant: React.FC<ChatAssistantProps> = ({ resume }) => {
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [showSessionHistory, setShowSessionHistory] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)

  const { messages, input, handleInputChange, handleSubmit, isLoading, error, setMessages } = useChat({
    api: '/api/chat',
    body: {
      resumeData: resume,
      session_id: currentSessionId
    },
    initialMessages: [
      {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your AI career assistant. I've analyzed your resume for ${resume.personal_info?.full_name || 'you'} and I'm here to help you improve it and prepare for your job search. What would you like to know?`,
      }
    ],
    onError: (error) => {
      console.error('Chat error:', error)
    },
    onFinish: () => {
      // Refresh sessions after a chat is completed
      loadChatSessions()
    }
  })

  // Generate session ID on component mount
  useEffect(() => {
    if (!currentSessionId) {
      setCurrentSessionId(generateSessionId())
    }
    loadChatSessions()
  }, [])

  const generateSessionId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  const loadChatSessions = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8002/chat-sessions')
      if (response.ok) {
        const sessions = await response.json()
        setChatSessions(sessions)
      }
    } catch (error) {
      console.error('Failed to load chat sessions:', error)
    }
  }

  const loadChatHistory = async (sessionId: string) => {
    setLoadingHistory(true)
    try {
      const response = await fetch(`http://127.0.0.1:8002/chat-history/${sessionId}`)
      if (response.ok) {
        const history = await response.json()
        
        // Convert backend format to frontend format
        const formattedMessages = history.map((msg: any, index: number) => ({
          id: `${sessionId}-${index}`,
          role: msg.role,
          content: msg.content
        }))

        // Add welcome message at the beginning if not present
        const hasWelcome = formattedMessages.some((msg: any) => msg.role === 'assistant' && msg.content.includes("Hello! I'm your AI career assistant"))
        if (!hasWelcome && formattedMessages.length > 0) {
          formattedMessages.unshift({
            id: 'welcome',
            role: 'assistant',
            content: `Hello! I'm your AI career assistant. I've analyzed your resume for ${resume.personal_info?.full_name || 'you'} and I'm here to help you improve it and prepare for your job search. What would you like to know?`,
          })
        }

        setMessages(formattedMessages)
        setCurrentSessionId(sessionId)
        setShowSessionHistory(false)
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  const startNewSession = () => {
    const newSessionId = generateSessionId()
    setCurrentSessionId(newSessionId)
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm your AI career assistant. I've analyzed your resume for ${resume.personal_info?.full_name || 'you'} and I'm here to help you improve it and prepare for your job search. What would you like to know?`,
    }])
    setShowSessionHistory(false)
    loadChatSessions() // Refresh sessions list
  }

  const suggestedQuestions = [
    "What are the strongest points of this resume?",
    "What skills should I add to be more competitive?",
    "How can I improve my experience section?",
    "What are some good interview questions I should prepare for?",
    "How does my background compare to industry standards?",
    "What certifications would benefit my career?"
  ]

  const handleSuggestedQuestion = (question: string) => {
    const event = {
      target: { value: question }
    } as React.ChangeEvent<HTMLInputElement>
    handleInputChange(event)
    
    const submitEvent = {
      preventDefault: () => {}
    } as React.FormEvent<HTMLFormElement>
    handleSubmit(submitEvent)
  }

  const renderMessage = (content: string) => {
    // Convert markdown-like formatting to JSX
    const lines = content.split('\n')
    const elements: JSX.Element[] = []
    
    lines.forEach((line, index) => {
      if (line.trim() === '') {
        elements.push(<br key={index} />)
      } else if (line.startsWith('• ')) {
        elements.push(
          <div key={index} className="flex items-start mb-1">
            <span className="text-blue-500 mr-2">•</span>
            <span dangerouslySetInnerHTML={{ __html: line.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
          </div>
        )
      } else if (line.startsWith('**') && line.endsWith('**')) {
        elements.push(
          <h4 key={index} className="font-semibold text-gray-800 mt-3 mb-2">
            {line.replace(/\*\*/g, '')}
          </h4>
        )
      } else {
        elements.push(
          <p key={index} className="mb-2" dangerouslySetInnerHTML={{ 
            __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
          }} />
        )
      }
    })
    
    return <div>{elements}</div>
  }

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md flex flex-col h-[700px]">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              <Bot className="w-6 h-6 text-primary-500 mr-2" />
              AI Resume Assistant
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {messages.length > 10 ? 'Session limit reached (10 messages)' : `${messages.length}/10 messages`}
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowSessionHistory(!showSessionHistory)}
              className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center text-sm text-gray-600 transition-colors"
            >
              <History className="w-4 h-4 mr-1" />
              History
            </button>
            <button
              onClick={startNewSession}
              className="px-3 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center text-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1" />
              New Chat
            </button>
          </div>
        </div>
      </div>

      {/* Session History Sidebar */}
      {showSessionHistory && (
        <div className="border-b border-gray-200 p-4 bg-gray-50 max-h-48 overflow-y-auto">
          <h3 className="font-medium text-gray-900 mb-3">Previous Sessions</h3>
          {loadingHistory && <p className="text-gray-500 text-sm">Loading sessions...</p>}
          {chatSessions.length === 0 && !loadingHistory && (
            <p className="text-gray-500 text-sm">No previous sessions found</p>
          )}
          <div className="space-y-2">
            {chatSessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => loadChatHistory(session.session_id)}
                className="w-full text-left p-3 bg-white hover:bg-gray-100 rounded-lg border text-sm transition-colors"
                disabled={loadingHistory}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">
                      Session {session.session_id.slice(-8)}
                    </p>
                    <p className="text-gray-500 text-xs">
                      {session.message_count} messages
                    </p>
                  </div>
                  <p className="text-gray-400 text-xs">
                    {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                message.role === 'user' ? 'bg-primary-500 ml-2' : 'bg-gray-300 mr-2'
              }`}>
                {message.role === 'user' ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-gray-600" />
                )}
              </div>
              <div className={`px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}>
                <div className={`text-sm ${
                  message.role === 'user' ? 'text-primary-100' : 'text-gray-500'
                } mb-1`}>
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </div>
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  renderMessage(message.content)
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex max-w-[80%]">
              <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-300 mr-2">
                <Bot className="w-4 h-4 text-gray-600" />
              </div>
              <div className="px-4 py-2 rounded-lg bg-gray-100">
                <div className="text-sm text-gray-500 mb-1">AI Assistant</div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center mb-3">
            <Lightbulb className="w-4 h-4 text-yellow-500 mr-2" />
            <span className="text-sm font-medium text-gray-700">Suggested questions:</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition-colors"
                disabled={isLoading || messages.length >= 10}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="border-t border-red-200 p-4 bg-red-50">
          <p className="text-red-600 text-sm">
            Error: {error.message}. Trying to provide helpful guidance based on your resume data.
          </p>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={handleInputChange}
            placeholder={messages.length >= 10 ? "Session limit reached" : "Ask me anything about your resume..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isLoading || messages.length >= 10}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || messages.length >= 10}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatAssistant
