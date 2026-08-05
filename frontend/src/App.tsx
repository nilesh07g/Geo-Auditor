import { useState } from 'react';
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

export function App() {
  const [viewState, setViewState] = useState<'input' | 'loading' | 'report'>('input');
  const [loadingStep, setLoadingStep] = useState(0);
  const [auditData, setAuditData] = useState<AuditResponse>(mockAuditData);

  const handleAnalyze = (url: string, businessName: string) => {
    setViewState('loading');
    setLoadingStep(0);

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
  };

  const handleNewAudit = () => {
    setViewState('input');
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
            <span className="status-badge-live">
              <span className="live-dot"></span>
              Deterministic Scoring Engine v0.1
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
            <UrlInput onAnalyze={handleAnalyze} isLoading={false} />
          </div>
        )}

        {viewState === 'loading' && (
          <div className="view-container loading-view">
            <AuditProgress step={loadingStep} currentMessage="" />
          </div>
        )}

        {viewState === 'report' && (
          <div className="view-container report-view">
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
        </div>
      </footer>
    </div>
  );
}

export default App;
