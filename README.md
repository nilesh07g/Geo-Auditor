# GEO Auditor: AI Extraction Readiness Assessment

## Live Deployment

- **Frontend:** [geo-auditor-frontend.vercel.app](https://geo-auditor-frontend.vercel.app)
- **Backend API docs:** [geo-auditor-kappa.vercel.app/docs](https://geo-auditor-kappa.vercel.app/docs)
- **Backend health:** [geo-auditor-kappa.vercel.app/health](https://geo-auditor-kappa.vercel.app/health)

## Introduction

In an era dominated by large language models (LLMs) and generative AI, a business's online visibility extends beyond traditional search engine rankings. AI engines now actively extract, synthesize, and present information directly to users, often citing or referencing businesses in their responses. This shift introduces a new frontier in digital presence: **Generative Engine Optimization (GEO)**.

The GEO Auditor is a specialized tool designed to assess a business website's readiness for optimal AI extraction. It evaluates key signals that influence how accurately and comprehensively AI models can understand, categorize, and represent a business in AI-generated answers and knowledge graphs. This report serves as both a technical audit and a strategic blueprint for enhancing AI visibility.

## The Problem Being Solved

Traditional SEO focuses on ranking in web search results. However, AI models often bypass these results, generating direct answers. If a business's website isn't structured to facilitate AI extraction, it risks:
- **Invisibility in AI answers:** AI may fail to identify or mention the business.
- **Inaccurate representation:** AI may misinterpret business details, services, or unique value propositions.
- **Missed citation opportunities:** AI might cite competitors that provide clearer, AI-friendly signals.
- **Reduced knowledge graph presence:** AI's foundational understanding of the business is incomplete.

The GEO Auditor addresses this by proactively identifying structural, content, and technical gaps that hinder AI's ability to "read" and comprehend a website effectively.

## Why This Product Was Built This Way

The design of the GEO Auditor prioritizes **determinism, speed, and actionable insights** for small to medium-sized businesses (SMBs).

1.  **Deterministic Scoring:** Unlike subjective human audits, the GEO Auditor employs a fixed set of four checks with clear scoring rubrics. This ensures consistent, repeatable results, making it suitable for automated pipelines and objective performance tracking.
2.  **Lightweight Crawl Scope (3 Pages):** The audit is intentionally scoped to the homepage, a detected "About" page, and one detected "Service/Product" page.
    *   **Reasoning:** For most SMBs, critical entity-defining information, primary service offerings, and contact details are concentrated on these core pages. A deep, recursive crawl (like a traditional SEO crawler) would be excessive for a rapid, initial GEO assessment and introduce unnecessary complexity and computational cost.
    *   **Trade-off:** This limits the depth of content analysis, potentially missing issues on deeper pages. However, the goal is to provide high-impact recommendations quickly for the most critical AI signals.
3.  **Fast HTTP Fetching:** Utilizing `httpx` with aggressive timeouts and a modern User-Agent ensures efficient page retrieval, minimizing latency and handling common SMB website quirks (e.g., legacy SSL, basic WAFs).
4.  **Focused HTML Parsing:** `BeautifulSoup` and targeted regex are used for precise extraction of titles, headings, meta descriptions, JSON-LD, and clean body text. This avoids the overhead of a full browser rendering engine, which is often overkill for server-side HTML analysis relevant to AI crawlers.
5.  **Python-based Backend (FastAPI):** Python offers a robust ecosystem for web scraping, NLP, and data processing. FastAPI provides a high-performance, developer-friendly framework for building the API, complete with automatic documentation.

## Why These Specific GEO Checks Were Chosen

The four implemented checks represent the most impactful and universally applicable signals for AI extraction across diverse business types. Each targets a critical aspect of AI comprehension:

1.  **Check 1: AI Crawler Access (Weight: 20%)**
    *   **Problem:** If AI bots can't access your site, no other optimization matters.
    *   **Justification:** This check verifies `robots.txt` and `llms.txt` configurations, and meta robot tags. `robots.txt` is fundamental for bot access, while `llms.txt` (per llmstxt.org) is an emerging standard for explicitly guiding LLMs. Absence of `noindex`/`noai` meta tags ensures content isn't explicitly hidden from AI. A strong score here means foundational visibility is established.
    *   **Deterministic:** Rules for `robots.txt` parsing and meta tag detection are unambiguous.
    *   **Scoring:** Scores higher for explicit `Allow` rules for AI bots, and for the presence of a well-formed `llms.txt`. Missing `robots.txt` is treated as a default allow but noted as a low severity finding because explicit declaration is preferred for signaling intent to AI engines.

2.  **Check 2: Entity Clarity (Weight: 25%)**
    *   **Problem:** AI needs to understand "who you are, what you do, and where you do it."
    *   **Justification:** This check focuses on how clearly the business entity is defined. It assesses the presence and quality of definitional statements in H1 headings and opening paragraphs, the completeness of `Organization`/`LocalBusiness` JSON-LD schema, the presence of a dedicated "About" page, and the consistency of Name, Address, Phone (NAP) information. These are primary signals for AI knowledge graph construction and accurate business categorization.
    *   **Heuristic + Deterministic:** Combines deterministic schema checks with heuristic content analysis for definitional sentences.
    *   **Scoring:** Rewards explicit, clear H1s, comprehensive JSON-LD, a well-formed "About" page, and complete NAP.

3.  **Check 3: Structured Data for AI Extraction (Weight: 25%)**
    *   **Problem:** Unstructured text is ambiguous for AI; structured data is explicit.
    *   **Justification:** This check verifies the implementation of JSON-LD schema, which is machine-readable data designed to provide explicit context to search engines and AI. It looks for expected schema types (e.g., `LocalBusiness`, `Service`, `FAQPage`) relevant to the inferred business category. Correctly implemented structured data significantly boosts AI's ability to extract facts, services, and answer common questions about the business.
    *   **Deterministic:** Based on the presence and validity of JSON-LD blocks.
    *   **Scoring:** Awards points for finding expected schema types and identifying schemas with minimal validation issues.

4.  **Check 4: Answer-Ready Content Structure (Weight: 30%)**
    *   **Problem:** Generic, marketing-heavy content provides little factual data for AI to cite.
    *   **Justification:** AI thrives on factual, concise, and structured information that directly answers potential user queries. This check evaluates the clarity of definitional sentences, the presence of FAQ-style content (often directly answerable), the detection of specific, measurable facts (e.g., years in business, service areas, employee count), and the absence of vague marketing filler. This check is given the highest weight due to the direct correlation between answer-ready content and AI citation potential.
    *   **Heuristic:** Primarily relies on NLP heuristics to analyze content quality and fact density.
    *   **Scoring:** Penalizes vague marketing copy and rewards clear, factual statements, and FAQ-like content.

## Why Other Checks Were Intentionally NOT Built

During development, several potential checks were considered and deliberately omitted to maintain focus, optimize for SMB impact, and avoid introducing unnecessary complexity:

*   **Deep Content NLP for Sentiment/Tone:** While interesting, analyzing sentiment or tone (e.g., "authoritative voice") is highly subjective for an automated system and less directly correlated with *extractability* of core business facts. It would also add significant computational cost and potential for false positives.
*   **Backlink/Domain Authority Analysis:** These are traditional SEO metrics, crucial for ranking, but less directly relevant to how AI *understands* the content of a specific website once crawled. Our focus is on on-page signals for AI comprehension.
*   **Image/Video Analysis:** Identifying alt-text, captions, or video transcripts *is* valuable for AI. However, performing comprehensive image OCR or video transcription is computationally intensive and outside the scope of a lightweight, fast-executing audit designed for quick insights. This could be a future enhancement.
*   **Competitor AI Visibility Comparison:** While a compelling product feature, directly comparing a business's AI visibility against competitors requires a much larger data pipeline, continuous monitoring, and more sophisticated AI probing capabilities (like the `ai-visibility` endpoint, currently a placeholder). This moves beyond a single-site audit.

## Trade-offs Made and Why

1.  **Crawl Depth vs. Speed/Cost:** Limiting the crawl to three key pages sacrifices a comprehensive site-wide analysis for rapid execution and lower resource usage. This is a deliberate choice for an initial, high-impact assessment, suitable for agencies managing many SMB clients.
2.  **Heuristic vs. Pure Determinism:** While the audit strives for determinism, checks like "Entity Clarity" and "Answer-Ready Content" necessarily rely on NLP heuristics (e.g., keyword patterns for definitions, fact detection). This introduces a degree of "softness" compared to purely technical checks.
    *   **Reasoning:** AI comprehension itself is heuristic-driven. To assess "AI readiness," the auditor must emulate AI's understanding, which often involves pattern matching in natural language. Pure determinism here would miss crucial content quality signals.
    *   **Mitigation:** Findings from heuristic checks are assigned "Medium" confidence, acknowledging their interpretative nature, contrasting with "High" confidence for deterministic checks (e.g., `robots.txt` parsing, JSON-LD presence).
3.  **Basic Business Category Inference:** The tool currently defaults to "local\_service" for structured data expectations. A more advanced system would use NLP to infer the business category from site content.
    *   **Trade-off:** Simplifies the logic and keeps the audit fast.
    *   **Impact:** May occasionally recommend schema types less perfectly aligned if the business is clearly SaaS or e-commerce but still provides broadly useful advice.

## Assumptions Made

*   **Publicly Accessible Websites:** The auditor assumes the target URL is publicly accessible via HTTP/HTTPS and does not require authentication.
*   **Standard HTML/CSS:** The auditor primarily parses server-rendered HTML. While it detects JavaScript shells, it does not execute JavaScript to render dynamic content.
*   **English Language Content:** NLP heuristics are optimized for English content.
*   **Standard URL Structures:** The logic for discovering "About" and "Service" pages relies on common URL patterns and link text.
*   **Local Service Business Focus:** While generally applicable, some recommendations (e.g., `LocalBusiness` schema) are tailored towards local service businesses, reflecting a common client profile for such an auditor.

## How the Scoring Works

The GEO score is a weighted average out of 100, calculated from the four core checks.

1.  **Individual Check Scores:** Each check (`AI Crawler Access`, `Entity Clarity`, `Structured Data`, `Answer-Ready Content`) has its own maximum score (e.g., 20, 25, 25, 30 points respectively). Points are awarded based on the findings within that check.
2.  **Weights:** Each check is assigned a weight, reflecting its relative importance to overall AI visibility. These weights sum to 100:
    *   AI Crawler Access: 20%
    *   Entity Clarity: 25%
    *   Structured Data: 25%
    *   Answer-Ready Content: 30%
3.  **Weighted Score Calculation:**
    *   `Weighted Score for Check = (Raw Score for Check / Max Score for Check) * Check Weight`
    *   Example: If "AI Crawler Access" (max 20 pts, weight 20%) gets a raw score of 15, its weighted contribution is `(15/20) * 20 = 15` points.
4.  **Overall GEO Score:** The sum of all weighted scores, normalized to a total out of 100.
5.  **Grade:** A categorical grade (`Strong`, `Moderate gaps`, `At Risk`, `Critical`) is assigned based on the overall numeric score, providing a quick, intuitive summary of AI readiness.

This weighting emphasizes content quality (Answer-Ready Content) and explicit entity definition (Entity Clarity, Structured Data), as these directly feed AI's ability to generate accurate answers.

## Architecture and Workflow

The project follows a standard client-server architecture:

```
+------------------+
|      Client      |
| (React/Vite      |
|    Frontend)     |
+--------+---------+
         |
         | HTTP/JSON (AuditRequest)
         v
+------------------+
|    FastAPI       |
|    Backend       |
| (main.py)        |
+--------+---------+
         |
         | (Delegates to)
         v
+------------------+     +-----------------+     +-----------------+
|  HTTP Fetcher    |---->| HTML Parser     |---->| Individual GEO  |
| (fetcher.py)     |     | (parser.py)     |     | Checks          |
|                  |     |                 |     | (checks/*.py)   |
| (Crawls URL,     |     | (Extracts data, |     |                 |
| robots.txt,       |     | JSON-LD, text)  |     | (Generates      |
| llms.txt, pages) |     |                 |     | findings, scores)|
+------------------+     +-----------------+     +-----------------+
         ^                                               |
         | (CrawlResult)                                 | (CheckResult List)
         +-----------------------------------------------|
                                         |
                                         v
                                 +-----------------+
                                 | Scoring Engine  |
                                 | (scoring.py)    |
                                 |                 |
                                 | (Calculates     |
                                 | weighted score, |
                                 | grade)          |
                                 +-----------------+
                                         |
                                         | (AuditResponse)
                                         v
                               +------------------+
                               |    FastAPI       |
                               |    Backend       |
                               | (main.py)        |
                               | (Generates       |
                               | summary, plan)   |
                               +------------------+
                                         |
                                         | HTTP/JSON (AuditResponse)
                                         v
                               +------------------+
                               |      Client      |
                               | (Frontend UI)    |
                               |                  |
                               +------------------+
```

1.  **Request Initiation:** The React/Vite frontend sends an `AuditRequest` (containing a URL and optional business name) to the `/api/audit` endpoint of the FastAPI backend.
2.  **Site Crawling:** The `fetcher.py` module, leveraging `httpx`, performs a targeted crawl:
    *   Fetches `robots.txt` and `llms.txt`.
    *   Fetches the homepage.
    *   Analyzes homepage links to discover and fetch "About" and one "Service/Product" page.
    *   Returns a `CrawlResult` containing raw HTML, parsed data, and any crawling limitations.
3.  **HTML Parsing:** For each fetched page, `parser.py` (using `BeautifulSoup4`) extracts structured content:
    *   Page title, meta description, H1/H2 headings.
    *   All JSON-LD structured data.
    *   Cleaned body text (stripped of boilerplate, scripts, styles).
    *   Navigation links for discovery.
    *   Detects if the page is a JavaScript-rendered shell.
4.  **Check Execution:** Each of the four checks (`crawler_access.py`, `entity_clarity.py`, `structured_data.py`, `answer_ready.py`) processes the `CrawlResult` data.
    *   Each check evaluates specific GEO signals.
    *   Assigns a raw score and generates `Finding` objects (title, severity, confidence, evidence, why it matters, recommended fix).
5.  **Scoring and Reporting:** `scoring.py` aggregates the `CheckResult` from all checks:
    *   Calculates the weighted overall GEO score (0-100).
    *   Assigns a letter grade.
    *   `main.py` then constructs the final `AuditResponse`:
        *   Generates a concise executive summary and a critical "Aha Line."
        *   Compiles a prioritized action plan from all findings (deduplicated, sorted by severity).
        *   Lists strengths and crawling limitations.
6.  **Response:** The `AuditResponse` is returned to the client, providing a comprehensive report of the website's AI extraction readiness.

## How to Run the Project in Under 5 Minutes

This project consists of a Python FastAPI backend and a React/Vite frontend.

### 1. Clone the repository:
```bash
git clone https://github.com/nilesh07g/PHASE-AI-ASSGN.git
cd PHASE-AI-ASSGN
```

### 2. Set up and run the Backend (API):

Navigate to the `backend` directory:
```bash
cd backend
```
Set up Python environment:
```bash
# Create a virtual environment
python -m venv venv
# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
Install backend dependencies:
```bash
pip install -r requirements.txt
```
Run the FastAPI server:
```bash
uvicorn main:app --reload
```
The backend API will be accessible at `http://127.0.0.1:8000`. You can access its interactive documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

### 3. Set up and run the Frontend (UI):

Open a new terminal window and navigate back to the project root, then into the `frontend` directory:
```bash
cd ..
cd frontend
```
Install frontend dependencies:
```bash
npm install
```
Run the React development server:
```bash
npm run dev
```
The frontend application will typically open in your browser at `http://localhost:5173` (or another available port). This UI interacts with the FastAPI backend.


## Current Limitations

1.  **Limited Crawl Depth:** The audit is strictly limited to 3 content pages (homepage, about, one service/product page), plus `robots.txt` and `llms.txt`. This is a design choice for speed but means issues on deeper pages are not detected.
2.  **No JavaScript Rendering:** The HTML parser only processes the initial server-delivered HTML. Websites heavily reliant on client-side JavaScript for content rendering (Single Page Applications - SPAs) may result in incomplete analysis, as the auditor does not execute JavaScript.
3.  **Basic Business Category Inference:** The `structured_data` check currently infers "local\_service" as a default business category. A more sophisticated NLP model would be needed for accurate multi-category classification.
4.  **Static Check Weights:** The weights for each GEO check are hardcoded. A more flexible system might allow dynamic weighting based on client needs or business type.
5.  **No Authentication/Authorization:** The API is publicly accessible. For production use, robust authentication and authorization mechanisms would be essential.
6.  **No Persistent Storage:** Audit results are not stored persistently in a database. Each API call is a fresh audit.
7.  **Placeholder AI Visibility Probe:** The `/api/audit/ai-visibility` endpoint is a placeholder, indicating an unimplemented future feature for live AI interaction.

## Future Improvements

1. **Enhance the Frontend Application:** Expand the existing React/Vite frontend with features such as authentication, audit history, interactive dashboards, report export (PDF/HTML), scheduled audits, and shareable reports to provide a more production-ready user experience.
2.  **Dynamic Crawl Depth Configuration:** Allow users to specify crawl depth (e.g., 5 pages, 10 pages) or define specific pages for auditing.
3.  **Headless Browser Integration:** Integrate a headless browser (e.g., Playwright, Puppeteer) to render JavaScript-heavy sites, enabling a more comprehensive analysis of SPAs. This would significantly improve accuracy for modern web applications.
4.  **Advanced Business Category Inference:** Implement an NLP model to accurately infer the business category (e.g., SaaS, E-commerce, Local Service, Non-profit) from website content, tailoring structured data and content expectations more precisely.
5.  **Custom Check Definitions:** Enable users or administrators to define custom GEO checks and their associated scoring logic.
6.  **Database Integration:** Implement persistent storage (e.g., PostgreSQL, MongoDB) for audit requests, results, and historical data, allowing for trend analysis and client management.
7.  **Authentication and User Management:** Secure the API with user authentication and role-based authorization.
8.  **Live AI Visibility Probe (LLM Integration):** Implement the experimental `/api/audit/ai-visibility` endpoint to query a live LLM (e.g., Gemini, GPT, Claude) with a summary of the site, asking "What do you know about [Business Name]?" to get real-time insights into AI's current understanding. This would be a powerful differentiator.
9.  **Scheduled Audits & Monitoring:** Allow users to schedule recurring audits and monitor changes in their GEO score over time.

## Sample Audit Reports

Located in the `examples/` folder, these HTML files demonstrate the output of the GEO Auditor:

*   **`examples/GEO_Audit_Mr._Electric(final).html`**: An audit of a local electrical service business.
*   **`examples/GEO_Audit_Benjamin_Franklin_Plumbing (final).html`**: An audit of a local plumbing service business.
*   **`examples/GEO_Audit_GitHub (final).html`**: An audit of GitHub, showcasing how a non-local-service business is scored and the types of findings it might receive.

These examples highlight the auditor's ability to identify actionable insights across different website types and demonstrate the professional report format.

