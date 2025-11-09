import { useState } from 'react'
import './App.css'
import Transcript from './Transcript'

type Tab = 'analysis' | 'transcript'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('analysis')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
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
      setResult({ error: 'Upload failed' })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="app">
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ 
          display: 'flex', 
          gap: '1rem', 
          justifyContent: 'center',
          borderBottom: '2px solid #e0e0e0',
          paddingBottom: '0.5rem'
        }}>
          <button
            onClick={() => setActiveTab('analysis')}
            style={{
              padding: '0.5rem 2rem',
              background: activeTab === 'analysis' ? '#646cff' : 'transparent',
              color: activeTab === 'analysis' ? 'white' : '#646cff',
              border: 'none',
              cursor: 'pointer',
              borderRadius: '4px',
              fontWeight: activeTab === 'analysis' ? 'bold' : 'normal'
            }}
          >
            Video Analysis
          </button>
          <button
            onClick={() => setActiveTab('transcript')}
            style={{
              padding: '0.5rem 2rem',
              background: activeTab === 'transcript' ? '#646cff' : 'transparent',
              color: activeTab === 'transcript' ? 'white' : '#646cff',
              border: 'none',
              cursor: 'pointer',
              borderRadius: '4px',
              fontWeight: activeTab === 'transcript' ? 'bold' : 'normal'
            }}
          >
            Video Transcript
          </button>
        </div>
      </div>

      {activeTab === 'analysis' ? (
        <>
          <h1>Ad Scoring Tool</h1>
          <div className="upload-section">
            <input
              type="file"
              accept="video/mp4,video/webm,video/*"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <button onClick={handleUpload} disabled={!file || uploading}>
              {uploading ? 'Uploading...' : 'Upload Video'}
            </button>
          </div>
          {result && (
            <div className="result">
              <h2>Result:</h2>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </>
      ) : (
        <Transcript />
      )}
    </div>
  )
}

export default App

