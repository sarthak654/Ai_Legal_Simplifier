import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ClauseViewer from './components/ClauseViewer';
import QAInterface from './components/QAInterface';
import './App.css';

function App() {
  const [documentData, setDocumentData] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');

  const handleDocumentUploaded = (data) => {
    setDocumentData(data);
    setActiveTab('clauses');
  };

  const handleNewDocument = () => {
    setDocumentData(null);
    setActiveTab('upload');
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>⚖️ AI Legal Simplifier & Q&A Assistant</h1>
        <p>Privacy-first legal document analysis using local AI</p>
        {documentData && (
          <button onClick={handleNewDocument} className="new-doc-btn">
            📄 Upload New Document
          </button>
        )}
      </header>

      <main className="app-main">
        {!documentData ? (
          <DocumentUpload onDocumentUploaded={handleDocumentUploaded} />
        ) : (
          <>
            <nav className="tab-navigation">
              <button
                className={`tab-btn ${activeTab === 'clauses' ? 'active' : ''}`}
                onClick={() => setActiveTab('clauses')}
              >
                📋 Clauses ({documentData.total_clauses})
              </button>
              <button
                className={`tab-btn ${activeTab === 'qa' ? 'active' : ''}`}
                onClick={() => setActiveTab('qa')}
              >
                🤖 Q&A
              </button>
            </nav>

            <div className="tab-content">
              {activeTab === 'clauses' && (
                <ClauseViewer documentData={documentData} />
              )}
              {activeTab === 'qa' && (
                <QAInterface documentData={documentData} />
              )}
            </div>
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>
          <strong>⚠️ Disclaimer:</strong> This tool is for educational purposes only. 
          It does not provide legal advice. Always consult with a qualified attorney for legal matters.
        </p>
        <p>🔒 Your documents are processed locally and never sent to external services.</p>
      </footer>
    </div>
  );
}

export default App;
