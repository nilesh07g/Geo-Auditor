import { useState, useEffect } from 'react';
import { UrlInput } from './components/UrlInput';
import { AuditProgress } from './components/AuditProgress';
import { ScoreHero } from './components/ScoreHero';
import { ScoreBreakdown } from './components/ScoreBreakdown';
import { FindingCard } from './components/FindingCard';
import { ActionPlan } from './components/ActionPlan';
import { MethodologySection } from './components/MethodologySection';
import { ExperimentalProbe } from './components/ExperimentalProbe';
import { mockAuditData } from './data/mockAudit';
import type { AuditResponse } from './types/audit';
import { exportReportAsHtml } from './utils/exportHtml';
import { SparklesIcon, SearchIcon } from './components/Icons';
import './index.css';

// API base URL - use environment variable or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function App() {
  const [viewState, setViewState] = useState<'input' | 'loading' | 'report'>('input');
  const [loadingStep, setLoadingStep] = useState(0);
  const [auditData, setAuditData] = useState<AuditResponse>(mockAuditData);
  const [isApiAvailable, setIsApiAvailable] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Check API availability on component mount
  useEffect(() => {
    const checkApiAvailability = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          setIsApiAvailable(true);
          console.log('✅ API is available at', API_BASE_URL);
        } else {
          setIsApiAvailable(false);
          setApiError(`API health check failed: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        setIsApiAvailable(false);
        setApiError(`API not available at ${API_BASE_URL}: ${error instanceof Error ? error.message : 'Network error'}`);
        console.warn('API health check failed:', error);
      }
    };

    checkApiAvailability();
  }, [API_BASE_URL]);

  const handleAnalyze = async (url: string, businessName: string) => {
    setViewState('loading');
    setLoadingStep(0);
    setApiError(null);

    if (!isApiAvailable) {
      setApiError('API is not available. Using mock data for demo.');
      // Fallback to mock data with provided URL
      const interval = setInterval(() => {
        setLoadingStep((prev) => {
          if (prev >= 5) {
            clearInterval(interval);
            setAuditData({
              ...mockAuditData,
              url,
              business_name: businessName || mockAuditData.business_name,
              audited_at: new Date().toISOString()
            });
            setViewState('report');
            return 5;
          }
          return prev + 1;
        });
      }, 600);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          business_name: businessName
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // Success - set audit data
      setAuditData(data);
      setViewState('report');

    } catch (error) {
      // API error - fallback to mock data
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setApiError(`API error: ${errorMessage}. Using mock data for demo.`);
      console.warn('API call failed, falling back to mock data:', error);

      // Simulate loading then use mock data
      const interval = setInterval(() => {
        setLoadingStep((prev) => {
          if (prev >= 5) {
            clearInterval(interval);
            setAuditData({
              ...mockAuditData,
              url,
              business_name: businessName || mockAuditData.business_name,
              audited_at: new Date().toISOString()
            });
            setViewState('report');
            return 5;
          }
          return prev + 1;
        });
      }, 600);
    }
  };

  const handleNewAudit = () => {
    setViewState('input');
    setAuditData(mockAuditData); // Reset to mock data for new audit
  };

  const handleExportHtml = () => {
    exportReportAsHtml(auditData);
  };

  const handlePrintPdf = () => {
    window.print();
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-container">
          <div className="brand-logo" onClick={handleNewAudit} style={{ cursor: 'pointer' }}>
            <div className="brand-icon">
              <SparklesIcon className="icon-md text-emerald-400" />
            </div>
            <div className="brand-text">
              <span className="brand-title">GEO Auditor</span>
              <span className="brand-tagline">Generative Engine Optimization</span>
            </div>
          </div>

          <div className="header-actions">
            <span className={`status-badge-live ${!isApiAvailable ? 'status-badge-offline' : ''}`}>
              <span className="live-dot"></span>
              {isApiAvailable ? 'Deterministic Scoring Engine v1.0' : 'Demo Mode (API Offline)'}
            </span>

            {viewState === 'report' && (
              <button type="button" className="btn btn-primary btn-sm" onClick={handleNewAudit}>
                <SearchIcon className="icon-xs" />
                Audit Another URL
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="app-main-content">
        {viewState === 'input' && (
          <div className="view-container input-view">
            {!isApiAvailable && (
              <div className="api-warning-banner">
                <div className="warning-content">
                  <strong>⚠️ API Offline</strong> {apiError || 'Running in demo mode with mock data'}
                </div>
              </div>
            )}
            <UrlInput onAnalyze={handleAnalyze} isLoading={!isApiAvailable} />
          </div>
        )}

        {viewState === 'loading' && (
          <div className="view-container loading-view">
            <AuditProgress step={loadingStep} currentMessage="Analyzing website..." />
          </div>
        )}

        {viewState === 'report' && (
          <div className="view-container report-view">
            {apiError && (
              <div className="api-warning-banner-small">
                <small>⚠️ Using fallback data - API was unavailable</small>
              </div>
            )}

            <ScoreHero
              data={auditData}
              onExportHtml={handleExportHtml}
              onPrintPdf={handlePrintPdf}
            />

            <ScoreBreakdown
              items={auditData.score_breakdown}
              totalScore={auditData.geo_score}
            />

            <FindingCard checkResults={auditData.check_results} />

            <ActionPlan items={auditData.action_plan} />

            <ExperimentalProbe
              businessName={auditData.business_name}
              url={auditData.url}
            />

            <MethodologySection
              strengths={auditData.strengths}
              limitations={auditData.limitations}
              pagesAnalyzed={auditData.pages_analyzed}
            />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-container">
          <p>GEO Auditor • Built based on PROJECT_BLUEPRINT.md single source of truth</p>
          <p className="footer-sub">
            4 Core Deterministic Checks • Scope: Up to 3 Pages Crawled Per Business
          </p>
          <p className="footer-sub">
            API: {isApiAvailable ? 'Online' : 'Offline (Demo Mode)'} • Base URL: {API_BASE_URL}
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
