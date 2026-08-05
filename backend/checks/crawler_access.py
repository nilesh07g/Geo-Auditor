"""Check 1: AI Crawler Access - Milestone M5.

Scoring (max 20 points):
  - AI bot access via robots.txt:  0/4/8/12 pts
  - llms.txt presence:             0 or 5 pts
  - No meta/header noai/noindex:   0 or 3 pts

All findings are deterministic (High confidence).
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple

from models import (
    CheckResult,
    Confidence,
    Finding,
    Severity,
)

CHECK_ID = "crawler_access"
CHECK_NAME = "AI Crawler Access"
MAX_SCORE = 20
WEIGHT = 20

# AI crawlers tracked - name -> display label
AI_BOTS: Dict[str, str] = {
    "gptbot":         "GPTBot (ChatGPT)",
    "claudebot":      "ClaudeBot (Anthropic/Claude)",
    "perplexitybot":  "PerplexityBot (Perplexity)",
    "google-extended": "Google-Extended (Google AI Overviews)",
    "bytespider":     "Bytespider (ByteDance/TikTok)",
}

VAGUE_FILLER_PATTERNS = [
    "welcome", "home", "quality services", "we are the best",
    "leading provider", "innovative solutions", "our company",
]


# ---------------------------------------------------------------------------
# robots.txt parser
# ---------------------------------------------------------------------------

def parse_robots_txt(content: Optional[str]) -> Dict[str, bool]:
    """Parse robots.txt and return dict of bot_name_lower -> is_blocked.

    Interprets standard robots.txt rules:
    - User-agent: *       (wildcard)
    - Disallow: /         (full block)
    - Allow: /            (explicit allow, overrides disallow)
    Case-insensitive for user-agent names.
    """
    blocked: Dict[str, bool] = {bot: False for bot in AI_BOTS}

    if not content:
        return blocked  # No robots.txt = all bots allowed

    lines = content.splitlines()
    current_agents: List[str] = []
    wildcard_disallow_all = False
    # Per-agent tracking: agent -> (disallow_root, allow_root)
    agent_rules: Dict[str, Dict[str, bool]] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            if current_agents:
                current_agents = []
            continue

        if line.lower().startswith("user-agent:"):
            agent_val = line[len("user-agent:"):].strip().lower()
            current_agents.append(agent_val)
            if agent_val not in agent_rules:
                agent_rules[agent_val] = {"disallow_root": False, "allow_root": False}

        elif line.lower().startswith("disallow:") and current_agents:
            path = line[len("disallow:"):].strip()
            if path in ("/", "/*", ""):
                for agent in current_agents:
                    if agent not in agent_rules:
                        agent_rules[agent] = {"disallow_root": False, "allow_root": False}
                    agent_rules[agent]["disallow_root"] = True
                    if agent == "*":
                        wildcard_disallow_all = True

        elif line.lower().startswith("allow:") and current_agents:
            path = line[len("allow:"):].strip()
            if path in ("/", "/*"):
                for agent in current_agents:
                    if agent not in agent_rules:
                        agent_rules[agent] = {"disallow_root": False, "allow_root": False}
                    agent_rules[agent]["allow_root"] = True

    # Determine blocked status for each AI bot
    for bot_lower in AI_BOTS:
        bot_rules = agent_rules.get(bot_lower, {})
        wildcard_rules = agent_rules.get("*", {})

        bot_disallowed = bot_rules.get("disallow_root", False)
        bot_allowed = bot_rules.get("allow_root", False)
        wildcard_disallowed = wildcard_rules.get("disallow_root", False)
        wildcard_allowed = wildcard_rules.get("allow_root", False)

        # Specific bot rule takes precedence over wildcard
        if bot_disallowed and not bot_allowed:
            blocked[bot_lower] = True
        elif not bot_disallowed and not bot_allowed:
            # Fall through to wildcard
            if wildcard_disallowed and not wildcard_allowed:
                blocked[bot_lower] = True

    return blocked


def extract_blocked_lines(content: str, bot_name: str) -> str:
    """Extract the relevant robots.txt lines for a specific bot."""
    lines = content.splitlines()
    result_lines: List[str] = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("user-agent:"):
            agent = stripped[len("user-agent:"):].strip().lower()
            in_block = (agent == bot_name.lower() or agent == "*")
            if in_block:
                result_lines.append(stripped)
        elif in_block:
            if stripped == "" or stripped.startswith("#"):
                in_block = False
            else:
                result_lines.append(stripped)
    return "\n".join(result_lines[:8])  # Cap at 8 lines for readability


# ---------------------------------------------------------------------------
# Meta robots / X-Robots-Tag check
# ---------------------------------------------------------------------------

def check_meta_restrictions(homepage_html: str) -> Tuple[bool, str]:
    """Return (has_restriction, evidence_string) for noai/noindex in HTML."""
    if not homepage_html:
        return False, ""
    patterns = [
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']*)["\']>',
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']robots["\']>',
    ]
    for pat in patterns:
        match = re.search(pat, homepage_html, re.IGNORECASE)
        if match:
            content = match.group(1).lower()
            if any(kw in content for kw in ("noindex", "noai", "none")):
                return True, f'<meta name="robots" content="{match.group(1)}">'
    return False, ""


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------

def evaluate_crawler_access(
    robots_txt_content: Optional[str],
    robots_txt_status: int,
    llms_txt_content: Optional[str],
    llms_txt_status: int,
    homepage_html: str,
    target_url: str,
) -> CheckResult:
    """Evaluate Check 1: AI Crawler Access.

    Args:
        robots_txt_content: Raw text of /robots.txt (or None if not found).
        robots_txt_status:  HTTP status code for /robots.txt fetch.
        llms_txt_content:   Raw text of /llms.txt (or None if not found).
        llms_txt_status:    HTTP status code for /llms.txt fetch.
        homepage_html:      Raw HTML string of the homepage.
        target_url:         The audited business URL string.

    Returns:
        CheckResult with score, weighted_score, and findings.
    """
    findings: List[Finding] = []
    score = 0

    robots_url = target_url.rstrip("/") + "/robots.txt"
    llms_url = target_url.rstrip("/") + "/llms.txt"

    # ------------------------------------------------------------------ #
    # Signal 1: robots.txt AI bot access (max 12 pts)                     #
    # ------------------------------------------------------------------ #

    if robots_txt_status == 404 or not robots_txt_content:
        # Missing robots.txt = unrestricted access per web standard
        bot_score = 12
        # Optional low-severity note about missing robots.txt file
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No robots.txt file found",
            severity=Severity.low,
            confidence=Confidence.high,
            page_url=robots_url,
            evidence=f"HTTP {robots_txt_status} at {robots_url}",
            why_it_matters=(
                "While the absence of robots.txt allows all crawlers by default, "
                "adding an explicit robots.txt with AI crawler allow rules signals "
                "intentional openness to AI indexing — which can improve crawl prioritization."
            ),
            recommended_fix=(
                "# Create /robots.txt at site root:\n"
                "User-agent: *\n"
                "Allow: /\n\n"
                "# Explicitly welcome AI crawlers\n"
                "User-agent: GPTBot\n"
                "Allow: /\n\n"
                "User-agent: ClaudeBot\n"
                "Allow: /\n\n"
                "User-agent: PerplexityBot\n"
                "Allow: /\n\n"
                "User-agent: Google-Extended\n"
                "Allow: /"
            ),
        ))
    else:
        blocked_map = parse_robots_txt(robots_txt_content)
        blocked_bots = [bot for bot, is_blocked in blocked_map.items() if is_blocked]
        allowed_count = len(AI_BOTS) - len(blocked_bots)

        # Score based on allowed bot count
        if allowed_count == 5:
            bot_score = 12
        elif allowed_count >= 3:
            bot_score = 8
        elif allowed_count >= 1:
            bot_score = 4
        else:
            bot_score = 0

        # Check if wildcard blocks everything
        wildcard_blocks_all = all(blocked_map.values())

        if wildcard_blocks_all or len(blocked_bots) >= 4:
            # Critical: most or all AI bots blocked
            evidence_lines = extract_blocked_lines(robots_txt_content, "*")
            findings.append(Finding(
                id=str(uuid.uuid4()),
                check_id=CHECK_ID,
                title="Wildcard rule blocks all AI crawlers in robots.txt",
                severity=Severity.critical,
                confidence=Confidence.high,
                page_url=robots_url,
                evidence=evidence_lines or f"User-agent: *\nDisallow: /",
                why_it_matters=(
                    "A blanket Disallow: / rule prevents ChatGPT, Perplexity, Claude, and "
                    "Google AI Overviews from indexing your website, making your business "
                    "invisible in AI-generated search answers."
                ),
                recommended_fix=(
                    "# Replace blocking wildcard with explicit AI bot access in robots.txt:\n"
                    "User-agent: *\n"
                    "Allow: /\n\n"
                    "User-agent: GPTBot\n"
                    "Allow: /\n\n"
                    "User-agent: ClaudeBot\n"
                    "Allow: /\n\n"
                    "User-agent: PerplexityBot\n"
                    "Allow: /\n\n"
                    "User-agent: Google-Extended\n"
                    "Allow: /"
                ),
            ))
        else:
            # Individual bot blocks
            primary_bots = ["gptbot", "perplexitybot"]
            secondary_bots = ["claudebot", "google-extended", "bytespider"]

            for bot_lower in blocked_bots:
                label = AI_BOTS.get(bot_lower, bot_lower)
                severity = Severity.critical if bot_lower in primary_bots else Severity.high
                evidence = extract_blocked_lines(robots_txt_content, bot_lower)
                findings.append(Finding(
                    id=str(uuid.uuid4()),
                    check_id=CHECK_ID,
                    title=f"{label} blocked in robots.txt",
                    severity=severity,
                    confidence=Confidence.high,
                    page_url=robots_url,
                    evidence=evidence or f"User-agent: {bot_lower}\nDisallow: /",
                    why_it_matters=(
                        f"{label} cannot index or quote your website content. "
                        "Blocked AI crawlers cannot include your business in AI search answers."
                    ),
                    recommended_fix=(
                        f"# Add or update in robots.txt to allow {label}:\n"
                        f"User-agent: {list(AI_BOTS.keys())[list(AI_BOTS.values()).index(label) if label in AI_BOTS.values() else 0]}\n"
                        f"Allow: /"
                    ),
                ))

    score += bot_score

    # ------------------------------------------------------------------ #
    # Signal 2: llms.txt presence (max 5 pts)                             #
    # ------------------------------------------------------------------ #

    if llms_txt_status == 200 and llms_txt_content and len(llms_txt_content.strip()) >= 50:
        score += 5  # Full points: llms.txt present and non-trivial
    else:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="No llms.txt standard file found",
            severity=Severity.medium,
            confidence=Confidence.high,
            page_url=llms_url,
            evidence=(
                f"HTTP {llms_txt_status} Not Found at {llms_url}"
                if llms_txt_status != 200
                else f"llms.txt is present but contains insufficient content ({len(llms_txt_content or '')} chars)"
            ),
            why_it_matters=(
                "The llms.txt standard (llmstxt.org) allows you to publish a clean Markdown "
                "summary of your business specifically curated for LLM context windows. "
                "AI engines increasingly prioritize this signal for fast, accurate entity knowledge."
            ),
            recommended_fix=(
                "# Create /llms.txt at your site root with this template:\n\n"
                "# [Your Business Name]\n"
                "> [One-sentence plain-English description of your business.]\n\n"
                "## Core Services\n"
                "- [Service 1 with price range]\n"
                "- [Service 2 with price range]\n"
                "- [Service 3]\n\n"
                "## Service Area\n"
                "[City, State or Country]\n\n"
                "## Contact\n"
                "- Phone: [number]\n"
                "- Email: [email]\n"
                "- Address: [full address]"
            ),
        ))

    # ------------------------------------------------------------------ #
    # Signal 3: meta robots / X-Robots-Tag restrictions (max 3 pts)       #
    # ------------------------------------------------------------------ #

    has_restriction, meta_evidence = check_meta_restrictions(homepage_html)
    if has_restriction:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            check_id=CHECK_ID,
            title="Meta robots tag restricts AI crawling on homepage",
            severity=Severity.high,
            confidence=Confidence.high,
            page_url=target_url,
            evidence=meta_evidence,
            why_it_matters=(
                "A restrictive meta robots tag (noindex, noai, none) prevents AI search engines "
                "from including your homepage content in training data and live answer generation."
            ),
            recommended_fix=(
                '<!-- Replace the restrictive meta robots tag with an open directive -->\n'
                '<meta name="robots" content="index, follow">'
            ),
        ))
    else:
        score += 3  # No restrictions found

    # Clamp score to valid range
    score = min(score, MAX_SCORE)
    weighted_score = round((score / MAX_SCORE) * WEIGHT)

    return CheckResult(
        check_id=CHECK_ID,
        check_name=CHECK_NAME,
        score=score,
        max_score=MAX_SCORE,
        weight=WEIGHT,
        weighted_score=weighted_score,
        findings=findings,
    )
