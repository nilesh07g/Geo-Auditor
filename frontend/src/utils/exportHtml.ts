import type { AuditResponse } from '../types/audit';

export function exportReportAsHtml(data: AuditResponse) {
  const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GEO Audit Report - ${data.business_name || data.url}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }
    .container { max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 2rem; border: 1px solid #334155; }
    h1 { color: #38bdf8; margin-top: 0; }
    .hero-score { font-size: 3rem; font-weight: bold; color: #10b981; margin: 1rem 0; }
    .grade { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; background: #991b1b; color: #fecaca; font-weight: bold; }
    .card { background: #0f172a; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #334155; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { text-align: left; padding: 0.75rem; border-bottom: 1px solid #334155; }
    th { color: #94a3b8; }
    pre { background: #020617; padding: 1rem; border-radius: 6px; overflow-x: auto; color: #38bdf8; }
    .sev-critical { color: #ef4444; font-weight: bold; }
    .sev-high { color: #f97316; font-weight: bold; }
    .sev-medium { color: #eab308; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <h1>GEO Visibility Audit</h1>
    <p><strong>Target:</strong> ${data.url} (${data.business_name || 'N/A'})</p>
    <p><strong>Audited At:</strong> ${new Date(data.audited_at).toLocaleString()}</p>
    
    <div class="card">
      <h2>Executive Score: <span class="hero-score">${data.geo_score}/100</span> <span class="grade">${data.grade}</span></h2>
      <p><strong>Verdict:</strong> ${data.executive_summary}</p>
      <p><strong>Aha Line:</strong> ${data.aha_line}</p>
    </div>

    <div class="card">
      <h3>Score Breakdown</h3>
      <table>
        <thead>
          <tr>
            <th>Check</th>
            <th>Raw Score</th>
            <th>Weight</th>
            <th>Weighted Points</th>
          </tr>
        </thead>
        <tbody>
          ${data.score_breakdown
            .map(
              (item) => `
            <tr>
              <td>${item.check_name}</td>
              <td>${item.score}/${item.max_score}</td>
              <td>${item.weight}%</td>
              <td>+${item.weighted_score} pts</td>
            </tr>
          `
            )
            .join('')}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>Audit Findings (${data.check_results.flatMap((r) => r.findings).length} issues)</h3>
      ${data.check_results
        .flatMap((r) => r.findings)
        .map(
          (f) => `
        <div style="border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 1rem;">
          <h4 class="sev-${f.severity}">${f.title} [${f.severity.toUpperCase()}]</h4>
          <p><strong>Evidence:</strong></p>
          <pre>${f.evidence}</pre>
          <p><strong>Why it matters:</strong> ${f.why_it_matters}</p>
          <p><strong>Fix:</strong></p>
          <pre>${f.recommended_fix}</pre>
        </div>
      `
        )
        .join('')}
    </div>
  </div>
</body>
</html>`;

  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `GEO_Audit_${(data.business_name || 'report').replace(/\s+/g, '_')}.html`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
