import React from 'react';
import { SearchIcon, CheckCircleIcon } from './Icons';

interface AuditProgressProps {
  step: number;
  currentMessage: string;
}

const STEPS = [
  'Fetching homepage & site navigation...',
  'Checking robots.txt & llms.txt crawler access...',
  'Extracting Organization & local entity schema...',
  'Parsing JSON-LD structured data...',
  'Evaluating answer-readiness & fact density...',
  'Calculating composite GEO score...'
];

export const AuditProgress: React.FC<AuditProgressProps> = ({ step, currentMessage }) => {
  const percentage = Math.min(Math.round(((step + 1) / STEPS.length) * 100), 100);

  return (
    <div className="card progress-card">
      <div className="progress-header">
        <div className="progress-title-group">
          <SearchIcon className="icon-md text-emerald-400 spinner-pulse" />
          <h3>Audit in Progress...</h3>
        </div>
        <span className="progress-percentage">{percentage}%</span>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar-fill" style={{ width: `${percentage}%` }}></div>
      </div>

      <div className="progress-message">{currentMessage || STEPS[Math.min(step, STEPS.length - 1)]}</div>

      <ul className="progress-steps-list">
        {STEPS.map((stepText, idx) => {
          const isDone = idx < step;
          const isCurrent = idx === step;
          return (
            <li
              key={idx}
              className={`progress-step-item ${
                isDone ? 'completed' : isCurrent ? 'active' : 'pending'
              }`}
            >
              {isDone ? (
                <CheckCircleIcon className="step-icon completed" />
              ) : isCurrent ? (
                <span className="step-spinner"></span>
              ) : (
                <span className="step-dot"></span>
              )}
              <span className="step-text">{stepText}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
