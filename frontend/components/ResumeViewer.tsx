import React, { useState } from 'react'
import { Mail, Phone, MapPin, Github, Linkedin, Globe, CheckCircle, XCircle, Upload, FileText } from 'lucide-react'

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

interface SkillMatch {
  resume_skill: string
  job_skill: string
  match_type: 'exact' | 'partial'
}

interface SkillsMatchData {
  resume_info: {
    job_id: string
    filename: string
    skills: string[]
  }
  job_info: {
    analysis_id: string
    job_title: string
    company: string
    required_skills: string[]
    preferred_skills: string[]
  }
  match_analysis: {
    overall_match_percentage: number
    required_skills: {
      total: number
      matched: number
      match_percentage: number
      exact_matches: SkillMatch[]
      partial_matches: SkillMatch[]
      missing: string[]
    }
    preferred_skills: {
      total: number
      matched: number
      match_percentage: number
      exact_matches: SkillMatch[]
      partial_matches: SkillMatch[]
      missing: string[]
    }
    resume_skills: string[]
    analysis_summary: {
      strong_match: boolean
      good_match: boolean
      fair_match: boolean
      weak_match: boolean
    }
  }
  recommendations: {
    overall_assessment: string
    priority_skills: string[]
    nice_to_have_skills: string[]
    action_items: string[]
  }
}

interface ResumeViewerProps {
  resume: ResumeData
  jobId: string
}

