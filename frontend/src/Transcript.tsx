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
  const [dragOver, setDragOver] = useState(false)

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
      <div className="app-header">
        <h1>Video Transcription</h1>
        <p>AI-Powered Audio Transcription & Analysis</p>
      </div>
      
      <div className="upload-section">
        <div className="file-input-wrapper">
          <label
            className={`file-input-label ${dragOver ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                setFile(e.dataTransfer.files[0]);
                setResult(null);
                setSafetyResult(null);
              }
            }}
          >
            <input
              type="file"
              className="file-input"
              accept="video/mp4,video/webm,video/*"
              onChange={handleFileChange}
              disabled={uploading}
              id="transcript-upload"
            />
            <label htmlFor="transcript-upload" style={{ cursor: 'pointer' }}>
              {file ? '📹 ' + file.name : '📤 Drop video or click to upload'}
            </label>
          </label>
        </div>

        {file && !result && (
          <div className="file-info">
            Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}

        <button
          className={`upload-button ${uploading ? 'loading' : ''}`}
          onClick={handleTranscribe}
          disabled={!file || uploading}
        >
          {uploading ? 'Processing...' : '🎙️ Transcribe Video'}
        </button>

        {uploading && (
          <div className="status-message info">
            <div className="loading-spinner"></div>
            <span>Processing your video... Extracting audio and transcribing...</span>
          </div>
        )}
      </div>


      {result && (
        <div className="result" style={{ marginTop: '2rem' }}>
          {result.success ? (
            <>
              <h2>✅ Transcription Complete</h2>
              
              {result.cached && (
                <div className="status-message success">
                  <span>⚡</span>
                  <span>Using cached transcript (file already processed)</span>
                </div>
              )}
              
              <div className="analysis-card" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  <span>🌐 Language: <strong style={{ color: 'var(--primary)' }}>{result.language}</strong></span>
                  <span>📊 Words: <strong style={{ color: 'var(--primary)' }}>{result.word_count}</strong></span>
                </div>
              </div>

              {result.summary && (
                <div className="summary-section">
                  <h3>📋 Summary</h3>
                  <p style={{ 
                    background: 'rgba(255, 255, 255, 0.6)', 
                    padding: '1rem', 
                    borderRadius: '12px', 
                    border: '1px solid var(--border-glow)',
                    lineHeight: '1.6',
                    color: 'var(--text-secondary)',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
                  }}>
                    {result.summary}
                  </p>
                </div>
              )}

              {result.key_points && result.key_points.length > 0 && (
                <div className="summary-section">
                  <h3>🔑 Key Points</h3>
                  <ul className="summary-list">
                    {result.key_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="summary-section">
                <h3>📝 Full Transcript</h3>
                <div className="json-display" style={{ 
                  maxHeight: '400px',
                  overflow: 'auto',
                  textAlign: 'left',
                  lineHeight: '1.8',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--text-secondary)'
                }}>
                  {result.transcript}
                </div>
              </div>

              {result.transcript_path && (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  💾 Saved to: <code style={{ color: 'var(--primary)' }}>{result.transcript_path}</code>
                </p>
              )}

              {/* Safety Check Section */}
              <div className="llm-summary" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginTop: 0 }}>🛡️ Safety & Ethics Check</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1rem' }}>
                  Analyze this video for content safety, bias, and misleading claims
                </p>
                {result.video_hash ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Video Hash: <code style={{ color: 'var(--primary)' }}>{result.video_hash}</code>
                  </p>
                ) : (
                  <div className="status-message error" style={{ marginBottom: '1rem' }}>
                    <span>⚠️</span>
                    <span>No video hash available - safety check disabled</span>
                  </div>
                )}
                <button 
                  className={`upload-button ${safetyChecking ? 'loading' : ''}`}
                  onClick={() => {
                    console.log('Safety check button clicked!', { video_hash: result.video_hash })
                    handleSafetyCheck()
                  }}
                  disabled={safetyChecking || !result.video_hash}
                  style={{
                    background: (safetyChecking || !result.video_hash) 
                      ? 'rgba(255, 255, 255, 0.1)' 
                      : 'linear-gradient(135deg, var(--accent) 0%, #00cc6a 100%)',
                    cursor: (safetyChecking || !result.video_hash) ? 'not-allowed' : 'pointer',
                    opacity: (safetyChecking || !result.video_hash) ? 0.5 : 1
                  }}
                >
                  {safetyChecking ? 'Checking...' : '🔍 Run Safety Check'}
                </button>
              </div>
            </>
          ) : (
            <>
              <h2 style={{ color: '#ff4444' }}>❌ Transcription Failed</h2>
              <div className="status-message error">
                <span>Error:</span>
                <span>{result.error}</span>
              </div>
              {result.message && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {result.message}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {/* Safety Check Results */}
      {safetyResult && (
        <div className="result" style={{ marginTop: '2rem', borderTop: '2px solid var(--border-glow)', paddingTop: '2rem' }}>
          {safetyResult.success ? (
            <>
              <h2>🛡️ Safety & Ethics Report</h2>
              
              {safetyResult.cached && (
                <div className="status-message success">
                  <span>⚡</span>
                  <span>Using cached safety report</span>
                </div>
              )}

              {/* Overall Score */}
              <div className="analysis-card" style={{ 
                marginBottom: '2rem', 
                padding: '1.5rem',
                background: safetyResult.severity === 'safe' 
                  ? 'rgba(0, 255, 136, 0.1)' 
                  : safetyResult.severity === 'warning' 
                    ? 'rgba(255, 152, 0, 0.1)' 
                    : 'rgba(255, 68, 68, 0.1)',
                border: `2px solid ${safetyResult.severity === 'safe' ? 'var(--accent)' : safetyResult.severity === 'warning' ? '#ff9800' : '#ff4444'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h3 style={{ margin: 0, color: 'var(--primary)' }}>Overall Safety Score</h3>
                    <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                      Status: <strong style={{ color: 'var(--text-primary)' }}>{safetyResult.severity?.toUpperCase()}</strong>
                    </p>
                  </div>
                  <div className="score" style={{ 
                    fontSize: '3rem',
                    color: safetyResult.severity === 'safe' ? 'var(--accent)' : safetyResult.severity === 'warning' ? '#ff9800' : '#ff4444'
                  }}>
                    {safetyResult.overall_score}/100
                  </div>
                </div>
              </div>

              {/* NSFW/Violence Check */}
              {safetyResult.nsfw_violence && (
                <div className="analysis-card" style={{ marginBottom: '1.5rem' }}>
                  <h3>🔞 NSFW & Violence Detection</h3>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Score:</strong> <span style={{ color: 'var(--primary)' }}>{safetyResult.nsfw_violence.score}/100</span></p>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Flag:</strong> {safetyResult.nsfw_violence.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Frames Analyzed:</strong> {safetyResult.nsfw_violence.frames_analyzed}</p>
                  {safetyResult.nsfw_violence.issues_found > 0 && (
                    <p style={{ color: '#ff4444', marginTop: '0.5rem' }}><strong>Issues Found:</strong> {safetyResult.nsfw_violence.issues_found}</p>
                  )}
                  {safetyResult.nsfw_violence.details && (
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      {safetyResult.nsfw_violence.details}
                    </p>
                  )}
                </div>
              )}

              {/* Bias & Stereotypes Check */}
              {safetyResult.bias_stereotypes && (
                <div className="analysis-card" style={{ marginBottom: '1.5rem' }}>
                  <h3>⚖️ Bias & Stereotypes Check</h3>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Score:</strong> <span style={{ color: 'var(--primary)' }}>{safetyResult.bias_stereotypes.score}/100</span></p>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Flag:</strong> {safetyResult.bias_stereotypes.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                  {safetyResult.bias_stereotypes.issues_found > 0 && (
                    <p style={{ color: '#ff4444', marginTop: '0.5rem' }}><strong>Issues Found:</strong> {safetyResult.bias_stereotypes.issues_found}</p>
                  )}
                  {safetyResult.bias_stereotypes.details && (
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      {safetyResult.bias_stereotypes.details}
                    </p>
                  )}
                </div>
              )}

              {/* Misleading Claims Check */}
              {safetyResult.misleading_claims && (
                <div className="analysis-card" style={{ marginBottom: '1.5rem' }}>
                  <h3>⚠️ Misleading Claims Detection</h3>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Score:</strong> <span style={{ color: 'var(--primary)' }}>{safetyResult.misleading_claims.score}/100</span></p>
                  <p style={{ color: 'var(--text-secondary)' }}><strong>Flag:</strong> {safetyResult.misleading_claims.flag ? '⚠️ Flagged' : '✅ Clear'}</p>
                  {safetyResult.misleading_claims.keywords_found && safetyResult.misleading_claims.keywords_found.length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <p style={{ color: 'var(--text-secondary)' }}><strong>Suspicious Keywords:</strong></p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                        {safetyResult.misleading_claims.keywords_found.map((keyword: string, i: number) => (
                          <span key={i} style={{
                            padding: '0.25rem 0.75rem',
                            background: 'rgba(255, 68, 68, 0.2)',
                            color: '#ff4444',
                            borderRadius: '12px',
                            fontSize: '0.85rem',
                            border: '1px solid rgba(255, 68, 68, 0.3)'
                          }}>
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {safetyResult.misleading_claims.details && (
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      {safetyResult.misleading_claims.details}
                    </p>
                  )}
                </div>
              )}

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '1rem' }}>
                Checked at: {safetyResult.checked_at ? new Date(safetyResult.checked_at).toLocaleString() : 'N/A'}
              </p>
            </>
          ) : (
            <>
              <h2 style={{ color: '#ff4444' }}>❌ Safety Check Failed</h2>
              <div className="status-message error">
                <span>Error:</span>
                <span>{safetyResult.error}</span>
              </div>
              {safetyResult.message && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                  {safetyResult.message}
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default Transcript

