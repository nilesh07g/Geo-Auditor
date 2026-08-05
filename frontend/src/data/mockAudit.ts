import type { AuditResponse, AIVisibilityResponse } from '../types/audit';

export const mockAuditData: AuditResponse = {
  url: 'https://acmeplumbing.com',
  business_name: 'Acme Plumbing Services',
  audited_at: new Date().toISOString(),
  geo_score: 58,
  grade: 'At Risk',
  executive_summary:
    'Acme Plumbing ranks on traditional Google Search, but is largely invisible in AI answer engines like ChatGPT and Perplexity. Key crawlers like GPTBot are explicitly blocked, structured schema is missing on service pages, and copy lacks citeable facts.',
  aha_line:
    'You rank #1 on Google for "Plumber Austin", but ChatGPT omits you entirely because GPTBot is blocked in your robots.txt and your /about page lacks entity schema.',
  pages_analyzed: [
    'https://acmeplumbing.com',
    'https://acmeplumbing.com/about',
    'https://acmeplumbing.com/services/drain-cleaning',
    'https://acmeplumbing.com/robots.txt',
    'https://acmeplumbing.com/llms.txt (404 Not Found)'
  ],
  score_breakdown: [
    {
      check_id: 'crawler_access',
      check_name: 'AI Crawler Access',
      score: 8,
      max_score: 20,
      weight: 20,
      weighted_score: 8
    },
    {
      check_id: 'entity_clarity',
      check_name: 'Entity Clarity',
      score: 15,
      max_score: 25,
      weight: 25,
      weighted_score: 15
    },
    {
      check_id: 'structured_data',
      check_name: 'Structured Data',
      score: 12,
      max_score: 25,
      weight: 25,
      weighted_score: 12
    },
    {
      check_id: 'answer_ready',
      check_name: 'Answer-Ready Content',
      score: 23,
      max_score: 30,
      weight: 30,
      weighted_score: 23
    }
  ],
  check_results: [
    {
      check_id: 'crawler_access',
      check_name: 'AI Crawler Access',
      score: 8,
      max_score: 20,
      weight: 20,
      weighted_score: 8,
      findings: [
        {
          id: 'c1-1',
          check_id: 'crawler_access',
          title: 'GPTBot and PerplexityBot blocked in robots.txt',
          severity: 'critical',
          confidence: 'high',
          page_url: 'https://acmeplumbing.com/robots.txt',
          evidence: 'User-agent: GPTBot\nDisallow: /\nUser-agent: PerplexityBot\nDisallow: /',
          why_it_matters:
            'AI search engines cannot index or quote your website content when their crawler bots are explicitly blocked in robots.txt.',
          recommended_fix:
            '# Remove disallow rules for AI bots in robots.txt\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /'
        },
        {
          id: 'c1-2',
          check_id: 'crawler_access',
          title: 'No llms.txt standard file detected',
          severity: 'medium',
          confidence: 'high',
          page_url: 'https://acmeplumbing.com/llms.txt',
          evidence: 'HTTP 404 Not Found at /llms.txt',
          why_it_matters:
            'An llms.txt file provides a clean, Markdown-formatted summary of your business facts specifically curated for LLM context windows.',
          recommended_fix:
            '# Create /llms.txt on server root:\n# Acme Plumbing Services\n> Licensed residential & commercial plumbing in Austin, TX since 2004.\n\n## Core Services\n- Emergency Drain Cleaning ($150-$300)\n- Tankless Water Heater Installation\n- Sewer Line Camera Inspection\n\n## Service Area\nGreater Austin Metropolitan Area (78701, 78702, 78704)'
        }
      ]
    },
    {
      check_id: 'entity_clarity',
      check_name: 'Entity Clarity',
      score: 15,
      max_score: 25,
      weight: 25,
      weighted_score: 15,
      findings: [
        {
          id: 'c2-1',
          check_id: 'entity_clarity',
          title: 'Vague homepage H1 heading and missing explicit entity definition',
          severity: 'high',
          confidence: 'medium',
          page_url: 'https://acmeplumbing.com',
          evidence: '<h1 class="hero-title">Welcome to Quality Services</h1>',
          why_it_matters:
            'LLMs require clear, self-contained definitional statements ("X is a Y serving Z") to categorize your entity accurately in answer graphs.',
          recommended_fix:
            '<!-- Replace vague hero heading with clear entity positioning -->\n<h1>Acme Plumbing: Licensed Austin Plumbing & Drain Specialists</h1>\n<p>Acme Plumbing is a family-owned residential and commercial plumbing company serving Austin, TX since 2004.</p>'
        },
        {
          id: 'c2-2',
          check_id: 'entity_clarity',
          title: 'Missing Organization JSON-LD Schema on /about page',
          severity: 'high',
          confidence: 'high',
          page_url: 'https://acmeplumbing.com/about',
          evidence: 'No <script type="application/ld+json"> containing "Organization" or "PlumbingService" was found on /about.',
          why_it_matters:
            'Without Organization structured schema, AI models must guess your location, operating hours, phone number, and service catalog.',
          recommended_fix:
            '<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "PlumbingService",\n  "name": "Acme Plumbing Services",\n  "url": "https://acmeplumbing.com",\n  "telephone": "+1-512-555-0199",\n  "address": {\n    "@type": "PostalAddress",\n    "streetAddress": "1200 Congress Ave",\n    "addressLocality": "Austin",\n    "addressRegion": "TX",\n    "postalCode": "78701"\n  },\n  "priceRange": "$$"\n}\n</script>'
        }
      ]
    },
    {
      check_id: 'structured_data',
      check_name: 'Structured Data',
      score: 12,
      max_score: 25,
      weight: 25,
      weighted_score: 12,
      findings: [
        {
          id: 'c3-1',
          check_id: 'structured_data',
          title: 'Missing FAQPage schema despite 12 FAQ items in HTML',
          severity: 'high',
          confidence: 'high',
          page_url: 'https://acmeplumbing.com/services/drain-cleaning',
          evidence: 'HTML contains 12 <div class="faq-item"> elements but zero FAQPage JSON-LD markup.',
          why_it_matters:
            'AI Overviews and Perplexity heavily prioritize sources with valid FAQPage schema for direct Q&A citation.',
          recommended_fix:
            '<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n  "mainEntity": [{\n    "@type": "Question",\n    "name": "How much does emergency drain cleaning cost in Austin?",\n    "acceptedAnswer": {\n      "@type": "Answer",\n      "text": "Acme Plumbing offers flat-rate drain cleaning starting at $149 with no hidden trip fees in Austin, TX."\n    }\n  }]\n}\n</script>'
        }
      ]
    },
    {
      check_id: 'answer_ready',
      check_name: 'Answer-Ready Content',
      score: 23,
      max_score: 30,
      weight: 30,
      weighted_score: 23,
      findings: [
        {
          id: 'c4-1',
          check_id: 'answer_ready',
          title: 'Marketing filler copy on service page lacking citable facts',
          severity: 'medium',
          confidence: 'medium',
          page_url: 'https://acmeplumbing.com/services/drain-cleaning',
          evidence: 'Found sentence: "We offer the best drain cleaning services with unmatched quality and customer care."',
          why_it_matters:
            'Generative search engines filter out subjective marketing puffery and favor pages rich in concrete specs, pricing ranges, and timelines.',
          recommended_fix:
            '<!-- Rewrite generic marketing filler with factual, citable data -->\n<p>Acme Plumbing provides 24/7 hydro-jetting and motorized snake drain clearing across Austin, TX. Our licensed technicians clear clogged main lines within 60 minutes using camera inspection technology, backed by a 1-year clog-free guarantee.</p>'
        }
      ]
    }
  ],
  action_plan: [
    {
      rank: 1,
      action: 'Unblock GPTBot & PerplexityBot in robots.txt to allow AI indexing',
      impact: 'high',
      effort: 'low',
      source_finding_title: 'GPTBot and PerplexityBot blocked in robots.txt'
    },
    {
      rank: 2,
      action: 'Inject PlumbingService JSON-LD Schema into /about page',
      impact: 'high',
      effort: 'low',
      source_finding_title: 'Missing Organization JSON-LD Schema on /about page'
    },
    {
      rank: 3,
      action: 'Add FAQPage JSON-LD Schema on Drain Cleaning service page',
      impact: 'high',
      effort: 'medium',
      source_finding_title: 'Missing FAQPage schema despite 12 FAQ items in HTML'
    },
    {
      rank: 4,
      action: 'Create /llms.txt file on site root detailing pricing & service area',
      impact: 'medium',
      effort: 'low',
      source_finding_title: 'No llms.txt standard file detected'
    },
    {
      rank: 5,
      action: 'Replace vague H1 on homepage with explicit entity definition sentence',
      impact: 'medium',
      effort: 'low',
      source_finding_title: 'Vague homepage H1 heading and missing explicit entity definition'
    }
  ],
  strengths: [
    'Fast server response time (< 200ms) with valid HTML5 semantic tags',
    'Clear service navigation hierarchy linking to individual service offerings',
    'Physical address and local phone number listed in footer text'
  ],
  limitations: [
    {
      description: 'Audit scope limited to 3 pages: Homepage, /about, and /services/drain-cleaning.'
    },
    {
      description: 'Static HTML analysis only; client-side rendered JavaScript components were not executed.'
    }
  ]
};

export const mockAIVisibilityData: AIVisibilityResponse = {
  url: 'https://acmeplumbing.com',
  business_name: 'Acme Plumbing Services',
  experimental: true,
  note: 'Experimental - not included in your GEO Score',
  results: [
    {
      prompt: 'Who is Acme Plumbing Services in Austin, TX?',
      mentioned: true,
      cited: false,
      response_excerpt:
        'Acme Plumbing Services is a local plumbing provider in Austin, Texas. However, detailed service pricing and credential details were not retrieved directly from their official domain.',
      competitors_mentioned: ['Radiant Plumbing', 'Stan\'s Heating & Plumbing']
    },
    {
      prompt: 'What are the top recommended emergency drain cleaning services in Austin?',
      mentioned: false,
      cited: false,
      response_excerpt:
        'Top cited Austin emergency drain cleaners include Radiant Plumbing and Abacus Plumbing, which publish transparent pricing charts and structured service FAQs.',
      competitors_mentioned: ['Radiant Plumbing', 'Abacus Plumbing']
    }
  ]
};
