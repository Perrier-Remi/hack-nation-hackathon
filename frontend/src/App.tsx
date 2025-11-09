import { useState } from 'react'
import './App.css'
import Transcript from './Transcript'

type Tab = 'analysis' | 'transcript'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('analysis')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('video', file)

    try {
      const response = await fetch('http://localhost:8000/analyze-video', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Upload error:', error)
      setResult({ error: 'Upload failed', message: 'Failed to connect to server' })
    } finally {
      setUploading(false)
    }
  }

  const renderAnalysisResults = () => {
    if (!result || result.error) {
      return (
        <div className="result">
          <h2 style={{ color: '#ff4444' }}>❌ Analysis Failed</h2>
          <div className="status-message error">
            <span>Error:</span>
            <span>{result?.error || 'Unknown error'}</span>
          </div>
        </div>
      )
    }

    const analyzers = result.analyzers || []
    const llmSummary = result.llm_summary || {}

    return (
      <div className="result">
        <h2>📊 Analysis Results</h2>
        
        {analyzers.length > 0 && (
          <div className="analysis-grid">
            {analyzers.map((item: any, index: number) => (
              <div key={index} className="analysis-card">
                <h4>{item.analyzer}</h4>
                {typeof item.result === 'object' ? (
                  <div>
                    {Object.entries(item.result).map(([key, value]: [string, any]) => (
                      <div key={key} style={{ marginTop: '0.5rem' }}>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                          {key}:
                        </span>
                        <span className="score" style={{ display: 'block', marginTop: '0.25rem' }}>
                          {typeof value === 'number' ? value.toFixed(2) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="score">{item.result}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {llmSummary && llmSummary.summary && llmSummary.summary !== 'LLM analysis unavailable' && (
          <div className="llm-summary">
            <h3>🤖 AI Analysis Summary</h3>
            
            {llmSummary.summary && (
              <div className="summary-section">
                <h4>Overall Assessment</h4>
                <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  {llmSummary.summary}
                </p>
              </div>
            )}

            {llmSummary.strengths && llmSummary.strengths.length > 0 && (
              <div className="summary-section">
                <h4>✨ Strengths</h4>
                <ul className="summary-list">
                  {llmSummary.strengths.map((strength: string, i: number) => (
                    <li key={i}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}

            {llmSummary.weaknesses && llmSummary.weaknesses.length > 0 && (
              <div className="summary-section">
                <h4>⚠️ Weaknesses</h4>
                <ul className="summary-list">
                  {llmSummary.weaknesses.map((weakness: string, i: number) => (
                    <li key={i}>{weakness}</li>
                  ))}
                </ul>
              </div>
            )}

            {llmSummary.recommendations && llmSummary.recommendations.length > 0 && (
              <div className="summary-section">
                <h4>💡 Recommendations</h4>
                <ul className="summary-list">
                  {llmSummary.recommendations.map((rec: string, i: number) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {llmSummary.follow_up_prompt && (
              <div className="summary-section">
                <h4>🚀 Follow-up Prompt</h4>
                <div style={{
                  padding: '1rem',
                  background: 'rgba(255, 255, 255, 0.6)',
                  borderRadius: '8px',
                  border: '1px solid var(--border-glow)',
                  color: 'var(--text-secondary)',
                  fontStyle: 'italic',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
                }}>
                  {llmSummary.follow_up_prompt}
                </div>
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '2rem' }}>
          <h3>Raw Data</h3>
          <div className="json-display">
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="app-header">
        <h1>Ad Scoring Tool</h1>
        <p>AI-Powered Video Analysis Platform</p>
      </div>

      <div className="tab-nav">
        <button
          className={`tab-button ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          📊 Video Analysis
        </button>
        <button
          className={`tab-button ${activeTab === 'transcript' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcript')}
        >
          📝 Video Transcript
        </button>
      </div>

      {activeTab === 'analysis' ? (
        <>
          <div className="upload-section">
            <div className="file-input-wrapper">
              <label
                className={`file-input-label ${dragOver ? 'dragover' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  className="file-input"
                  accept="video/mp4,video/webm,video/*"
                  onChange={handleFileChange}
                  disabled={uploading}
                  id="video-upload"
                />
                <label htmlFor="video-upload" style={{ cursor: 'pointer' }}>
                  {file ? '📹 ' + file.name : '📤 Drop video or click to upload'}
                </label>
              </label>
            </div>

            {file && (
              <div className="file-info">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </div>
            )}

            <button
              className={`upload-button ${uploading ? 'loading' : ''}`}
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? 'Processing...' : '🚀 Analyze Video'}
            </button>

            {uploading && (
              <div className="status-message info">
                <div className="loading-spinner"></div>
                <span>Processing your video... This may take a minute.</span>
              </div>
            )}
          </div>

          {result && renderAnalysisResults()}
        </>
      ) : (
        <Transcript />
      )}
    </div>
  )
}

export default App
