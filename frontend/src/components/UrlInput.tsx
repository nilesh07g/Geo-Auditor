import React, { useState } from 'react';
import { SearchIcon, SparklesIcon } from './Icons';

interface UrlInputProps {
  onAnalyze: (url: string, businessName: string) => void;
  isLoading: boolean;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onAnalyze, isLoading }) => {
  const [url, setUrl] = useState('');
  const [businessName, setBusinessName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onAnalyze(url.trim(), businessName.trim());
  };

  const handlePreset = (presetUrl: string, presetName: string) => {
    setUrl(presetUrl);
    setBusinessName(presetName);
    onAnalyze(presetUrl, presetName);
  };

  return (
    <div className="card hero-input-card">
      <div className="badge-pill">
        <SparklesIcon className="icon-sm" />
        <span>Generative Engine Optimization (GEO) Audit Tool</span>
      </div>

      <h1 className="hero-title">
        Are AI answer engines <span className="highlight-text">hiding your business</span>?
      </h1>
      <p className="hero-subtitle">
        Enter your website URL below to run a 4-check deterministic GEO audit. Get page-level evidence,
        a visible score breakdown, and copy-paste ready fixes.
      </p>

      <form onSubmit={handleSubmit} className="audit-form">
        <div className="form-group">
          <label htmlFor="url-input" className="form-label">
            Website URL <span className="required">*</span>
          </label>
          <div className="input-wrapper">
            <SearchIcon className="input-icon" />
            <input
              id="url-input"
              type="text"
              className="form-input"
              placeholder="e.g. https://acmeplumbing.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="business-name-input" className="form-label">
            Business Name <span className="optional">(Optional)</span>
          </label>
          <input
            id="business-name-input"
            type="text"
            className="form-input"
            placeholder="e.g. Acme Plumbing Services"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <button type="submit" className="btn btn-primary btn-lg" disabled={isLoading || !url.trim()}>
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Analyzing Website...
            </>
          ) : (
            <>
              <SearchIcon className="icon-md" />
              Run Free GEO Audit
            </>
          )}
        </button>
      </form>

      <div className="preset-section">
        <span className="preset-label">Or try a sample business:</span>
        <div className="preset-buttons">
          <button
            type="button"
            className="btn btn-preset"
            onClick={() => handlePreset('https://acmeplumbing.com', 'Acme Plumbing Services')}
            disabled={isLoading}
          >
            🔧 Acme Plumbing (Local Service)
          </button>
          <button
            type="button"
            className="btn btn-preset"
            onClick={() => handlePreset('https://cloudpulse.io', 'CloudPulse Tech')}
            disabled={isLoading}
          >
            ⚡ CloudPulse (B2B SaaS)
          </button>
        </div>
      </div>
    </div>
  );
};
