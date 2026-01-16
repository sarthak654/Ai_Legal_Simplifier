import React, { useState } from 'react';
import axios from 'axios';

const DocumentUpload = ({ onDocumentUploaded }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('Please select a PDF file');
        return;
      }
      if (selectedFile.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB');
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    try {
      setUploading(true);
      setError('');

      // Upload file
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const documentId = uploadResponse.data.document_id;

      // Analyze document
      setUploading(false);
      setAnalyzing(true);

      const analysisResponse = await axios.post(`/api/analyze/${documentId}`);
      
      // Notify parent component
      onDocumentUploaded(analysisResponse.data);
      
      // Reset form
      setFile(null);
      setAnalyzing(false);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
      setUploading(false);
      setAnalyzing(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>📄 Upload Legal Document</h2>
      
      <div className="disclaimer">
        <p><strong>⚠️ Important:</strong> This tool is for educational purposes only and does not provide legal advice. Always consult with a qualified attorney for legal matters.</p>
      </div>

      <div className="upload-form">
        <div className="file-input-container">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={uploading || analyzing}
            id="file-input"
          />
          <label htmlFor="file-input" className="file-input-label">
            {file ? file.name : 'Choose PDF file (max 5MB)'}
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading || analyzing}
          className="upload-button"
        >
          {uploading && '📤 Uploading...'}
          {analyzing && '🔍 Analyzing...'}
          {!uploading && !analyzing && '🚀 Upload & Analyze'}
        </button>

        {error && <div className="error-message">{error}</div>}
        
        {(uploading || analyzing) && (
          <div className="progress-info">
            {uploading && <p>Uploading document...</p>}
            {analyzing && (
              <div>
                <p>Analyzing document...</p>
                <ul>
                  <li>✓ Extracting text from PDF</li>
                  <li>✓ Splitting into legal clauses</li>
                  <li>🔄 Simplifying legal language</li>
                  <li>🔄 Detecting risk levels</li>
                  <li>🔄 Creating Q&A embeddings</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;