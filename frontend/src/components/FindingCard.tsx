import React, { useState } from 'react';
import type { CheckResult, Severity } from '../types/audit';
import {
  CopyIcon,
  CheckIcon,
  ExternalLinkIcon,
  ShieldAlertIcon
} from './Icons';

interface FindingCardProps {
  checkResults: CheckResult[];
}

export const FindingCard: React.FC<FindingCardProps> = ({ checkResults }) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const allFindings = checkResults.flatMap((res) => res.findings);

  const filteredFindings =
    selectedSeverity === 'all'
      ? allFindings
      : allFindings.filter((f) => f.severity === selectedSeverity);

  const handleCopyFix = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getSeverityBadgeClass = (sev: Severity) => {
    switch (sev) {
      case 'critical':
        return 'sev-critical';
      case 'high':
        return 'sev-high';
      case 'medium':
        return 'sev-medium';
      case 'low':
        return 'sev-low';
    }
  };

  return (
    <div className="card findings-section-card">
      <div className="section-header-flex">
        <div>
          <h3 className="section-title">Audit Findings & Proof</h3>
          <p className="section-subtitle">
            Page-level evidence and copy-paste ready technical fixes.
          </p>
        </div>

        <div className="filter-tabs">
          <button
            type="button"
            className={`tab-btn ${selectedSeverity === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedSeverity('all')}
          >
            All ({allFindings.length})
          </button>
          <button
            type="button"
            className={`tab-btn ${selectedSeverity === 'critical' ? 'active' : ''}`}
            onClick={() => setSelectedSeverity('critical')}
          >
            Critical ({allFindings.filter((f) => f.severity === 'critical').length})
          </button>
          <button
            type="button"
            className={`tab-btn ${selectedSeverity === 'high' ? 'active' : ''}`}
            onClick={() => setSelectedSeverity('high')}
          >
            High ({allFindings.filter((f) => f.severity === 'high').length})
          </button>
          <button
            type="button"
            className={`tab-btn ${selectedSeverity === 'medium' ? 'active' : ''}`}
            onClick={() => setSelectedSeverity('medium')}
          >
            Medium ({allFindings.filter((f) => f.severity === 'medium').length})
          </button>
        </div>
      </div>

      <div className="findings-list">
        {filteredFindings.map((finding) => (
          <div key={finding.id} className="finding-item-card">
            <div className="finding-item-header">
              <div className="finding-title-group">
                <ShieldAlertIcon className={`icon-md ${getSeverityBadgeClass(finding.severity)}-icon`} />
                <h4 className="finding-title">{finding.title}</h4>
              </div>

              <div className="finding-badges">
                <span className={`badge-severity ${getSeverityBadgeClass(finding.severity)}`}>
                  {finding.severity.toUpperCase()} SEVERITY
                </span>
                <span className={`badge-confidence conf-${finding.confidence}`}>
                  {finding.confidence.toUpperCase()} CONFIDENCE
                </span>
              </div>
            </div>

            {finding.page_url && (
              <div className="finding-url">
                <span className="url-label">Target Page:</span>
                <a href={finding.page_url} target="_blank" rel="noopener noreferrer" className="url-link">
                  {finding.page_url} <ExternalLinkIcon className="icon-xs inline" />
                </a>
              </div>
            )}

            <div className="finding-section">
              <div className="finding-section-label">Evidence / Observation:</div>
              <pre className="evidence-block">
                <code>{finding.evidence}</code>
              </pre>
            </div>

            <div className="finding-section">
              <div className="finding-section-label">Why it Matters for AI Visibility:</div>
              <p className="why-text">{finding.why_it_matters}</p>
            </div>

            <div className="finding-fix-box">
              <div className="fix-box-header">
                <span className="fix-label font-bold text-emerald-400">⚡ Recommended Fix (Copy-Paste Ready)</span>
                <button
                  type="button"
                  className="btn btn-copy"
                  onClick={() => handleCopyFix(finding.id, finding.recommended_fix)}
                >
                  {copiedId === finding.id ? (
                    <>
                      <CheckIcon className="icon-xs text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <CopyIcon className="icon-xs" />
                      Copy Fix
                    </>
                  )}
                </button>
              </div>
              <pre className="fix-code-block">
                <code>{finding.recommended_fix}</code>
              </pre>
            </div>
          </div>
        ))}

        {filteredFindings.length === 0 && (
          <div className="empty-findings">No findings matched the selected severity filter.</div>
        )}
      </div>
    </div>
  );
};
