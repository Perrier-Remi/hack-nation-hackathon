import { useState } from 'react'
import './App.css'

interface TranscriptResult {
  success: boolean
  transcript: string
  summary: string
  key_points: string[]
  language: string
  word_count: number
  transcript_path: string
  cached?: boolean
  error?: string
  message?: string
}

function Transcript() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<TranscriptResult | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
    }
  }

  const handleTranscribe = async () => {
    if (!file) return

    setUploading(true)
    setResult(null)
    
    const formData = new FormData()
    formData.append('video', file)

    try {
      const response = await fetch('http://localhost:8000/transcript', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Transcription error:', error)
      setResult({ 
        success: false,
        error: 'Network error',
        message: 'Failed to connect to server',
        transcript: '',
        summary: '',
        key_points: [],
        language: '',
        word_count: 0,
        transcript_path: ''
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="app">
      <h1>Video Transcription</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Upload a video to get an AI-powered transcript
      </p>
      
      <div className="upload-section">
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <button onClick={handleTranscribe} disabled={!file || uploading}>
          {uploading ? 'Processing...' : 'Transcribe Video'}
        </button>
      </div>

      {file && !result && (
        <div style={{ marginTop: '1rem', color: '#666' }}>
          Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
        </div>
      )}

      {uploading && (
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <p>⏳ Processing your video...</p>
          <p style={{ fontSize: '0.9rem', color: '#666' }}>
            This may take a minute. Extracting audio and transcribing...
          </p>
        </div>
      )}

      {result && (
        <div className="result" style={{ marginTop: '2rem' }}>
          {result.success ? (
            <>
              <h2>✅ Transcription Complete</h2>
              
              {result.cached && (
                <div style={{ 
                  marginBottom: '1rem', 
                  padding: '0.75rem', 
                  background: '#e3f2fd', 
                  border: '1px solid #2196f3',
                  borderRadius: '8px',
                  color: '#1976d2',
                  fontSize: '0.9rem'
                }}>
                  ⚡ Using cached transcript (file already processed)
                </div>
              )}
              
              <div style={{ marginBottom: '1.5rem', padding: '1rem', background: '#f5f5f5', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#666' }}>
                  <span>Language: {result.language}</span>
                  <span>Words: {result.word_count}</span>
                </div>
              </div>

              {result.summary && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3>📋 Summary</h3>
                  <p style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', lineHeight: '1.6' }}>
                    {result.summary}
                  </p>
                </div>
              )}

              {result.key_points && result.key_points.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3>🔑 Key Points</h3>
                  <ul style={{ textAlign: 'left', lineHeight: '1.8' }}>
                    {result.key_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ marginBottom: '1.5rem' }}>
                <h3>📝 Full Transcript</h3>
                <div style={{ 
                  background: '#fff', 
                  padding: '1.5rem', 
                  borderRadius: '8px', 
                  border: '1px solid #e0e0e0',
                  maxHeight: '400px',
                  overflow: 'auto',
                  textAlign: 'left',
                  lineHeight: '1.8',
                  whiteSpace: 'pre-wrap'
                }}>
                  {result.transcript}
                </div>
              </div>

              {result.transcript_path && (
                <p style={{ fontSize: '0.85rem', color: '#999' }}>
                  Saved to: {result.transcript_path}
                </p>
              )}
            </>
          ) : (
            <>
              <h2 style={{ color: '#d32f2f' }}>❌ Transcription Failed</h2>
              <div style={{ background: '#ffebee', padding: '1rem', borderRadius: '8px', marginTop: '1rem' }}>
                <p><strong>Error:</strong> {result.error}</p>
                <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>{result.message}</p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default Transcript

