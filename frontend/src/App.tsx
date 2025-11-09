import { useState } from 'react'
import './App.css'
import Transcript from './Transcript'
import PipelineGraph, { PipelineNodeId, PipelineStatus } from './PipelineGraph'

type Tab = 'analysis' | 'transcript' | 'graph'

const defaultPipelineState: Record<PipelineNodeId, PipelineStatus> = {
  upload: 'idle',
  preprocess: 'idle',
  transcription: 'idle',
  safety: 'idle',
  llm: 'idle',
  veo: 'idle',
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('analysis')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [dragOver, setDragOver] = useState(false)
  const [enhancing, setEnhancing] = useState(false)
  const [enhancementResult, setEnhancementResult] = useState<any>(null)
  const [transcriptResult, setTranscriptResult] = useState<any>(null)
  const [safetyResult, setSafetyResult] = useState<any>(null)
  const [videoHash, setVideoHash] = useState<string | null>(null)
  const [pipelineState, setPipelineState] = useState<Record<PipelineNodeId, PipelineStatus>>(defaultPipelineState)
  const [enhanceDuration, setEnhanceDuration] = useState<number>(6)
  const [enhanceAspect, setEnhanceAspect] = useState<'16:9' | '9:16'>('16:9')
  const [enhanceVideoCount, setEnhanceVideoCount] = useState<number>(1)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setTranscriptResult(null)
      setSafetyResult(null)
      setVideoHash(null)
      setPipelineState(defaultPipelineState)
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
      setTranscriptResult(null)
      setSafetyResult(null)
      setVideoHash(null)
      setPipelineState(defaultPipelineState)
    }
  }

  const getVideoHash = () => result?.video_hash ?? videoHash ?? null

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setEnhancementResult(null)
    setTranscriptResult(null)
    setSafetyResult(null)
    setPipelineState({
      upload: 'running',
      preprocess: 'running',
      transcription: 'idle',
      safety: 'idle',
      llm: 'running',
      veo: 'idle',
    })

    const formData = new FormData()
    formData.append('video', file)

    try {
      const response = await fetch('http://localhost:8000/analyze-video', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Analysis failed')
      }
      setResult(data)
      const hash = data.video_hash ?? data.file_hash ?? null
      setVideoHash(hash)
      setPipelineState((prev) => ({
        ...prev,
        upload: 'done',
        preprocess: 'done',
        llm: data?.llm_summary ? 'done' : 'idle',
        transcription: 'idle',
        safety: 'idle',
        veo: 'idle',
      }))
    } catch (error) {
      console.error('Upload error:', error)
      setResult({ error: 'Upload failed', message: 'Failed to connect to server' })
      setPipelineState((prev) => ({
        ...prev,
        upload: 'error',
        preprocess: 'error',
        llm: 'error',
      }))
    } finally {
      setUploading(false)
    }
  }

  const handleTranscriptStep = async () => {
    if (!file) {
      console.error('Transcript requires an uploaded video file')
      setPipelineState((prev) => ({ ...prev, transcription: 'error' }))
      return
    }
    setPipelineState((prev) => ({ ...prev, transcription: 'running' }))
    try {
      const formData = new FormData()
      formData.append('video', file)
      const response = await fetch('http://localhost:8000/transcript', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Transcription failed')
      }
      setTranscriptResult(data)
      setVideoHash(data.video_hash ?? getVideoHash())
      setPipelineState((prev) => ({ ...prev, transcription: 'done' }))
    } catch (error) {
      console.error('Transcript error:', error)
      setPipelineState((prev) => ({ ...prev, transcription: 'error' }))
    }
  }

  const handleSafetyStep = async () => {
    const hash = getVideoHash()
    if (!hash) {
      console.error('Safety check requires a processed video hash')
      setPipelineState((prev) => ({ ...prev, safety: 'error' }))
      return
    }
    setPipelineState((prev) => ({ ...prev, safety: 'running' }))
    try {
      const response = await fetch('http://localhost:8000/safety-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_hash: hash }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data?.detail || data?.error || 'Safety check failed')
      }
      setSafetyResult(data)
      setPipelineState((prev) => ({ ...prev, safety: 'done' }))
    } catch (error) {
      console.error('Safety check error:', error)
      setPipelineState((prev) => ({ ...prev, safety: 'error' }))
    }
  }

  const handleEnhanceVideo = async (maxScenes: number = 3) => {
    const hash = getVideoHash()
    if (!hash) {
      console.error('No video hash available')
      setPipelineState((prev) => ({ ...prev, veo: 'error' }))
      return
    }

    setEnhancing(true)
    setEnhancementResult(null)
    setPipelineState((prev) => ({ ...prev, veo: 'running' }))

    try {
      const response = await fetch('http://localhost:8000/enhance-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_hash: hash,
          max_scenes: maxScenes,
          aspect_ratio: enhanceAspect,
          duration_seconds: enhanceDuration,
          video_count: enhanceVideoCount,
        }),
      })

      if (!response.ok) {
        throw new Error(`Enhancement failed: ${response.statusText}`)
      }

      const data = await response.json()
      setEnhancementResult(data)
      setPipelineState((prev) => ({ ...prev, veo: data.success ? 'done' : 'error' }))
    } catch (error) {
      console.error('Enhancement error:', error)
      setEnhancementResult({
        success: false,
        error: 'Enhancement failed',
        message: error instanceof Error ? error.message : 'Failed to enhance video',
      })
      setPipelineState((prev) => ({ ...prev, veo: 'error' }))
    } finally {
      setEnhancing(false)
    }
  }

  const handlePipelineTrigger = async (nodeId: PipelineNodeId) => {
    switch (nodeId) {
      case 'upload':
      case 'preprocess':
      case 'llm':
        await handleUpload()
        break
      case 'transcription':
        await handleTranscriptStep()
        break
      case 'safety':
        await handleSafetyStep()
        break
      case 'veo':
        await handleEnhanceVideo(3)
        break
      default:
        break
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
                <div
                  style={{
                    padding: '1rem',
                    background: 'rgba(255, 255, 255, 0.6)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-glow)',
                    color: 'var(--text-secondary)',
                    fontStyle: 'italic',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                  }}
                >
                  {llmSummary.follow_up_prompt}
                </div>
              </div>
            )}

            <div className="summary-section" style={{ marginTop: '2rem' }}>
              <h4>🎬 AI Video Enhancement</h4>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Generate enhanced video scenes using Google Veo 2 based on the AI recommendations above.
              </p>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Duration
                  <select
                    value={enhanceDuration}
                    onChange={(e) => setEnhanceDuration(Number(e.target.value))}
                    style={{ marginTop: '0.3rem', padding: '0.4rem', borderRadius: '6px' }}
                  >
                    {[5, 6, 7, 8].map((value) => (
                      <option key={value} value={value}>
                        {value}s
                      </option>
                    ))}
                  </select>
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Aspect Ratio
                  <select
                    value={enhanceAspect}
                    onChange={(e) => setEnhanceAspect(e.target.value as '16:9' | '9:16')}
                    style={{ marginTop: '0.3rem', padding: '0.4rem', borderRadius: '6px' }}
                  >
                    <option value="16:9">16:9 (Landscape)</option>
                    <option value="9:16">9:16 (Portrait)</option>
                  </select>
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Variations
                  <select
                    value={enhanceVideoCount}
                    onChange={(e) => setEnhanceVideoCount(Number(e.target.value))}
                    style={{ marginTop: '0.3rem', padding: '0.4rem', borderRadius: '6px' }}
                  >
                    {[1, 2].map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <button
                className={`upload-button ${enhancing ? 'loading' : ''}`}
                onClick={() => handleEnhanceVideo(3)}
                disabled={enhancing || !getVideoHash()}
                style={{ width: 'auto', padding: '0.75rem 2rem' }}
              >
                {enhancing ? '🔄 Generating Enhanced Videos...' : '✨ Enhance with Veo 2'}
              </button>
              {enhancing && (
                <div className="status-message info" style={{ marginTop: '1rem' }}>
                  <div className="loading-spinner"></div>
                  <span>Generating enhanced videos with Veo 2... This may take a couple of minutes per scene.</span>
                </div>
              )}
            </div>
          </div>
        )}

        {enhancementResult && (
          <div className="llm-summary" style={{ marginTop: '2rem' }}>
            <h3>🎥 Veo 2 Enhancement Results</h3>

            {enhancementResult.success ? (
              <>
                <div className="summary-section">
                  <h4>✅ Generation Complete</h4>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    Enhanced {enhancementResult.total_scenes_enhanced ?? 0} scene(s) using{' '}
                    <strong>{enhancementResult.model}</strong>
                  </p>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Aspect ratio: {enhancementResult.aspect_ratio} • Duration: {enhancementResult.duration_seconds}s •
                    Variations: {enhancementResult.video_count}
                  </p>
                </div>

                <div className="summary-section">
                  <h4>📝 Enhancement Prompt Used</h4>
                  <div
                    style={{
                      padding: '1rem',
                      background: 'rgba(255, 255, 255, 0.6)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-glow)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.9rem',
                      lineHeight: '1.5',
                    }}
                  >
                    {enhancementResult.llm_follow_up_prompt}
                  </div>
                </div>

                {enhancementResult.enhancements && enhancementResult.enhancements.length > 0 && (
                  <div className="summary-section">
                    <h4>🎬 Enhanced Scenes</h4>
                    <div className="analysis-grid">
                      {enhancementResult.enhancements.map((scene: any, index: number) => (
                        <div key={index} className="analysis-card" style={{ textAlign: 'left' }}>
                          <h4 style={{ marginBottom: '0.5rem' }}>Scene {scene.scene_index}</h4>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Status:</strong>{' '}
                              <span style={{ color: scene.status === 'generated' ? '#4CAF50' : '#ff9800' }}>
                                {scene.status}
                              </span>
                            </div>
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Reference Frames:</strong> {scene.reference_frames_count}
                            </div>
                            {scene.duration_seconds && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Duration:</strong> {scene.duration_seconds}s
                              </div>
                            )}
                            {scene.aspect_ratio && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Aspect:</strong> {scene.aspect_ratio}
                              </div>
                            )}
                            {scene.file_size_mb && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Size:</strong> {scene.file_size_mb.toFixed(2)} MB
                              </div>
                            )}
                            {scene.enhanced_video_path && (
                              <div style={{ marginTop: '0.75rem', wordBreak: 'break-all' }}>
                                <strong>Output:</strong>
                                <br />
                                <code
                                  style={{
                                    fontSize: '0.75rem',
                                    background: 'rgba(0,0,0,0.05)',
                                    padding: '0.25rem',
                                    borderRadius: '4px',
                                  }}
                                >
                                  {scene.enhanced_video_path}
                                </code>
                              </div>
                            )}
                            {scene.error && (
                              <div style={{ marginTop: '0.75rem', color: '#ff4444' }}>
                                <strong>Error:</strong> {scene.error}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="status-message error">
                <span>❌ Enhancement Failed</span>
                <span>{enhancementResult.message || enhancementResult.error}</span>
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
        <button className={`tab-button ${activeTab === 'analysis' ? 'active' : ''}`} onClick={() => setActiveTab('analysis')}>
          📊 Video Analysis
        </button>
        <button
          className={`tab-button ${activeTab === 'transcript' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcript')}
        >
          📝 Video Transcript
        </button>
        <button className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>
          🧩 Pipeline Graph
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

            <button className={`upload-button ${uploading ? 'loading' : ''}`} onClick={handleUpload} disabled={!file || uploading}>
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
      ) : activeTab === 'transcript' ? (
        <Transcript />
      ) : (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <h2 style={{ marginBottom: '0.5rem' }}>Pipeline Orchestrator</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              Trigger each stage manually or watch their status as you run the automated flow. Nodes reflect whether a stage
              is waiting, running, completed, or needs attention.
            </p>
          </div>

          <PipelineGraph pipelineState={pipelineState} onTrigger={handlePipelineTrigger} disabled={uploading || enhancing} />

          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            <div className="graph-card">
              <h4>Selected Video</h4>
              <p>{file ? file.name : 'Choose a video in the Analysis tab to activate the pipeline.'}</p>
              <button className="graph-link-button" onClick={() => setActiveTab('analysis')}>
                Go to Analysis
              </button>
            </div>
            <div className="graph-card">
              <h4>Transcript</h4>
              <p>
                {pipelineState.transcription === 'done'
                  ? `Transcript ready (~${transcriptResult?.transcript?.split(' ').length ?? 0} words).`
                  : 'Generate the transcript to power safety analysis and summaries.'}
              </p>
              <button className="graph-link-button" onClick={() => setActiveTab('transcript')}>
                View Transcript Tab
              </button>
            </div>
            <div className="graph-card">
              <h4>Safety Report</h4>
              <p>
                {pipelineState.safety === 'done'
                  ? `Overall risk score: ${safetyResult?.overall?.score?.toFixed?.(2) ?? '—'}`
                  : 'Run the Safety Check node to flag NSFW, bias, or misleading claims.'}
              </p>
              <button
                className="graph-link-button"
                onClick={() => window.open('https://ai.google.dev/gemini-api/docs/video', '_blank')}
              >
                Veo Prompt Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
