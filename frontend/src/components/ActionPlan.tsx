import React from 'react';
import type { ActionPlanItem } from '../types/audit';

interface ActionPlanProps {
  items: ActionPlanItem[];
}

export const ActionPlan: React.FC<ActionPlanProps> = ({ items }) => {
  return (
    <div className="card action-plan-card">
      <div className="section-header">
        <div>
          <h3 className="section-title">Prioritized Action Plan</h3>
          <p className="section-subtitle">
            Ranked by expected Impact vs. Implementation Effort for maximum ROI.
          </p>
        </div>
      </div>

      <div className="action-plan-list">
        {items.map((item) => (
          <div key={item.rank} className="action-plan-item">
            <div className="rank-badge">#{item.rank}</div>
            <div className="action-body">
              <div className="action-text">{item.action}</div>
              {item.source_finding_title && (
                <div className="source-title font-mono text-xs text-gray-400 mt-1">
                  Source: {item.source_finding_title}
                </div>
              )}
            </div>
            <div className="action-tags">
              <span className={`tag-impact impact-${item.impact}`}>
                Impact: {item.impact.toUpperCase()}
              </span>
              <span className={`tag-effort effort-${item.effort}`}>
                Effort: {item.effort.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
