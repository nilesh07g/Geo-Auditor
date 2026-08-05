import React from 'react';
import type { ScoreBreakdownItem } from '../types/audit';
import { InfoIcon, CheckCircleIcon, AlertTriangleIcon } from './Icons';

interface ScoreBreakdownProps {
  items: ScoreBreakdownItem[];
  totalScore: number;
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({ items, totalScore }) => {
  return (
    <div className="card score-breakdown-card">
      <div className="section-header">
        <div>
          <h3 className="section-title">Score Breakdown</h3>
          <p className="section-subtitle">
            Calculated transparently from 4 deterministic technical checks.
          </p>
        </div>
        <div className="math-badge">
          <span>Weighted Sum: </span>
          <strong className="math-score">{totalScore} / 100</strong>
        </div>
      </div>

      <div className="table-responsive">
        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Check</th>
              <th>Raw Score</th>
              <th>Weight</th>
              <th>Weighted Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const scorePct = Math.round((item.score / item.max_score) * 100);
              const isGood = scorePct >= 75;
              const isWarning = scorePct >= 50 && scorePct < 75;

              return (
                <tr key={item.check_id}>
                  <td className="check-name-cell">
                    <strong>{item.check_name}</strong>
                  </td>
                  <td>
                    <span className="mono-text">
                      {item.score} / {item.max_score}
                    </span>
                  </td>
                  <td>
                    <span className="badge-weight">{item.weight}%</span>
                  </td>
                  <td>
                    <strong className="mono-text text-emerald-400">
                      +{item.weighted_score} pts
                    </strong>
                  </td>
                  <td>
                    {isGood ? (
                      <span className="status-tag tag-good">
                        <CheckCircleIcon className="icon-xs" /> Pass
                      </span>
                    ) : isWarning ? (
                      <span className="status-tag tag-warning">
                        <AlertTriangleIcon className="icon-xs" /> Gaps Found
                      </span>
                    ) : (
                      <span className="status-tag tag-critical">
                        <AlertTriangleIcon className="icon-xs" /> Action Required
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="deterministic-note">
        <InfoIcon className="deterministic-icon text-sky-400" />
        <span className="deterministic-text">
          <strong>Deterministic Guarantee:</strong> All scores above are generated using reproducible
          code logic and HTML/robots.txt extraction rules. No LLM APIs were used to compute these points.
        </span>
      </div>
    </div>
  );
};
