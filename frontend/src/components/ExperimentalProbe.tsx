import React, { useState } from 'react';
import type { AIVisibilityResponse } from '../types/audit';
import { mockAIVisibilityData } from '../data/mockAudit';
import { SparklesIcon, AlertCircleIcon } from './Icons';

interface ExperimentalProbeProps {
  businessName?: string;
  url?: string;
}

export const ExperimentalProbe: React.FC<ExperimentalProbeProps> = ({
  businessName = 'Acme Plumbing Services'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<AIVisibilityResponse | null>(null);

  const handleRunProbe = () => {
    setIsLoading(true);
    setTimeout(() => {
      setData(mockAIVisibilityData);
      setIsLoading(false);
      setIsOpen(true);
    }, 1200);
  };

  return (
    <div className="card experimental-card">
      <div className="experimental-banner">
        <div className="banner-left">
          <SparklesIcon className="icon-md text-amber-400" />
          <div>
            <h3 className="experimental-title">Check 5: Live AI Visibility Probe</h3>
            <span className="experimental-tag">EXPERIMENTAL • EXCLUDED FROM CORE SCORE</span>
          </div>
        </div>

        {!data && (
          <button
            type="button"
            className="btn btn-experimental"
            onClick={handleRunProbe}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span> Querying Gemini API...
              </>
            ) : (
              <>Run Experimental AI Probe</>
            )}
          </button>
        )}
      </div>

      <p className="experimental-desc">
        Probes live AI answer engines (Gemini 2.5 Flash) with natural queries to evaluate whether{' '}
        <strong>{businessName}</strong> is actively cited or recommended in real-time answers.
      </p>

      {isOpen && data && (
        <div className="probe-results-container">
          <div className="probe-note">
            <AlertCircleIcon className="icon-xs text-amber-400 inline" /> {data.note}
          </div>

          <div className="probe-grid">
            {data.results.map((res, idx) => (
              <div key={idx} className="probe-item-card">
                <div className="probe-prompt">
                  <strong>Query #{idx + 1}:</strong> "{res.prompt}"
                </div>

                <div className="probe-status-row">
                  <span className={`probe-status-tag ${res.mentioned ? 'status-yes' : 'status-no'}`}>
                    Mentioned: {res.mentioned ? 'YES' : 'NO'}
                  </span>
                  <span className={`probe-status-tag ${res.cited ? 'status-yes' : 'status-no'}`}>
                    Cited URL: {res.cited ? 'YES' : 'NO'}
                  </span>
                </div>

                <div className="probe-excerpt">
                  <div className="excerpt-label">AI Response Excerpt:</div>
                  <blockquote className="excerpt-quote">"{res.response_excerpt}"</blockquote>
                </div>

                {res.competitors_mentioned.length > 0 && (
                  <div className="competitors-box">
                    <span className="comp-label">Competitors Cited in AI Answer:</span>
                    <div className="comp-tags">
                      {res.competitors_mentioned.map((comp, i) => (
                        <span key={i} className="comp-tag font-mono">
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
