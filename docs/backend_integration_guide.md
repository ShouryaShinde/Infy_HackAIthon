# Backend API Documentation & Frontend Integration Guide

This guide provides everything needed to connect a React/Vite/Next.js frontend to the AI-powered meeting notes summarization backend.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│                 (http://localhost:5173)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / Multipart Form-Data
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Node.js Express Backend                     │
│                 (http://localhost:5001)                     │
│  - CORS enabled for frontend                                │
│  - Multer middleware for file upload handling               │
│  - Routes: /api/summarize-video, /api/summarize, ...        │
└──────────────────────────────┬──────────────────────────────┘
                               │ Stream / Axios
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Flask AI Service                    │
│                 (http://localhost:5000)                     │
│  - FFmpeg: Audio extraction (16kHz Mono WAV)                │
│  - Faster-Whisper: Local speech-to-text model (base, int8)  │
│  - Summary Engine: Cirrascale Llama-3.1-8B LLM              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Server Base URL & Environment Config

In your frontend `.env` (e.g. Vite):
```env
VITE_API_BASE_URL=http://localhost:5001
```

Or Create React App / Next.js:
```env
REACT_APP_API_BASE_URL=http://localhost:5001
# or
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001
```

---

## 3. Endpoints Reference

### A. Video Upload & Summarize (Primary Endpoint)

Uploads a `.mp4` video (or other supported formats), transcribes speech locally using FFmpeg + Faster-Whisper, and generates structured meeting notes using Cirrascale AI.

- **Method**: `POST`
- **URL**: `http://localhost:5001/api/summarize-video`
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file`: Video or Audio binary file (Supported: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.mp3`, `.wav`, `.m4a` — max 200MB).

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "data": {
    "transcript": "Hello everyone, thank you guys for coming to our weekly student success meeting...",
    "language": "en",
    "duration": 98.38,
    "segments": [
      {
        "start": 0.0,
        "end": 6.28,
        "text": "Hello everyone, thank you guys for coming to our weekly student success meeting and let's just get started"
      },
      {
        "start": 6.28,
        "end": 11.48,
        "text": "So I have our list of chronically absent students here and I've been noticing a troubling trend"
      }
    ],
    "summary": {
      "summary": "The team discussed strategies to improve student attendance on Fridays, including organizing a pancake breakfast.",
      "keyPoints": [
        "A list of chronically absent students was reviewed.",
        "Students frequently skip classes on Fridays.",
        "The team proposed a pancake breakfast to encourage attendance."
      ],
      "actionItems": [
        {
          "task": "Organize pancake breakfast for students",
          "responsible": "Not specified",
          "deadline": "Next week",
          "priority": "High"
        }
      ],
      "decisions": [
        "Try the pancake breakfast incentive next week."
      ],
      "pendingQuestions": []
    }
  }
}
```

#### Error Response (`400 / 500`)
```json
{
  "success": false,
  "message": "Video file is required. Please upload with field name 'file' or 'video'.",
  "error": "Details..."
}
```

---

### B. Text Summarization (Direct Notes Input)

Summarizes plain text notes without uploading media files.

- **Method**: `POST`
- **URL**: `http://localhost:5001/api/summarize`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "text": "The team discussed the upcoming hackathon project. Rahul will complete the backend API by Friday. Priya will prepare the presentation."
  }
  ```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "data": {
    "summary": "The team discussed the upcoming hackathon project and assigned tasks to team members.",
    "keyPoints": [
      "Rahul will complete the backend API by Friday.",
      "Priya will prepare the presentation."
    ],
    "actionItems": [
      {
        "task": "Complete backend API",
        "responsible": "Rahul",
        "deadline": "Friday",
        "priority": "High"
      },
      {
        "task": "Prepare presentation",
        "responsible": "Priya",
        "deadline": "Not specified",
        "priority": "Medium"
      }
    ],
    "decisions": [],
    "pendingQuestions": []
  }
}
```

---

### C. Video Transcription Only

Transcribes an uploaded video or audio file without sending it to the summary engine.

- **Method**: `POST`
- **URL**: `http://localhost:5001/api/transcribe`
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file`: Video or Audio binary file

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "data": {
    "transcript": "Hello everyone...",
    "language": "en",
    "languageProbability": 0.98,
    "duration": 98.38,
    "segments": [
      { "start": 0.0, "end": 6.28, "text": "Hello everyone..." }
    ]
  }
}
```

---

## 4. Frontend Data Models (TypeScript / JSDoc)

```typescript
export interface ActionItem {
  task: string;
  responsible: string;
  deadline: string;
  priority: 'High' | 'Medium' | 'Low';
}

export interface SummaryData {
  summary: string;
  keyPoints: string[];
  actionItems: ActionItem[];
  decisions: string[];
  pendingQuestions: string[];
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface VideoSummaryResponse {
  success: boolean;
  data: {
    transcript: string;
    language: string;
    duration: number;
    segments: TranscriptSegment[];
    summary: SummaryData;
  };
}
```

