import React from 'react';
import type { AuditResponse } from '../types/audit';
import { ZapIcon, ExternalLinkIcon, DownloadIcon } from './Icons';

interface ScoreHeroProps {
  data: AuditResponse;
  onExportHtml?: () => void;
  onPrintPdf?: () => void;
}

export const ScoreHero: React.FC<ScoreHeroProps> = ({ data, onExportHtml, onPrintPdf }) => {
  const getGradeColorClass = (grade: string) => {
    switch (grade) {
      case 'Strong':
        return 'grade-strong';
      case 'Moderate gaps':
        return 'grade-moderate';
      case 'At Risk':
        return 'grade-risk';
      case 'Critical':
        return 'grade-critical';
      default:
        return 'grade-risk';
    }
  };

  const formattedDate = new Date(data.audited_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  return (
    <div className="card score-hero-card">
      <div className="score-hero-header">
        <div>
          <div className="domain-pill">
            <span>{data.business_name || data.url}</span>
            <a href={data.url} target="_blank" rel="noopener noreferrer" className="external-link">
              <ExternalLinkIcon className="icon-xs" />
            </a>
          </div>
          <div className="audit-meta">Audited on {formattedDate} • 3 Pages Analyzed</div>
        </div>

        <div className="action-buttons">
          {onExportHtml && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onExportHtml}>
              <DownloadIcon className="icon-xs" />
              Export HTML
            </button>
          )}
          {onPrintPdf && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onPrintPdf}>
              Print / Save PDF
            </button>
          )}
        </div>
      </div>

      <div className="score-hero-grid">
        <div className="score-badge-wrapper">
          <div className="score-circle">
            <svg viewBox="0 0 100 100" className="score-svg">
              <circle cx="50" cy="50" r="42" className="score-bg" />
              <circle
                cx="50"
                cy="50"
                r="42"
                className="score-progress"
                style={{
                  strokeDasharray: 264,
                  strokeDashoffset: 264 - (264 * data.geo_score) / 100
                }}
              />
            </svg>
            <div className="score-inner">
              <span className="score-value">{data.geo_score}</span>
              <span className="score-max">/ 100</span>
            </div>
          </div>
          <div className={`grade-badge ${getGradeColorClass(data.grade)}`}>
            {data.grade}
          </div>
        </div>

        <div className="summary-content">
          <h2 className="summary-title">Executive Summary</h2>
          <p className="summary-text">{data.executive_summary}</p>

          <div className="aha-callout-box">
            <div className="aha-icon-wrapper">
              <ZapIcon className="aha-icon" />
            </div>
            <div className="aha-body">
              <div className="aha-header">The Invisible Gap ("Aha" Line)</div>
              <div className="aha-text">{data.aha_line}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
