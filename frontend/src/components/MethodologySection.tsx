import React from 'react';
import type { Limitation } from '../types/audit';
import { InfoIcon, CheckCircleIcon, AlertCircleIcon } from './Icons';

interface MethodologySectionProps {
  strengths: string[];
  limitations: Limitation[];
  pagesAnalyzed: string[];
}

export const MethodologySection: React.FC<MethodologySectionProps> = ({
  strengths,
  limitations,
  pagesAnalyzed
}) => {
  return (
    <div className="card methodology-card">
      <h3 className="section-title">Methodology & Audit Scope</h3>
      <p className="section-subtitle">
        Transparent audit boundaries, evaluated pages, and system limitations.
      </p>

      <div className="methodology-grid">
        <div className="methodology-column">
          <div className="column-header">
            <div className="methodology-icon-wrapper">
              <CheckCircleIcon className="methodology-icon text-emerald-400" />
            </div>
            <h4 className="column-title">Verified Strengths</h4>
          </div>
          <ul className="strengths-list">
            {strengths.map((str, idx) => (
              <li key={idx} className="strength-item">
                <span className="bullet-dot bg-emerald-400"></span>
                <span>{str}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="methodology-column">
          <div className="column-header">
            <div className="methodology-icon-wrapper">
              <AlertCircleIcon className="methodology-icon text-amber-400" />
            </div>
            <h4 className="column-title">Scope & Limitations</h4>
          </div>
          <ul className="limitations-list">
            {limitations.map((lim, idx) => (
              <li key={idx} className="limitation-item">
                <span className="bullet-dot bg-amber-400"></span>
                <span>{lim.description}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="pages-analyzed-box">
        <div className="box-title flex items-center gap-2">
          <InfoIcon className="icon-xs text-sky-400" /> Pages Analyzed in this Crawl Scope:
        </div>
        <ul className="pages-list font-mono text-xs">
          {pagesAnalyzed.map((p, idx) => (
            <li key={idx}>• {p}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
