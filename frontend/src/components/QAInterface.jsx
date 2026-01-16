import React, { useState } from 'react';
import axios from 'axios';

const QAInterface = ({ documentData }) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const sampleQuestions = [
    "What are the termination conditions?",
    "What are my obligations under this contract?",
    "What penalties or fees are mentioned?",
    "What are the confidentiality requirements?",
    "What happens if I breach this agreement?",
    "What are the payment terms?",
    "How long is this agreement valid?",
    "What are the liability limitations?"
  ];

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    if (!documentData?.document_id) {
      setError('No document loaded');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setAnswer(null);

      const response = await axios.post('/api/ask', {
        document_id: documentData.document_id,
        question: question.trim()
      });

      setAnswer(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const handleSampleQuestion = (sampleQ) => {
    setQuestion(sampleQ);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  return (
    <div className="qa-interface">
      <h2>🤖 Ask Questions About Your Document</h2>
      
      <div className="qa-disclaimer">
        <p><strong>Note:</strong> The AI will only answer based on the content of your uploaded document. It cannot provide legal advice or information not contained in the document.</p>
      </div>

      {/* Sample Questions */}
      <div className="sample-questions">
        <h3>💡 Sample Questions</h3>
        <div className="sample-questions-grid">
          {sampleQuestions.map((sampleQ, index) => (
            <button
              key={index}
              className="sample-question-btn"
              onClick={() => handleSampleQuestion(sampleQ)}
              disabled={loading}
            >
              {sampleQ}
            </button>
          ))}
        </div>
      </div>

      {/* Question Input */}
      <div className="question-input-container">
        <div className="question-input">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question about the document here..."
            disabled={loading}
            rows={3}
          />
          <button
            onClick={handleAskQuestion}
            disabled={loading || !question.trim() || !documentData?.document_id}
            className="ask-button"
          >
            {loading ? '🤔 Thinking...' : '❓ Ask Question'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Answer Display */}
      {answer && (
        <div className="answer-container">
          <div className="answer-header">
            <h3>💬 Answer</h3>
            <div className="answer-meta">
              <span className="confidence">
                Confidence: {Math.round(answer.confidence * 100)}%
              </span>
              {answer.relevant_clauses && answer.relevant_clauses.length > 0 && (
                <span className="relevant-clauses">
                  Based on {answer.relevant_clauses.length} clause(s)
                </span>
              )}
            </div>
          </div>

          <div className="question-display">
            <strong>Question:</strong> {answer.question}
          </div>

          <div className="answer-text">
            {answer.answer.split('\n').map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>

          {answer.relevant_clauses && answer.relevant_clauses.length > 0 && (
            <div className="relevant-clauses-info">
              <h4>📎 Relevant Clauses</h4>
              <p>This answer is based on clauses: {answer.relevant_clauses.join(', ')}</p>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner">🤔</div>
          <p>Analyzing your question and searching the document...</p>
        </div>
      )}
    </div>
  );
};

export default QAInterface;