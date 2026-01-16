import React, { useState } from 'react';

const ClauseViewer = ({ documentData }) => {
  const [selectedClause, setSelectedClause] = useState(null);
  const [filterRisk, setFilterRisk] = useState('ALL');

  if (!documentData) {
    return <div>No document loaded</div>;
  }

  const { clauses, high_risk_count, medium_risk_count, low_risk_count } = documentData;

  const filteredClauses = clauses.filter(clause => {
    if (filterRisk === 'ALL') return true;
    return clause.risk_level === filterRisk;
  });

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'HIGH': return '#ff4444';
      case 'MEDIUM': return '#ff8800';
      case 'LOW': return '#44aa44';
      default: return '#666';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel) {
      case 'HIGH': return '🚨';
      case 'MEDIUM': return '⚠️';
      case 'LOW': return '✅';
      default: return '📄';
    }
  };

  return (
    <div className="clause-viewer">
      <h2>📋 Document Analysis Results</h2>
      
      {/* Risk Summary */}
      <div className="risk-summary">
        <h3>Risk Summary</h3>
        <div className="risk-stats">
          <div className="risk-stat high">
            <span className="risk-icon">🚨</span>
            <span className="risk-count">{high_risk_count}</span>
            <span className="risk-label">High Risk</span>
          </div>
          <div className="risk-stat medium">
            <span className="risk-icon">⚠️</span>
            <span className="risk-count">{medium_risk_count}</span>
            <span className="risk-label">Medium Risk</span>
          </div>
          <div className="risk-stat low">
            <span className="risk-icon">✅</span>
            <span className="risk-count">{low_risk_count}</span>
            <span className="risk-label">Low Risk</span>
          </div>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="filter-controls">
        <label>Filter by Risk Level:</label>
        <select 
          value={filterRisk} 
          onChange={(e) => setFilterRisk(e.target.value)}
        >
          <option value="ALL">All Clauses ({clauses.length})</option>
          <option value="HIGH">High Risk ({high_risk_count})</option>
          <option value="MEDIUM">Medium Risk ({medium_risk_count})</option>
          <option value="LOW">Low Risk ({low_risk_count})</option>
        </select>
      </div>

      {/* Clauses List */}
      <div className="clauses-container">
        <div className="clauses-list">
          <h3>Clauses ({filteredClauses.length})</h3>
          {filteredClauses.map((clause) => (
            <div
              key={clause.id}
              className={`clause-item ${selectedClause?.id === clause.id ? 'selected' : ''}`}
              onClick={() => setSelectedClause(clause)}
            >
              <div className="clause-header">
                <span className="clause-number">#{clause.id}</span>
                <span 
                  className="risk-badge"
                  style={{ backgroundColor: getRiskColor(clause.risk_level) }}
                >
                  {getRiskIcon(clause.risk_level)} {clause.risk_level}
                </span>
              </div>
              <div className="clause-preview">
                {clause.original_text.substring(0, 100)}...
              </div>
            </div>
          ))}
        </div>

        {/* Clause Detail */}
        {selectedClause && (
          <div className="clause-detail">
            <div className="clause-detail-header">
              <h3>Clause #{selectedClause.id}</h3>
              <span 
                className="risk-badge large"
                style={{ backgroundColor: getRiskColor(selectedClause.risk_level) }}
              >
                {getRiskIcon(selectedClause.risk_level)} {selectedClause.risk_level} RISK
              </span>
            </div>

            <div className="clause-content">
              <div className="original-text">
                <h4>📜 Original Legal Text</h4>
                <div className="text-content">
                  {selectedClause.original_text}
                </div>
              </div>

              <div className="simplified-text">
                <h4>💡 Simplified Explanation</h4>
                <div className="text-content simplified">
                  {selectedClause.simplified_text}
                </div>
              </div>

              {selectedClause.risk_reasons && selectedClause.risk_reasons.length > 0 && (
                <div className="risk-reasons">
                  <h4>⚠️ Risk Factors</h4>
                  <ul>
                    {selectedClause.risk_reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClauseViewer;