import { useState } from 'react'
import './App.css'

interface TranscriptResult {
  success: boolean
  video_hash?: string
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

interface SafetyResult {
  success: boolean
  video_hash?: string
  overall_score?: number
  severity?: string
  nsfw_violence?: any
  bias_stereotypes?: any
  misleading_claims?: any
  checked_at?: string
  cached?: boolean
  error?: string
  message?: string
}

function Transcript() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<TranscriptResult | null>(null)
  const [safetyChecking, setSafetyChecking] = useState(false)
  const [safetyResult, setSafetyResult] = useState<SafetyResult | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setSafetyResult(null)
    }
  }

  const handleTranscribe = async () => {
    if (!file) return

    setUploading(true)
    setResult(null)
    setSafetyResult(null)
    
    const formData = new FormData()
    formData.append('video', file)

    try {
      const response = await fetch('http://localhost:8000/transcript', {
        method: 'POST',
        body: formData,
      })
      
      // Check if response is OK
      if (!response.ok) {
        console.error('Server error:', response.status, response.statusText)
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        setResult({ 
          success: false,
          error: errorData.error || 'Server error',
          message: errorData.message || `Server returned ${response.status}`,
          transcript: '',
          summary: '',
          key_points: [],
          language: '',
          word_count: 0,
          transcript_path: ''
        })
        return
      }
      
      const data = await response.json()
      console.log('Transcription success:', data)
      setResult(data)
    } catch (error) {
      console.error('Transcription error:', error)
      setResult({ 
        success: false,
        error: 'Network error',
        message: error instanceof Error ? error.message : 'Failed to connect to server',
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

  const handleSafetyCheck = async () => {
    if (!result || !result.video_hash) return

    setSafetyChecking(true)
    setSafetyResult(null)

    try {
      const response = await fetch('http://localhost:8000/safety-check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ video_hash: result.video_hash }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        setSafetyResult({
          success: false,
          error: errorData.error || 'Server error',
          message: errorData.message || `Server returned ${response.status}`,
        })
        return
      }

      const data = await response.json()
      console.log('Safety check success:', data)
      setSafetyResult(data)
    } catch (error) {
      console.error('Safety check error:', error)
      setSafetyResult({
        success: false,
        error: 'Network error',
        message: error instanceof Error ? error.message : 'Failed to connect to server',
      })
    } finally {
      setSafetyChecking(false)
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
          accept="video/mp4,video/webm,video/*"
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

              {/* Safety Check Section */}
              <div style={{ 
                marginTop: '2rem', 
                padding: '1.5rem', 
                background: '#f5f5f5', 
                borderRadius: '8px',
                border: '2px dashed #bdbdbd'
              }}>
                <h3 style={{ marginTop: 0 }}>🛡️ Safety & Ethics Check</h3>
                <p style={{ color: '#666', fontSize: '0.95rem', marginBottom: '1rem' }}>
                  Analyze this video for content safety, bias, and misleading claims
                </p>
                {result.video_hash ? (
                  <p style={{ fontSize: '0.85rem', color: '#999', marginBottom: '1rem' }}>
                    Video Hash: {result.video_hash}
                  </p>
                ) : (
                  <p style={{ fontSize: '0.85rem', color: '#f44336', marginBottom: '1rem' }}>
                    ⚠️ No video hash available - safety check disabled
                  </p>
                )}
                <button 
                  onClick={() => {
                    console.log('Safety check button clicked!', { video_hash: result.video_hash })
                    handleSafetyCheck()
                  }}
                  disabled={safetyChecking || !result.video_hash}
                  style={{
                    padding: '0.75rem 1.5rem',
                    fontSize: '1rem',
                    cursor: (safetyChecking || !result.video_hash) ? 'not-allowed' : 'pointer',
                    backgroundColor: (safetyChecking || !result.video_hash) ? '#ccc' : '#4caf50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '600'
                  }}
                >
                  {safetyChecking ? '⏳ Checking...' : '🔍 Run Safety Check'}
                </button>
              </div>
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

      {/* Safety Check Results */}
      {safetyResult && (
        <div className="result" style={{ marginTop: '2rem', borderTop: '2px solid #e0e0e0', paddingTop: '2rem' }}>
          {safetyResult.success ? (
            <>
              <h2>🛡️ Safety & Ethics Report</h2>
              
              {safetyResult.cached && (
                <div style={{ 
                  marginBottom: '1rem', 
                  padding: '0.75rem', 
                  background: '#e3f2fd', 
                  border: '1px solid #2196f3',
                  borderRadius: '8px',
                  color: '#1976d2',
                  fontSize: '0.9rem'
                }}>
                  ⚡ Using cached safety report
                </div>
              )}

              {/* Overall Score */}
              <div style={{ 
                marginBottom: '2rem', 
                padding: '1.5rem', 
                background: safetyResult.severity === 'safe' ? '#e8f5e9' : safetyResult.severity === 'warning' ? '#fff3e0' : '#ffebee',
                borderRadius: '12px',
                border: `3px solid ${safetyResult.severity === 'safe' ? '#4caf50' : safetyResult.severity === 'warning' ? '#ff9800' : '#f44336'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h3 style={{ margin: 0 }}>Overall Safety Score</h3>
                    <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#666' }}>
                      Status: <strong>{safetyResult.severity?.toUpperCase()}</strong>
                    </p>
                  </div>
                  <div style={{ 
                    fontSize: '3rem', 
                    fontWeight: 'bold',
                    color: safetyResult.severity === 'safe' ? '#4caf50' : safetyResult.severity === 'warning' ? '#ff9800' : '#f44336'
                  }}>
                    {safetyResult.overall_score}/100
                  </div>
                </div>
              </div>

              {/* NSFW/Violence Check */}
              {safetyResult.nsfw_violence && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3>🔞 NSFW & Violence Detection</h3>
                  <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
                    <p><strong>Score:</strong> {safetyResult.nsfw_violence.score}/100</p>
                    <p><strong>Flag:</strong> {safetyResult.nsfw_violence.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                    <p><strong>Frames Analyzed:</strong> {safetyResult.nsfw_violence.frames_analyzed}</p>
                    {safetyResult.nsfw_violence.issues_found > 0 && (
                      <p style={{ color: '#d32f2f' }}><strong>Issues Found:</strong> {safetyResult.nsfw_violence.issues_found}</p>
                    )}
                    {safetyResult.nsfw_violence.details && (
                      <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
                        {safetyResult.nsfw_violence.details}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Bias & Stereotypes Check */}
              {safetyResult.bias_stereotypes && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3>⚖️ Bias & Stereotypes Check</h3>
                  <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
                    <p><strong>Score:</strong> {safetyResult.bias_stereotypes.score}/100</p>
                    <p><strong>Flag:</strong> {safetyResult.bias_stereotypes.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                    {safetyResult.bias_stereotypes.issues_found > 0 && (
                      <p style={{ color: '#d32f2f' }}><strong>Issues Found:</strong> {safetyResult.bias_stereotypes.issues_found}</p>
                    )}
                    {safetyResult.bias_stereotypes.details && (
                      <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
                        {safetyResult.bias_stereotypes.details}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Misleading Claims Check */}
              {safetyResult.misleading_claims && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h3>⚠️ Misleading Claims Detection</h3>
                  <div style={{ background: '#fff', padding: '1rem', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
                    <p><strong>Score:</strong> {safetyResult.misleading_claims.score}/100</p>
                    <p><strong>Flag:</strong> {safetyResult.misleading_claims.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                    {safetyResult.misleading_claims.keywords_found && safetyResult.misleading_claims.keywords_found.length > 0 && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <p><strong>Suspicious Keywords:</strong></p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                          {safetyResult.misleading_claims.keywords_found.map((keyword: string, i: number) => (
                            <span key={i} style={{
                              padding: '0.25rem 0.75rem',
                              background: '#ffebee',
                              color: '#d32f2f',
                              borderRadius: '12px',
                              fontSize: '0.85rem'
                            }}>
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {safetyResult.misleading_claims.details && (
                      <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
                        {safetyResult.misleading_claims.details}
                      </p>
                    )}
                  </div>
                </div>
              )}

              <p style={{ fontSize: '0.85rem', color: '#999', marginTop: '1rem' }}>
                Checked at: {safetyResult.checked_at ? new Date(safetyResult.checked_at).toLocaleString() : 'N/A'}
              </p>
            </>
          ) : (
            <>
              <h2 style={{ color: '#d32f2f' }}>❌ Safety Check Failed</h2>
              <div style={{ background: '#ffebee', padding: '1rem', borderRadius: '8px', marginTop: '1rem' }}>
                <p><strong>Error:</strong> {safetyResult.error}</p>
                <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>{safetyResult.message}</p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default Transcript