---

## 5. React Frontend Code Examples

### A. API Service Module (`src/services/api.js`)

```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Upload video file (.mp4) and receive transcription + summary
 * @param {File} file - The video file object
 * @param {Function} onProgress - Optional upload progress callback (0-100)
 */
export const summarizeVideo = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/summarize-video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

/**
 * Summarize raw text
 * @param {string} text - Meeting notes or transcript text
 */
export const summarizeText = async (text) => {
  const response = await apiClient.post('/api/summarize', { text });
  return response.data;
};
```

---

### B. React Video Upload Component Example

```jsx
import React, { useState } from 'react';
import { summarizeVideo } from '../services/api';

export default function VideoSummarizer() {
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a video file first (.mp4, .mov, etc.)');
      return;
    }

    setIsLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response = await summarizeVideo(file, (progress) => {
        setUploadProgress(progress);
      });

      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message || 'Failed to process video');
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.message || err.message || 'Server error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Meeting Video Summarizer</h1>

      {/* File Input */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4">
        <input
          type="file"
          accept="video/*,audio/*,.mp4,.mov,.mkv"
          onChange={handleFileChange}
          disabled={isLoading}
          className="mb-2"
        />
        {file && (
          <p className="text-sm text-gray-600 mt-2">
            Selected: <strong>{file.name}</strong> ({(file.size / (1024 * 1024)).toFixed(2)} MB)
          </p>
        )}
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={isLoading || !file}
        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isLoading ? 'Processing Video...' : 'Transcribe & Summarize'}
      </button>

      {/* Progress / Loading Indicator */}
      {isLoading && (
        <div className="mt-4">
          <p className="text-sm text-gray-600">
            {uploadProgress < 100
              ? `Uploading: ${uploadProgress}%`
              : 'Transcribing speech locally & generating AI summary (this may take a few seconds)...'}
          </p>
          <div className="w-full bg-gray-200 rounded h-2 mt-1">
            <div
              className="bg-blue-600 h-2 rounded transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Summary Section */}
          <div className="p-4 bg-gray-50 rounded-lg border">
            <h2 className="text-xl font-semibold mb-2">Executive Summary</h2>
            <p className="text-gray-800">{result.summary?.summary}</p>
          </div>

          {/* Key Points */}
          {result.summary?.keyPoints?.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg border">
              <h2 className="text-xl font-semibold mb-2">Key Discussion Points</h2>
              <ul className="list-disc list-inside space-y-1 text-gray-800">
                {result.summary.keyPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {result.summary?.actionItems?.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg border">
              <h2 className="text-xl font-semibold mb-2">Action Items</h2>
              <div className="space-y-2">
                {result.summary.actionItems.map((item, index) => (
                  <div key={index} className="p-3 bg-white rounded border flex justify-between items-center">
                    <div>
                      <p className="font-medium">{item.task}</p>
                      <p className="text-xs text-gray-500">
                        Assignee: {item.responsible} | Deadline: {item.deadline}
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded font-semibold ${
                      item.priority === 'High' ? 'bg-red-100 text-red-800' :
                      item.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {item.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Decisions */}
          {result.summary?.decisions?.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg border">
              <h2 className="text-xl font-semibold mb-2">Key Decisions</h2>
              <ul className="list-disc list-inside space-y-1 text-gray-800">
                {result.summary.decisions.map((decision, index) => (
                  <li key={index}>{decision}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Transcript Accordion / Viewer */}
          <details className="p-4 bg-gray-50 rounded-lg border">
            <summary className="font-semibold cursor-pointer">
              Full Transcript ({result.duration}s, {result.language?.toUpperCase()})
            </summary>
            <div className="mt-3 text-sm text-gray-700 max-h-60 overflow-y-auto space-y-2">
              {result.segments?.map((seg, idx) => (
                <p key={idx}>
                  <span className="text-xs text-gray-400 font-mono">[{seg.start}s - {seg.end}s]</span>{' '}
                  {seg.text}
                </p>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
```

---

## 6. Testing & Troubleshooting Checklist

| Check | Expected | Solution if Failing |
| :--- | :--- | :--- |
| **Node Backend Running** | Port `5001` (`http://localhost:5001/`) | Run `npm run dev` in `server/` |
| **Python AI Service Running** | Port `5000` (`http://localhost:5000/health`) | Run `python app.py` in `server/src/ai-service/` |
| **CORS Errors** | Frontend URL allowed | Ensure `CLIENT_URL=http://localhost:5173` in `server/.env` matches your frontend dev port |
| **Form Data Key** | Field name MUST be `file` | `formData.append('file', videoFile)` |
| **File Formats** | `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.mp3`, `.wav`, `.m4a` | Max size: 200MB |