const ResumeViewer: React.FC<ResumeViewerProps> = ({ resume, jobId }) => {
  const [isUploadingJD, setIsUploadingJD] = useState(false)
  const [showSkillsMatch, setShowSkillsMatch] = useState(false)
  const [skillsMatchData, setSkillsMatchData] = useState<SkillsMatchData | null>(null)

  // Get API URL from environment, fallback to localhost for development
  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'
  }

  const handleJobDescriptionUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }

    setIsUploadingJD(true)
    
    try {
      // Upload job description
      const formData = new FormData()
      formData.append('file', file)
      
      const uploadResponse = await fetch(`${getApiUrl()}/upload-job-description`, {
        method: 'POST',
        body: formData
      })
      
      if (!uploadResponse.ok) {
        throw new Error('Failed to upload job description')
      }
      
      const { analysis_id } = await uploadResponse.json()
      
      // Poll for completion
      let completed = false
      while (!completed) {
        await new Promise(resolve => setTimeout(resolve, 2000)) // Wait 2 seconds
        
        const statusResponse = await fetch(`${getApiUrl()}/job-analysis-status/${analysis_id}`)
        const status = await statusResponse.json()
        
        if (status.status === 'completed') {
          completed = true
          
          // Analyze skills match
          const matchResponse = await fetch(`${getApiUrl()}/analyze-skills/${jobId}/${analysis_id}`, {
            method: 'POST'
          })
          
          if (matchResponse.ok) {
            const matchData = await matchResponse.json()
            setSkillsMatchData(matchData)
            setShowSkillsMatch(true)
          }
        } else if (status.status === 'error') {
          throw new Error(status.error || 'Job description analysis failed')
        }
      }
      
    } catch (error) {
      console.error('Error processing job description:', error)
      alert('Error processing job description. Please try again.')
    } finally {
      setIsUploadingJD(false)
      // Reset file input
      event.target.value = ''
    }
  }
  const getCompletionStatus = () => {
    const sections = {
      'Personal Information': !!resume.personal_info?.full_name && !!resume.personal_info?.email,
      'Experience': resume.experience?.length > 0,
      'Education': resume.education?.length > 0,
      'Skills': resume.skills?.length > 0,
      'Projects': resume.projects?.length > 0,
      'Certifications': resume.certifications?.length > 0,
      'Languages': resume.languages?.length > 0
    }

    const completed = Object.values(sections).filter(Boolean).length
    const total = Object.keys(sections).length
    const percentage = Math.round((completed / total) * 100)

    return { sections, completed, total, percentage }
  }

  const { sections, completed, total, percentage } = getCompletionStatus()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Completion Overview */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Resume Analysis</h2>
        <div className="flex items-center justify-between mb-4">
          <span className="text-lg font-medium text-gray-700">
            Completion: {completed}/{total} sections
          </span>
          <span className="text-2xl font-bold text-primary-600">{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            className="bg-primary-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(sections).map(([section, completed]) => (
            <div key={section} className="flex items-center space-x-2">
              {completed ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <span className={`text-sm ${completed ? 'text-green-700' : 'text-red-700'}`}>
                {section}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Personal Information */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Personal Information</h3>
        <div className="space-y-3">
          <h4 className="text-2xl font-semibold text-gray-800">
            {resume.personal_info?.full_name || 'Name not found'}
          </h4>
          <div className="flex flex-wrap gap-4 text-gray-600">
            {resume.personal_info?.email && (
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4" />
                <span>{resume.personal_info.email}</span>
              </div>
            )}
            {resume.personal_info?.phone && (
              <div className="flex items-center space-x-2">
                <Phone className="w-4 h-4" />
                <span>{resume.personal_info.phone}</span>
              </div>
            )}
            {resume.personal_info?.location && (
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4" />
                <span>{resume.personal_info.location}</span>
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-4">
            {resume.personal_info?.linkedin && (
              <a
                href={resume.personal_info.linkedin.startsWith('http') 
                  ? resume.personal_info.linkedin 
                  : `https://${resume.personal_info.linkedin}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
              >
                <Linkedin className="w-4 h-4" />
                <span>LinkedIn</span>
              </a>
            )}
            {resume.personal_info?.github && (
              <a
                href={resume.personal_info.github.startsWith('http') 
                  ? resume.personal_info.github 
                  : `https://${resume.personal_info.github}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-800"
              >
                <Github className="w-4 h-4" />
                <span>GitHub</span>
              </a>
            )}
            {resume.personal_info?.portfolio && (
              <a
                href={resume.personal_info.portfolio.startsWith('http') 
                  ? resume.personal_info.portfolio 
                  : `https://${resume.personal_info.portfolio}`
                }
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-primary-600 hover:text-primary-800"
              >
                <Globe className="w-4 h-4" />
                <span>Portfolio</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Experience */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Experience</h3>
        {resume.experience?.length > 0 ? (
          <div className="space-y-6">
            {resume.experience.map((exp, index) => (
              <div key={index} className="border-l-4 border-primary-500 pl-4">
                <h4 className="text-lg font-semibold text-gray-800">{exp.position}</h4>
                <p className="text-primary-600 font-medium">{exp.company}</p>
                <p className="text-gray-500 text-sm mb-2">{exp.duration}</p>
                <p className="text-gray-700 mb-3">{exp.description}</p>
                {exp.achievements?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">Key Achievements:</h5>
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      {exp.achievements.map((achievement, achieveIndex) => (
                        <li key={achieveIndex}>{achievement}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 italic">No experience information found</p>
        )}
      </div>

      {/* Education */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Education</h3>
        {resume.education?.length > 0 ? (
          <div className="space-y-4">
            {resume.education.map((edu, index) => (
              <div key={index} className="border-l-4 border-green-500 pl-4">
                <h4 className="text-lg font-semibold text-gray-800">
                  {edu.degree} in {edu.field}
                </h4>
                <p className="text-green-600 font-medium">{edu.institution}</p>
                <div className="flex gap-4 text-gray-500 text-sm">
                  <span>Class of {edu.graduation_year}</span>
                  {edu.gpa && <span>GPA: {edu.gpa}</span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 italic">No education information found</p>
        )}
      </div>

      {/* Skills */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900">Skills</h3>
          {!showSkillsMatch && (
            <div className="relative">
              <input
                type="file"
                accept=".pdf"
                onChange={handleJobDescriptionUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={isUploadingJD}
              />
              <button
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                disabled={isUploadingJD}
              >
                {isUploadingJD ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Compare with Job
                  </>
                )}
              </button>
            </div>
          )}
        </div>
        
        {resume.skills?.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {resume.skills.map((skill, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium"
              >
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 italic">No skills information found</p>
        )}
        
        {showSkillsMatch && skillsMatchData && (
          <div className="mt-6 border-t pt-6">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-800">Job Match Analysis</h4>
              <button
                onClick={() => setShowSkillsMatch(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                Hide Analysis
              </button>
            </div>
            
            {/* Overall Match Score */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Overall Match</span>
                <span className={`text-2xl font-bold ${
                  skillsMatchData.match_analysis.overall_match_percentage >= 80 ? 'text-green-600' :
                  skillsMatchData.match_analysis.overall_match_percentage >= 60 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {skillsMatchData.match_analysis.overall_match_percentage}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className={`h-2 rounded-full ${
                    skillsMatchData.match_analysis.overall_match_percentage >= 80 ? 'bg-green-600' :
                    skillsMatchData.match_analysis.overall_match_percentage >= 60 ? 'bg-yellow-600' :
                    'bg-red-600'
                  }`}
                  style={{ width: `${skillsMatchData.match_analysis.overall_match_percentage}%` }}
                ></div>
              </div>
            </div>
            
            {/* Job Info */}
            <div className="bg-blue-50 rounded-lg p-4 mb-4">
              <h5 className="font-semibold text-blue-800 mb-2">
                {skillsMatchData.job_info.job_title} 
                {skillsMatchData.job_info.company && ` at ${skillsMatchData.job_info.company}`}
              </h5>
            </div>
            
            {/* Required Skills Match */}
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div className="bg-white border rounded-lg p-4">
                <h5 className="font-semibold text-gray-800 mb-2">
                  Required Skills ({skillsMatchData.match_analysis.required_skills.matched}/{skillsMatchData.match_analysis.required_skills.total})
                </h5>
                
                {/* Matched Skills */}
                {[...skillsMatchData.match_analysis.required_skills.exact_matches, ...skillsMatchData.match_analysis.required_skills.partial_matches].length > 0 && (
                  <div className="mb-3">
                    <p className="text-sm text-green-600 font-medium mb-1">✓ Matched</p>
                    <div className="flex flex-wrap gap-1">
                      {[...skillsMatchData.match_analysis.required_skills.exact_matches, ...skillsMatchData.match_analysis.required_skills.partial_matches].map((match, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs"
                        >
                          {match.job_skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Missing Skills */}
                {skillsMatchData.match_analysis.required_skills.missing.length > 0 && (
                  <div>
                    <p className="text-sm text-red-600 font-medium mb-1">✗ Missing</p>
                    <div className="flex flex-wrap gap-1">
                      {skillsMatchData.match_analysis.required_skills.missing.map((skill, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Preferred Skills Match */}
              <div className="bg-white border rounded-lg p-4">
                <h5 className="font-semibold text-gray-800 mb-2">
                  Preferred Skills ({skillsMatchData.match_analysis.preferred_skills.matched}/{skillsMatchData.match_analysis.preferred_skills.total})
                </h5>
                
                {/* Matched Skills */}
                {[...skillsMatchData.match_analysis.preferred_skills.exact_matches, ...skillsMatchData.match_analysis.preferred_skills.partial_matches].length > 0 && (
                  <div className="mb-3">
                    <p className="text-sm text-blue-600 font-medium mb-1">✓ Matched</p>
                    <div className="flex flex-wrap gap-1">
                      {[...skillsMatchData.match_analysis.preferred_skills.exact_matches, ...skillsMatchData.match_analysis.preferred_skills.partial_matches].map((match, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                        >
                          {match.job_skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Missing Skills */}
                {skillsMatchData.match_analysis.preferred_skills.missing.length > 0 && (
                  <div>
                    <p className="text-sm text-orange-600 font-medium mb-1">⚠ Missing</p>
                    <div className="flex flex-wrap gap-1">
                      {skillsMatchData.match_analysis.preferred_skills.missing.map((skill, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Recommendations */}
            {skillsMatchData.recommendations && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h5 className="font-semibold text-gray-800 mb-2">Recommendations</h5>
                <p className="text-sm text-gray-700 mb-3">{skillsMatchData.recommendations.overall_assessment}</p>
                
                {skillsMatchData.recommendations.priority_skills.length > 0 && (
                  <div className="mb-2">
                    <p className="text-sm font-medium text-red-700">Priority Skills to Learn:</p>
                    <p className="text-sm text-gray-600">{skillsMatchData.recommendations.priority_skills.join(', ')}</p>
                  </div>
                )}
                
                {skillsMatchData.recommendations.action_items.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-blue-700">Action Items:</p>
                    <ul className="text-sm text-gray-600 list-disc list-inside">
                      {skillsMatchData.recommendations.action_items.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Projects */}
      {resume.projects?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Projects</h3>
          <div className="space-y-6">
            {resume.projects.map((project, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-lg font-semibold text-gray-800">{project.name}</h4>
                  {project.url && (
                    <a
                      href={project.url.startsWith('http') ? project.url : `https://${project.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-800 text-sm"
                    >
                      View Project →
                    </a>
                  )}
                </div>
                <p className="text-gray-700 mb-3">{project.description}</p>
                <div className="flex flex-wrap gap-2">
                  {project.technologies?.map((tech, techIndex) => (
                    <span
                      key={techIndex}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Certifications */}
      {resume.certifications?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Certifications</h3>
          <div className="space-y-3">
            {resume.certifications.map((cert, index) => (
              <div key={index} className="flex justify-between items-center border-b border-gray-100 pb-3">
                <div>
                  <h4 className="font-semibold text-gray-800">{cert.name}</h4>
                  <p className="text-gray-600">{cert.issuer}</p>
                </div>
                <span className="text-gray-500 text-sm">{cert.date}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Languages */}
      {resume.languages?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Languages</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {resume.languages.map((lang, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="font-medium text-gray-800">{lang.language}</span>
                <span className="text-gray-600 text-sm">{lang.proficiency}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ResumeViewer
