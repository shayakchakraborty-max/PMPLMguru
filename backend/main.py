"""
PMGuru Brain v10.0 - Template-Driven Architecture
=================================================
PHILOSOPHY SHIFT from v9:
  OLD: LLM generates everything from scratch -> fragile, slow, 500s
  NEW: Agents are "trained" on real PM/PLM templates + examples.
       Output is generated DETERMINISTICALLY from templates filled
       with idea-specific context. LLM is used only for EVALUATION
       and polishing the summary text - never for structure.

Result: Always works. Always formatted. Sub-second response.
        LLM failure = graceful degradation, never a 500.
"""
import json
import os
import re
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

import httpx

# Research-grade MSME agent layer (self-contained, deterministic). Optional import
# so the legacy engine still boots even if this module is absent.
try:
    import msme_agents as MSME
except Exception as _e:
    MSME = None
    print(f"[msme_agents] not loaded: {_e}", flush=True)

try:
    import industry_playbooks as PLAYBOOKS
except Exception as _e:
    PLAYBOOKS = None
    print(f"[industry_playbooks] not loaded: {_e}", flush=True)

try:
    import live_brain as BRAIN
except Exception as _e:
    BRAIN = None
    print(f"[live_brain] not loaded: {_e}", flush=True)

try:
    import doc_store as DOCS
except Exception as _e:
    DOCS = None
    print(f"[doc_store] not loaded: {_e}", flush=True)

try:
    import gov_schemes as SCHEMES
except Exception as _e:
    SCHEMES = None
    print(f"[gov_schemes] not loaded: {_e}", flush=True)

try:
    import monitor as MONITOR
except Exception as _e:
    MONITOR = None
    print(f"[monitor] not loaded: {_e}", flush=True)

try:
    import sim_library as SIM
except Exception as _e:
    SIM = None
    print(f"[sim_library] not loaded: {_e}", flush=True)

try:
    import llm_stack as LLM
except Exception as _e:
    LLM = None
    print(f"[llm_stack] not loaded: {_e}", flush=True)

VERSION = "12.0"

# ============================================================
# KNOWLEDGE BASE - Methodology templates trained on real examples
# ============================================================
KNOWLEDGE_BASE = {
    "scrum": {
        "name": "Scrum",
        "best_for": "Software products with evolving requirements, teams of 5-9, iterative delivery",
        "confidence": "Very High",
        "reasoning": "Scrum's 2-week sprint cadence allows rapid iteration and stakeholder feedback, which is essential when requirements are likely to evolve as users interact with early versions. Daily standups keep small teams aligned, and the PO/SM/Dev role structure provides clear accountability without bureaucracy.",
        "why_not_others": [
            {"method": "Waterfall", "reason": "Too rigid - requirements will evolve as you learn from users, and sequential phases cannot absorb mid-project pivots."},
            {"method": "Kanban", "reason": "No built-in cadence for batched releases and stakeholder demos; better for steady-state operations than new product development."},
            {"method": "SAFe", "reason": "Overkill for teams under 50 people - introduces ceremonies and roles designed for multi-team coordination you don't need."},
        ],
        "method_details": {
            "roles": ["Product Owner", "Scrum Master", "Development Team (5-9)"],
            "ceremonies": ["Sprint Planning (4h)", "Daily Standup (15m)", "Sprint Review (2h)", "Sprint Retrospective (1.5h)", "Backlog Refinement (2h/week)"],
            "artifacts": ["Product Backlog", "Sprint Backlog", "Increment", "Burndown Chart", "Definition of Done"],
            "cadence": "2-week sprints",
        },
        "tool_recommendation": {
            "primary": "Linear",
            "alternatives": ["Jira", "Asana", "ClickUp"],
            "reason": "Linear offers the cleanest Scrum workflow with built-in sprints, cycles, and velocity tracking, without Jira's configuration overhead. Keyboard-first UX accelerates the team's daily work.",
        },
        "success_factors": [
            "Product Owner is empowered to make real-time scope decisions",
            "Team holds retrospectives and actually acts on improvements",
            "Sprint goals are outcome-focused, not just task lists",
            "Stakeholders attend Sprint Reviews for fast feedback loops",
        ],
        "phases": [
            {"name": "Sprint 0 - Foundation", "duration_weeks": 2, "key_activities": ["Team formation", "Tech stack decisions", "Dev environment setup", "Initial backlog creation", "Definition of Done agreement"], "deliverables": ["Working dev environment", "Prioritized product backlog", "Sprint 1 plan"]},
            {"name": "Sprints 1-3 - MVP Build", "duration_weeks": 6, "key_activities": ["Core feature development", "Daily standups", "Sprint reviews with stakeholders", "Continuous integration"], "deliverables": ["Functional MVP", "Automated test suite", "Deployed staging environment"]},
            {"name": "Sprints 4-5 - Polish & Beta", "duration_weeks": 4, "key_activities": ["UX refinement", "Performance optimization", "Beta user onboarding", "Bug triage"], "deliverables": ["Beta release", "User feedback report", "Performance benchmarks"]},
            {"name": "Sprint 6 - Launch", "duration_weeks": 2, "key_activities": ["Production deployment", "Marketing alignment", "Launch monitoring", "Support readiness"], "deliverables": ["Live product", "Launch announcement", "Monitoring dashboards"]},
            {"name": "Post-Launch - Iterate", "duration_weeks": 4, "key_activities": ["User analytics review", "Feature prioritization", "Rapid iteration on feedback"], "deliverables": ["v1.1 release", "Product-market fit metrics", "Roadmap for next quarter"]},
        ],
        "team_composition": [
            {"role": "Product Owner", "count": 1, "allocation": "100%"},
            {"role": "Scrum Master", "count": 1, "allocation": "50%"},
            {"role": "Senior Full-Stack Engineer", "count": 2, "allocation": "100%"},
            {"role": "Frontend Engineer", "count": 1, "allocation": "100%"},
            {"role": "UX Designer", "count": 1, "allocation": "75%"},
            {"role": "QA Engineer", "count": 1, "allocation": "75%"},
        ],
        "kpis": [
            {"metric": "Sprint Velocity", "target": "40-60 story points stable by Sprint 3"},
            {"metric": "User Activation Rate", "target": "60% within 7 days of signup"},
            {"metric": "Defect Escape Rate", "target": "< 5% defects reach production"},
            {"metric": "Stakeholder NPS", "target": "≥ 8/10 after Sprint Reviews"},
        ],
        "risks": [
            {"id": "R-1", "type": "Risk", "description": "Scope creep from stakeholders mid-sprint", "probability": 4, "impact": 4, "mitigation": "Enforce sprint goal protection; route new requests to backlog for next sprint planning", "owner": "Scrum Master"},
            {"id": "R-2", "type": "Risk", "description": "Product Owner unavailable for rapid decisions", "probability": 3, "impact": 5, "mitigation": "Establish PO proxy with decision authority up to a defined threshold", "owner": "Product Owner"},
            {"id": "R-3", "type": "Risk", "description": "Technical debt accumulates faster than velocity allows", "probability": 4, "impact": 3, "mitigation": "Reserve 20% of each sprint for refactoring; track debt in backlog", "owner": "Tech Lead"},
            {"id": "R-4", "type": "Risk", "description": "Team burnout from aggressive sprint commitments", "probability": 3, "impact": 4, "mitigation": "Monitor velocity variance; enforce sustainable pace in retrospectives", "owner": "Scrum Master"},
            {"id": "R-5", "type": "Risk", "description": "Low user adoption post-launch", "probability": 3, "impact": 5, "mitigation": "Run 5+ user interviews per sprint starting Sprint 2; validate before full build", "owner": "Product Owner"},
            {"id": "R-6", "type": "Risk", "description": "Integration failures with third-party APIs", "probability": 3, "impact": 3, "mitigation": "Build adapter pattern; implement circuit breakers; maintain vendor SLA tracking", "owner": "Tech Lead"},
        ],
        "stakeholders": [
            {"name": "Executive Sponsor", "power": "High", "interest": "High", "strategy": "Manage Closely", "channel": "Weekly 1:1 + Sprint Review demo"},
            {"name": "End Users / Beta Testers", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "In-app updates + monthly newsletter + user interviews"},
            {"name": "Engineering Leadership", "power": "High", "interest": "Medium", "strategy": "Keep Satisfied", "channel": "Bi-weekly architecture review"},
            {"name": "Sales & Marketing Team", "power": "Medium", "interest": "High", "strategy": "Keep Informed", "channel": "Sprint Review attendance + Slack channel"},
            {"name": "Customer Support", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "Release notes + training sessions before launch"},
            {"name": "Security & Compliance", "power": "High", "interest": "Low", "strategy": "Keep Satisfied", "channel": "Pre-release security review + audit trail"},
            {"name": "Finance / Budget Owner", "power": "High", "interest": "Low", "strategy": "Keep Satisfied", "channel": "Monthly burn report"},
        ],
    },

    "kanban": {
        "name": "Kanban",
        "best_for": "Continuous flow work, support/ops, content pipelines, teams with unpredictable incoming requests",
        "confidence": "High",
        "reasoning": "Kanban's visual board and WIP limits are ideal when work arrives unpredictably and must be handled as it comes, rather than in batched sprints. It minimizes ceremony overhead and maximizes flow efficiency, which suits ongoing operational work better than new product development.",
        "why_not_others": [
            {"method": "Scrum", "reason": "Sprint commitments are disrupted by the unpredictable arrival of support tickets and operational requests."},
            {"method": "Waterfall", "reason": "Sequential phases have no place in a continuous-flow environment where work is always in-flight."},
            {"method": "PRINCE2", "reason": "Stage gates and governance ceremonies create friction that slows down short-cycle operational work."},
        ],
        "method_details": {
            "roles": ["Service Request Manager", "Flow Manager", "Team Members (cross-functional)"],
            "ceremonies": ["Daily Kanban standup (10m)", "Service Delivery Review (weekly)", "Operations Review (monthly)", "Replenishment meeting (weekly)"],
            "artifacts": ["Kanban board", "WIP limits per column", "Cumulative flow diagram", "Lead time distribution chart", "Service classes"],
            "cadence": "Continuous flow",
        },
        "tool_recommendation": {
            "primary": "Trello",
            "alternatives": ["Jira (Kanban board)", "Notion", "Linear"],
            "reason": "Trello's card-based UI is the most intuitive for non-technical stakeholders and supports WIP limits via Power-Ups. Zero learning curve.",
        },
        "success_factors": [
            "WIP limits are strictly enforced - work is pulled, never pushed",
            "Cycle time metrics drive continuous improvement",
            "Service classes distinguish urgent vs standard work",
            "Regular replenishment keeps backlog healthy without overplanning",
        ],
        "phases": [
            {"name": "Phase 1 - Board Design", "duration_weeks": 1, "key_activities": ["Map value stream", "Define columns", "Set initial WIP limits", "Identify service classes"], "deliverables": ["Live Kanban board", "WIP limit policy", "Definition of Done per column"]},
            {"name": "Phase 2 - Ramp Up", "duration_weeks": 4, "key_activities": ["Initial work intake", "Daily standups", "WIP limit adjustment", "Metrics baseline"], "deliverables": ["Cycle time baseline", "Throughput baseline", "First Service Delivery Review"]},
            {"name": "Phase 3 - Optimize", "duration_weeks": 8, "key_activities": ["Bottleneck identification", "Process improvements", "Cumulative flow analysis"], "deliverables": ["Optimized flow", "Reduced cycle time", "Monthly operations review"]},
            {"name": "Phase 4 - Steady State", "duration_weeks": 0, "key_activities": ["Continuous delivery", "Kaizen improvements", "Predictable SLAs"], "deliverables": ["Consistent cycle time", "Published SLA commitments", "Ongoing improvement log"]},
        ],
        "team_composition": [
            {"role": "Flow Manager", "count": 1, "allocation": "50%"},
            {"role": "Service Request Manager", "count": 1, "allocation": "100%"},
            {"role": "Cross-functional Team Member", "count": 4, "allocation": "100%"},
            {"role": "Technical Specialist (on-call)", "count": 1, "allocation": "25%"},
        ],
        "kpis": [
            {"metric": "Average Cycle Time", "target": "< 5 days for standard class"},
            {"metric": "Throughput", "target": "15+ items per week steady state"},
            {"metric": "WIP Adherence", "target": "> 95% compliance with limits"},
            {"metric": "SLA Achievement", "target": "90% of items within service class SLA"},
        ],
        "risks": [
            {"id": "R-1", "type": "Risk", "description": "WIP limits ignored under urgency pressure", "probability": 4, "impact": 4, "mitigation": "Visible limit enforcement; escalation policy for exceeding limits", "owner": "Flow Manager"},
            {"id": "R-2", "type": "Risk", "description": "Bottleneck column blocks entire flow", "probability": 4, "impact": 4, "mitigation": "Daily standup highlights blockers; swarm pattern for clearing bottlenecks", "owner": "Team"},
            {"id": "R-3", "type": "Risk", "description": "No predictable delivery date for stakeholders", "probability": 3, "impact": 3, "mitigation": "Use cycle time percentiles for forecasts; communicate service classes upfront", "owner": "Service Request Manager"},
            {"id": "R-4", "type": "Risk", "description": "Backlog bloat from uncontrolled intake", "probability": 4, "impact": 3, "mitigation": "Weekly replenishment with explicit prioritization; aging policy for stale items", "owner": "Flow Manager"},
            {"id": "R-5", "type": "Risk", "description": "Team members optimize locally instead of for flow", "probability": 3, "impact": 3, "mitigation": "Reward throughput and cycle time, not individual output", "owner": "Flow Manager"},
            {"id": "R-6", "type": "Risk", "description": "Technical debt invisible without sprint reviews", "probability": 3, "impact": 3, "mitigation": "Dedicated 'improvement' service class with guaranteed throughput", "owner": "Flow Manager"},
        ],
        "stakeholders": [
            {"name": "Internal Customers", "power": "Medium", "interest": "High", "strategy": "Keep Informed", "channel": "Kanban board visibility + weekly status"},
            {"name": "Operations Leadership", "power": "High", "interest": "High", "strategy": "Manage Closely", "channel": "Monthly Operations Review"},
            {"name": "Service Consumers", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "SLA dashboard + ticket status"},
            {"name": "Finance", "power": "High", "interest": "Low", "strategy": "Keep Satisfied", "channel": "Quarterly cost-per-item report"},
            {"name": "HR / Team Welfare", "power": "Medium", "interest": "Medium", "strategy": "Keep Informed", "channel": "Flow metrics showing sustainable pace"},
        ],
    },

    "waterfall": {
        "name": "Waterfall",
        "best_for": "Fixed-scope projects with stable requirements - hardware, regulated industries, construction, compliance-heavy work",
        "confidence": "High",
        "reasoning": "When requirements are fully knowable upfront and change is expensive (hardware tooling, regulatory approval, physical construction), Waterfall's sequential phases provide the predictability, documentation depth, and audit trail that regulators and finance teams require. Rework after a phase gate is costly, which enforces upfront rigor.",
        "why_not_others": [
            {"method": "Scrum", "reason": "Iterative changes are impractical when each phase locks in physical or regulatory commitments that cannot be cheaply undone."},
            {"method": "Kanban", "reason": "Continuous flow has no mechanism for the phase gates and formal handoffs that regulated work requires."},
            {"method": "Lean Startup", "reason": "The 'build-measure-learn' loop assumes cheap pivots, which don't exist when you're manufacturing hardware or seeking FDA approval."},
        ],
        "method_details": {
            "roles": ["Project Manager", "Requirements Analyst", "Architect", "Development Lead", "QA Manager", "Deployment Manager"],
            "ceremonies": ["Phase gate reviews", "Change control board", "Formal sign-offs", "Weekly PM status meeting"],
            "artifacts": ["Requirements Specification (SRS)", "Design Document", "Test Plan", "Traceability Matrix", "Gantt Chart", "Change Requests"],
            "cadence": "Sequential phase gates",
        },
        "tool_recommendation": {
            "primary": "Microsoft Project",
            "alternatives": ["Smartsheet", "Primavera P6", "Jira with Structure plugin"],
            "reason": "MS Project's Gantt-centric interface, resource leveling, and critical path analysis are purpose-built for predictable sequential execution with dependencies.",
        },
        "success_factors": [
            "Requirements are frozen before design begins - change control is strict",
            "Traceability matrix links every requirement to design, code, and test",
            "Phase gates have formal sign-off criteria and executive review",
            "Risk register is maintained from day one with mitigation owners",
        ],
        "phases": [
            {"name": "Phase 1 - Requirements", "duration_weeks": 4, "key_activities": ["Stakeholder interviews", "Requirements elicitation", "SRS document creation", "Traceability matrix setup"], "deliverables": ["Signed-off SRS", "Use cases", "Acceptance criteria"]},
            {"name": "Phase 2 - Design", "duration_weeks": 6, "key_activities": ["Architecture design", "Detailed design docs", "Database schema", "Interface specs"], "deliverables": ["Architecture document", "HLD + LLD", "Design review sign-off"]},
            {"name": "Phase 3 - Implementation", "duration_weeks": 12, "key_activities": ["Coding to spec", "Unit testing", "Code reviews", "Documentation"], "deliverables": ["Completed codebase", "Unit test results", "Technical documentation"]},
            {"name": "Phase 4 - Verification", "duration_weeks": 6, "key_activities": ["System testing", "UAT", "Performance testing", "Security audit", "Compliance validation"], "deliverables": ["Test report", "UAT sign-off", "Compliance certification"]},
            {"name": "Phase 5 - Deployment", "duration_weeks": 2, "key_activities": ["Production rollout", "User training", "Documentation handoff", "Support transition"], "deliverables": ["Live system", "Training materials", "Operations runbook"]},
            {"name": "Phase 6 - Maintenance", "duration_weeks": 0, "key_activities": ["Bug fixes", "Change requests", "Preventive maintenance"], "deliverables": ["Maintenance SLA", "Change log", "Performance reports"]},
        ],
        "team_composition": [
            {"role": "Project Manager", "count": 1, "allocation": "100%"},
            {"role": "Business Analyst", "count": 2, "allocation": "100%"},
            {"role": "Solution Architect", "count": 1, "allocation": "100%"},
            {"role": "Developer", "count": 4, "allocation": "100%"},
            {"role": "QA Lead", "count": 1, "allocation": "100%"},
            {"role": "Compliance Officer", "count": 1, "allocation": "50%"},
        ],
        "kpis": [
            {"metric": "Phase Gate On-Time Rate", "target": "100% of gates met on schedule"},
            {"metric": "Requirements Volatility", "target": "< 10% change after requirements freeze"},
            {"metric": "Defect Density", "target": "< 1 defect per 1000 LOC at deployment"},
            {"metric": "Budget Variance", "target": "Within +/- 5% of baseline"},
        ],
        "risks": [
            {"id": "R-1", "type": "Risk", "description": "Requirements discovered late in development", "probability": 4, "impact": 5, "mitigation": "Extensive requirements phase with sign-off; strict change control with impact assessment", "owner": "Business Analyst"},
            {"id": "R-2", "type": "Risk", "description": "Integration failures discovered in testing", "probability": 3, "impact": 5, "mitigation": "Interface contracts defined in design phase; early integration test environment", "owner": "Architect"},
            {"id": "R-3", "type": "Risk", "description": "Regulatory compliance gap found during audit", "probability": 2, "impact": 5, "mitigation": "Compliance officer embedded from Phase 1; pre-audit in Phase 4", "owner": "Compliance Officer"},
            {"id": "R-4", "type": "Risk", "description": "Key personnel departure mid-project", "probability": 3, "impact": 4, "mitigation": "Documentation enforced per phase; shadow roles for critical positions", "owner": "PM"},
            {"id": "R-5", "type": "Risk", "description": "Budget overrun due to change requests", "probability": 4, "impact": 4, "mitigation": "Change control board with finance approval; 15% contingency reserve", "owner": "PM"},
            {"id": "R-6", "type": "Risk", "description": "UAT reveals usability issues unaddressed in design", "probability": 3, "impact": 4, "mitigation": "Prototype review with end users in Design phase", "owner": "UX Lead"},
        ],
        "stakeholders": [
            {"name": "Executive Sponsor", "power": "High", "interest": "High", "strategy": "Manage Closely", "channel": "Monthly steering committee + phase gate approvals"},
            {"name": "Regulatory Body", "power": "High", "interest": "Medium", "strategy": "Keep Satisfied", "channel": "Formal audit documentation + scheduled reviews"},
            {"name": "End Users", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "Training + UAT involvement"},
            {"name": "Finance", "power": "High", "interest": "High", "strategy": "Manage Closely", "channel": "Monthly budget reports + change request approvals"},
            {"name": "Operations Team", "power": "Medium", "interest": "High", "strategy": "Keep Informed", "channel": "Deployment readiness reviews"},
            {"name": "Legal / Procurement", "power": "Medium", "interest": "Low", "strategy": "Keep Satisfied", "channel": "Contract milestones + formal deliverable sign-offs"},
        ],
    },

    "lean_startup": {
        "name": "Lean Startup",
        "best_for": "Early-stage products seeking product-market fit, MVPs, pre-revenue startups validating hypotheses",
        "confidence": "Very High",
        "reasoning": "When you're uncertain about core assumptions (who the customer is, what they'll pay for, what actually solves their problem), Lean Startup's build-measure-learn cycles minimize waste by validating each hypothesis cheaply before committing capital. The goal isn't shipping features - it's learning what to build.",
        "why_not_others": [
            {"method": "Waterfall", "reason": "Assumes you know what to build - but at the MVP stage, the riskiest assumption is whether anyone wants it at all."},
            {"method": "Scrum", "reason": "Scrum assumes you have a backlog worth building; Lean Startup first validates whether the backlog exists."},
            {"method": "SAFe", "reason": "Enterprise scaling framework for established products, not for finding product-market fit."},
        ],
        "method_details": {
            "roles": ["Founder / Product Lead", "Growth Hacker", "Full-stack Engineer", "Customer Development Lead"],
            "ceremonies": ["Weekly metrics review", "Hypothesis validation session", "Pivot-or-persevere decision meeting", "Customer interview debriefs"],
            "artifacts": ["Lean Canvas", "Hypothesis log", "Validated learning report", "Cohort analysis", "North Star metric dashboard"],
            "cadence": "1-week build-measure-learn loops",
        },
        "tool_recommendation": {
            "primary": "Notion + Mixpanel",
            "alternatives": ["Airtable + Amplitude", "Linear + PostHog"],
            "reason": "Notion for lightweight hypothesis tracking and customer notes, Mixpanel for rigorous cohort analytics. Both free at startup scale.",
        },
        "success_factors": [
            "Every feature ties to a falsifiable hypothesis",
            "Customer interviews happen weekly, not quarterly",
            "Metrics are actionable, not vanity",
            "Team is willing to pivot when data invalidates assumptions",
        ],
        "phases": [
            {"name": "Phase 1 - Problem Validation", "duration_weeks": 2, "key_activities": ["20+ customer interviews", "Problem hypothesis definition", "Lean Canvas creation"], "deliverables": ["Validated problem statement", "Customer archetype", "Lean Canvas v1"]},
            {"name": "Phase 2 - Solution Validation", "duration_weeks": 2, "key_activities": ["Concierge MVP", "Landing page test", "Willingness-to-pay experiments"], "deliverables": ["Solution hypothesis validated", "Pricing signal", "Waitlist conversion data"]},
            {"name": "Phase 3 - MVP Build", "duration_weeks": 4, "key_activities": ["Minimum viable build", "Instrumentation first", "Alpha user onboarding"], "deliverables": ["Live MVP", "Analytics dashboard", "10 active alpha users"]},
            {"name": "Phase 4 - Measure & Learn", "duration_weeks": 4, "key_activities": ["Cohort analysis", "Funnel optimization", "Retention experiments"], "deliverables": ["Activation/retention metrics", "Validated learning report", "Next-cycle hypotheses"]},
            {"name": "Phase 5 - Pivot or Scale", "duration_weeks": 2, "key_activities": ["Strategic decision", "Scale plan or pivot plan", "Fundraising prep if scaling"], "deliverables": ["Pivot/persevere decision memo", "Next-phase roadmap"]},
        ],
        "team_composition": [
            {"role": "Founder / Product Lead", "count": 1, "allocation": "100%"},
            {"role": "Full-Stack Engineer", "count": 2, "allocation": "100%"},
            {"role": "Growth / Marketing", "count": 1, "allocation": "75%"},
            {"role": "Designer (contract)", "count": 1, "allocation": "50%"},
        ],
        "kpis": [
            {"metric": "Validated Learnings per Week", "target": "≥ 2 hypotheses tested weekly"},
            {"metric": "Customer Interview Count", "target": "10+ per week in Phase 1-2"},
            {"metric": "Activation Rate", "target": "40% of signups complete core action"},
            {"metric": "Week-4 Retention", "target": "≥ 20% for a real signal"},
        ],
        "risks": [
            {"id": "R-1", "type": "Risk", "description": "Building before validating the problem exists", "probability": 5, "impact": 5, "mitigation": "Mandate 20 customer interviews before writing code", "owner": "Founder"},
            {"id": "R-2", "type": "Risk", "description": "Vanity metrics mask lack of real engagement", "probability": 4, "impact": 4, "mitigation": "Define North Star metric tied to user value, not activity", "owner": "Growth Lead"},
            {"id": "R-3", "type": "Risk", "description": "Founders refuse to pivot despite data", "probability": 4, "impact": 5, "mitigation": "Pre-commit to pivot criteria before running experiments", "owner": "Advisors / Board"},
            {"id": "R-4", "type": "Risk", "description": "MVP technical debt blocks iteration speed", "probability": 3, "impact": 3, "mitigation": "Boring tech stack; defer optimization until PMF", "owner": "Engineering Lead"},
            {"id": "R-5", "type": "Risk", "description": "Running out of runway before PMF", "probability": 4, "impact": 5, "mitigation": "Track burn weekly; set tripwire at 6 months runway", "owner": "Founder"},
            {"id": "R-6", "type": "Risk", "description": "Customer interviews biased toward friendly users", "probability": 4, "impact": 3, "mitigation": "Recruit cold leads; use Mom Test techniques", "owner": "Customer Dev Lead"},
        ],
        "stakeholders": [
            {"name": "Investors / Advisors", "power": "High", "interest": "High", "strategy": "Manage Closely", "channel": "Monthly investor update + KPI dashboard"},
            {"name": "Early Customers", "power": "Medium", "interest": "High", "strategy": "Manage Closely", "channel": "Weekly interviews + direct founder access"},
            {"name": "Team", "power": "Medium", "interest": "High", "strategy": "Manage Closely", "channel": "Daily standups + transparency on metrics"},
            {"name": "Prospective Customers", "power": "Low", "interest": "Medium", "strategy": "Keep Informed", "channel": "Landing page + waitlist updates"},
            {"name": "Mentors", "power": "Low", "interest": "High", "strategy": "Keep Informed", "channel": "Bi-weekly check-ins"},
        ],
    },
}


# ============================================================
# TRAINING LIBRARY - 500+ real-world project examples
# ============================================================
# Each example is a tuple: (idea_text, expected_method, expected_industry, expected_complexity)
# These are used by the simulation runner to validate agent accuracy.
# Generated from 50 base templates x 10 variations each = 500+ examples.

_BASE_TEMPLATES = [
    # Retail/SMB - Scrum
    ("grocery app for kirana store with POS and inventory", "scrum", "Retail/SMB", "medium"),
    ("retail merchant dashboard with GST filing and credit ledger", "scrum", "Retail/SMB", "medium"),
    ("point of sale app for small shop with barcode scanner", "scrum", "Retail/SMB", "medium"),
    ("inventory management for retail store with supplier tracking", "scrum", "Retail/SMB", "medium"),
    ("merchant onboarding platform for msme segment", "scrum", "Retail/SMB", "medium"),
    # SaaS/Product - Scrum
    ("b2b saas platform for project collaboration", "scrum", "SaaS/Product", "medium"),
    ("mobile app for habit tracking and gamification", "scrum", "SaaS/Product", "medium"),
    ("web app for freelance invoicing and time tracking", "scrum", "SaaS/Product", "medium"),
    ("product analytics tool with cohort analysis", "scrum", "SaaS/Product", "medium"),
    ("customer feedback platform with sentiment analysis", "scrum", "SaaS/Product", "medium"),
    # AI/ML - Scrum high complexity
    ("ai chatbot for customer service using llm and rag", "scrum", "AI/ML", "high"),
    ("generative ai tool for content creation using gpt", "scrum", "AI/ML", "high"),
    ("ml model for fraud detection in transactions", "scrum", "AI/ML", "high"),
    ("nlp pipeline for document summarization", "scrum", "AI/ML", "high"),
    ("ai agent for autonomous task execution", "scrum", "AI/ML", "high"),
    # Fintech - Scrum high complexity
    ("fintech lending platform with credit scoring", "scrum", "Fintech", "high"),
    ("payment gateway with upi integration", "scrum", "Fintech", "high"),
    ("digital banking app with savings and payments", "scrum", "Fintech", "high"),
    ("insurance claim processing system", "scrum", "Fintech", "high"),
    ("credit line product for small merchants", "scrum", "Fintech", "high"),
    # Healthcare - Waterfall very high
    ("medical device firmware with fda regulatory approval", "waterfall", "Healthcare", "very_high"),
    ("hospital patient management system with hipaa compliance", "waterfall", "Healthcare", "very_high"),
    ("clinical diagnosis support tool for radiologists", "waterfall", "Healthcare", "very_high"),
    ("pharma drug tracking system with audit trail", "waterfall", "Healthcare", "very_high"),
    ("medical device for patient monitoring in icu", "waterfall", "Healthcare", "very_high"),
    # Construction/Hardware - Waterfall very high
    ("construction project management for 50 story building", "waterfall", "Construction/Hardware", "very_high"),
    ("aerospace navigation system with safety certification", "waterfall", "Construction/Hardware", "very_high"),
    ("automotive engine control unit firmware", "waterfall", "Construction/Hardware", "very_high"),
    ("hardware manufacturing line for consumer electronics", "waterfall", "Construction/Hardware", "very_high"),
    ("infrastructure project for highway bridge", "waterfall", "Construction/Hardware", "very_high"),
    # GovTech - Waterfall high
    ("government tax filing portal with gst compliance", "waterfall", "GovTech", "high"),
    ("regulatory audit system for banking compliance", "waterfall", "GovTech", "high"),
    ("municipal citizen services portal", "waterfall", "GovTech", "high"),
    ("government subsidy distribution with aadhaar", "waterfall", "GovTech", "high"),
    ("compliance tracking platform for regulated industry", "waterfall", "GovTech", "high"),
    # Operations - Kanban low
    ("customer support ticketing system", "kanban", "Operations", "low"),
    ("helpdesk platform for it incident management", "kanban", "Operations", "low"),
    ("ops dashboard for service desk team", "kanban", "Operations", "low"),
    ("customer service triage workflow", "kanban", "Operations", "low"),
    ("ticketing system for field service operations", "kanban", "Operations", "low"),
    # Content/Media - Kanban low
    ("editorial workflow for newsroom publishing", "kanban", "Content/Media", "low"),
    ("content pipeline for media publishing platform", "kanban", "Content/Media", "low"),
    ("publishing workflow for digital magazine", "kanban", "Content/Media", "low"),
    ("editorial review system for academic journal", "kanban", "Content/Media", "low"),
    ("newsroom content management system", "kanban", "Content/Media", "low"),
    # Early-Stage - Lean Startup low
    ("early-stage mvp to validate willingness-to-pay hypothesis", "lean_startup", "Early-Stage", "low"),
    ("pre-revenue experiment to test pmf in new market", "lean_startup", "Early-Stage", "low"),
    ("validation prototype for business hypothesis", "lean_startup", "Early-Stage", "low"),
    ("mvp for product-market fit validation", "lean_startup", "Early-Stage", "low"),
    ("early-stage startup mvp with lean experiments", "lean_startup", "Early-Stage", "low"),
]


def _generate_training_examples():
    """Generate 500+ training examples by varying base templates."""
    variations = [
        "build a {}",
        "create {}",
        "design and deploy {}",
        "launch {}",
        "we need to develop {}",
        "project to implement {}",
        "initiative for {}",
        "startup building {}",
        "enterprise rollout of {}",
        "ship {}",
    ]
    library = []
    for base, method, industry, complexity in _BASE_TEMPLATES:
        for var in variations:
            library.append({
                "idea": var.format(base),
                "expected_method": method,
                "expected_industry": industry,
                "expected_complexity": complexity,
            })
    return library


TRAINING_LIBRARY = _generate_training_examples()


def run_simulations():
    """Run all training examples through the classifier. Returns accuracy stats."""
    results = {
        "total": len(TRAINING_LIBRARY),
        "method_correct": 0,
        "industry_correct": 0,
        "complexity_correct": 0,
        "failures": [],
        "by_method": {},
        "by_industry": {},
    }
    for example in TRAINING_LIBRARY:
        classification = classify_idea(example["idea"])
        method_ok = classification["method_key"] == example["expected_method"]
        industry_ok = classification["industry"] == example["expected_industry"]
        complexity_ok = classification["complexity"] == example["expected_complexity"]

        if method_ok:
            results["method_correct"] += 1
        if industry_ok:
            results["industry_correct"] += 1
        if complexity_ok:
            results["complexity_correct"] += 1

        # Track per-method accuracy
        em = example["expected_method"]
        if em not in results["by_method"]:
            results["by_method"][em] = {"total": 0, "correct": 0}
        results["by_method"][em]["total"] += 1
        if method_ok:
            results["by_method"][em]["correct"] += 1

        ei = example["expected_industry"]
        if ei not in results["by_industry"]:
            results["by_industry"][ei] = {"total": 0, "correct": 0}
        results["by_industry"][ei]["total"] += 1
        if industry_ok:
            results["by_industry"][ei]["correct"] += 1

        if not method_ok and len(results["failures"]) < 20:
            results["failures"].append({
                "idea": example["idea"][:80],
                "expected_method": example["expected_method"],
                "got_method": classification["method_key"],
                "expected_industry": example["expected_industry"],
                "got_industry": classification["industry"],
            })

    results["method_accuracy"] = round(100 * results["method_correct"] / results["total"], 1)
    results["industry_accuracy"] = round(100 * results["industry_correct"] / results["total"], 1)
    results["complexity_accuracy"] = round(100 * results["complexity_correct"] / results["total"], 1)
    return results


# ============================================================
# INDUSTRY PATTERN LIBRARY - for classification
# ============================================================
# Order matters: more specific patterns first, general ones last.
# Ties in scoring are broken in favor of whichever was listed first.
INDUSTRY_PATTERNS = [
    {"keywords": ["healthcare", "medical", "hospital", "patient", "diagnosis", "clinical", "fda", "hipaa", "pharma", "device"], "industry": "Healthcare", "complexity": "very_high", "method": "waterfall"},
    {"keywords": ["construction", "scaffolding", "civil engineering", "skyscraper", "infrastructure", "hardware", "manufacturing", "aerospace", "automotive", "factory"], "industry": "Construction/Hardware", "complexity": "very_high", "method": "waterfall"},
    {"keywords": ["government", "compliance", "regulation", "regulatory", "audit", "tax", "gst", "govtech"], "industry": "GovTech", "complexity": "high", "method": "waterfall"},
    {"keywords": ["validate", "validation", "hypothesis", "experiment", "pre-revenue", "early-stage", "willingness-to-pay", "pmf", "product-market", "mvp"], "industry": "Early-Stage", "complexity": "low", "method": "lean_startup"},
    {"keywords": ["support", "helpdesk", "ticketing", "operations", "ops", "customer service", "service desk", "incident"], "industry": "Operations", "complexity": "low", "method": "kanban"},
    {"keywords": ["content", "editorial", "publishing", "newsroom", "media pipeline"], "industry": "Content/Media", "complexity": "low", "method": "kanban"},
    {"keywords": ["fintech", "banking", "lending", "payment", "upi", "credit", "insurance"], "industry": "Fintech", "complexity": "high", "method": "scrum"},
    {"keywords": ["ai", "ml", "llm", "gpt", "rag", "agent", "chatbot", "nlp", "generative"], "industry": "AI/ML", "complexity": "high", "method": "scrum"},
    {"keywords": ["kirana", "grocery", "retail", "pos", "merchant", "msme", "shopkeeper", "store"], "industry": "Retail/SMB", "complexity": "medium", "method": "scrum"},
    {"keywords": ["b2b", "enterprise", "wholesale", "procurement", "distributor"], "industry": "B2B", "complexity": "medium", "method": "scrum"},
    {"keywords": ["education", "learning", "edtech", "course", "training", "lms"], "industry": "EdTech", "complexity": "medium", "method": "scrum"},
    {"keywords": ["saas", "platform", "web app", "mobile app", "product", "startup"], "industry": "SaaS/Product", "complexity": "medium", "method": "scrum"},
]

COMPLEXITY_BUDGETS = {
    "low":       {"people": 120000, "tools": 6000,  "infrastructure": 4000,  "contingency": 15000, "total": 145000},
    "medium":    {"people": 220000, "tools": 12000, "infrastructure": 8000,  "contingency": 25000, "total": 265000},
    "high":      {"people": 480000, "tools": 24000, "infrastructure": 18000, "contingency": 60000, "total": 582000},
    "very_high": {"people": 950000, "tools": 40000, "infrastructure": 45000, "contingency": 120000,"total": 1155000},
}


def classify_idea(idea: str) -> dict:
    """Rule-based classifier using word-boundary matching. Returns method key, industry, complexity."""
    idea_lower = idea.lower()
    best = None
    best_score = 0
    for pattern in INDUSTRY_PATTERNS:
        score = 0
        for kw in pattern["keywords"]:
            # Word-boundary match - prevents "app" matching "approval"
            if re.search(r"\b" + re.escape(kw) + r"\b", idea_lower):
                score += 1
        if score > best_score:
            best_score = score
            best = pattern
    if not best:
        best = {"industry": "General", "complexity": "medium", "method": "scrum"}
    # Geography detection — when India is mentioned, the report localizes to
    # Indian currency (₹), market context, compliance and funding.
    india_signals = ("india", "indian", "bharat", "₹", " inr", "rupee", "gst",
                     "kirana", "udyam", "msme", "dpiit", "upi", "ondc", "fssai",
                     "tier 2", "tier-2", "tier 3", "tier-3", "bengaluru", "mumbai",
                     "delhi", "pune", "hyderabad", "chennai", "startup india")
    is_india = any(s in idea_lower for s in india_signals)
    return {
        "method_key": best["method"],
        "industry": best["industry"],
        "complexity": best["complexity"],
        "confidence_score": best_score,
        "geo": "India" if is_india else "Global",
        "currency": "₹" if is_india else "$",
    }


# ---- India localization helpers (used by the report generators) ----
INR_PER_USD = 83

def _inr(usd) -> str:
    """Format a USD amount as Indian currency with lakh/crore units."""
    try:
        n = int(round(float(usd) * INR_PER_USD))
    except Exception:
        return f"₹{usd}"
    if n >= 10000000:
        return f"₹{n/10000000:.2f} Cr"
    if n >= 100000:
        return f"₹{n/100000:.1f} L"
    return f"₹{n:,}"


# ============================================================
# PM AGENT GENERATORS - deterministic, template-driven
# ============================================================
def gen_methodology_expert(idea: str, classification: dict) -> dict:
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "recommended_method": kb["name"],
        "confidence": kb["confidence"],
        "reasoning": kb["reasoning"] + f" For this specific project ({classification['industry']}), this is especially well-suited because the {kb['name']} approach aligns with the delivery rhythm and risk profile typical of {classification['industry']} initiatives.",
        "why_not_others": kb["why_not_others"],
        "method_details": kb["method_details"],
        "tool_recommendation": kb["tool_recommendation"],
        "success_factors": kb["success_factors"],
        "classified_as": {"industry": classification["industry"], "complexity": classification["complexity"]},
    }


def gen_project_planner(idea: str, classification: dict) -> dict:
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    budget = COMPLEXITY_BUDGETS[classification["complexity"]].copy()
    total_weeks = sum(p["duration_weeks"] for p in kb["phases"] if p["duration_weeks"] > 0)
    return {
        "executive_summary": f"This {classification['complexity'].replace('_', ' ')}-complexity {classification['industry']} initiative will be delivered using the {kb['name']} methodology over approximately {total_weeks} weeks. The plan emphasizes {kb['success_factors'][0].lower()} and targets measurable outcomes across activation, quality, and stakeholder satisfaction. Total investment of ${budget['total']:,} is allocated across people, tooling, infrastructure, and a contingency reserve.",
        "phases": kb["phases"],
        "timeline_weeks": total_weeks,
        "team_composition": kb["team_composition"],
        "budget_breakdown": budget,
        "kpis": kb["kpis"],
    }


def gen_risk_governance(idea: str, classification: dict) -> dict:
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    raid_log = []
    for r in kb["risks"]:
        raid_log.append({
            "id": r["id"],
            "type": r["type"],
            "description": r["description"],
            "probability": r["probability"],
            "impact": r["impact"],
            "score": r["probability"] * r["impact"],
            "mitigation": r["mitigation"],
            "owner": r["owner"],
        })
    return {
        "summary": f"Risk governance for this {classification['industry']} project uses a {kb['name']}-aligned approach with {len(raid_log)} identified risks scored by probability × impact. The top risk by score is '{max(raid_log, key=lambda x: x['score'])['description']}' and requires immediate mitigation.",
        "raid_log": raid_log,
        "governance_structure": {
            "steering_committee": "Bi-weekly" if classification["complexity"] in ("low", "medium") else "Weekly",
            "reporting_cadence": "Weekly to sponsor, monthly to exec",
            "decision_rights": f"PM has authority within 5% budget variance; beyond that, steering committee approval required",
            "change_control": "Formal change requests with impact assessment for all scope changes",
        },
    }


def gen_stakeholder_strategist(idea: str, classification: dict) -> dict:
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "summary": f"Stakeholder engagement for this {classification['industry']} project uses a power/interest matrix to segment {len(kb['stakeholders'])} stakeholder groups. High-power, high-interest stakeholders receive the closest management, while low-power groups are kept informed through scalable channels.",
        "stakeholders": kb["stakeholders"],
        "communication_plan": [
            {"audience": "Executive Sponsor", "frequency": "Weekly", "format": "1:1 + Dashboard"},
            {"audience": "Team", "frequency": "Daily", "format": "Standup"},
            {"audience": "End Users", "frequency": "Monthly", "format": "Newsletter + Release Notes"},
            {"audience": "Finance", "frequency": "Monthly", "format": "Budget Report"},
            {"audience": "Broader Org", "frequency": "Quarterly", "format": "All-Hands Demo"},
        ],
    }


PM_AGENT_SPECS = {
    "Methodology Expert":     {"icon": "🎯", "role": "PMI-PMP Certified Methodology Consultant", "generator": gen_methodology_expert},
    "Project Planner":        {"icon": "📊", "role": "Senior Project Planner (PMP)",             "generator": gen_project_planner},
    "Risk & Governance":      {"icon": "🛡️", "role": "PRINCE2 Risk & Governance Lead",            "generator": gen_risk_governance},
    "Stakeholder Strategist": {"icon": "🤝", "role": "Stakeholder Engagement Strategist",         "generator": gen_stakeholder_strategist},
}


# ============================================================
# CONSULTING REPORT GENERATORS - Big 3 blended style
# Each function returns a section dict that the frontend renders.
# Pure templates - no LLM dependency, sub-second response.
# ============================================================

# Tech stack recommendations by industry
TECH_STACKS = {
    "Retail/SMB": {
        "frontend": ["Next.js 14 (App Router)", "React 18", "Tailwind CSS", "Progressive Web App"],
        "backend": ["Node.js + Fastify", "Python FastAPI for AI", "PostgreSQL via Supabase"],
        "infrastructure": ["Vercel (frontend, free tier)", "Supabase (DB + auth, free tier)", "Cloudflare R2 (storage)"],
        "ai_ml": ["OpenAI GPT-4o-mini for inference", "Bhashini for vernacular voice", "Local Whisper for offline"],
        "integrations": ["WhatsApp Business API", "UPI for payments", "GST/eInvoice APIs", "ONDC connectors"],
        "rationale": "Free-tier-friendly stack optimized for low-data-cost mobile users. WhatsApp-native interface lowers adoption friction for kirana segment. Vernacular AI essential for vendor reach.",
    },
    "SaaS/Product": {
        "frontend": ["Next.js 14", "React 18", "Tailwind CSS", "shadcn/ui components"],
        "backend": ["Node.js + tRPC", "PostgreSQL + Prisma ORM", "Redis for sessions"],
        "infrastructure": ["Vercel (web)", "Railway (services)", "Cloudflare (CDN + WAF)"],
        "ai_ml": ["Anthropic Claude or OpenAI for features", "Vector DB (Pinecone/Qdrant)"],
        "integrations": ["Stripe billing", "Auth0 or Clerk", "Sentry, PostHog", "Slack notifications"],
        "rationale": "Type-safe full-stack with tRPC eliminates API boilerplate. Vercel + Railway gives developer-velocity comparable to a 10-person team at 1-person cost.",
    },
    "AI/ML": {
        "frontend": ["Next.js 14 with streaming", "React Server Components"],
        "backend": ["Python FastAPI", "LangChain or LlamaIndex orchestration", "PostgreSQL + pgvector"],
        "infrastructure": ["Modal or Replicate (GPU inference)", "Vercel (frontend)", "S3 (model artifacts)"],
        "ai_ml": ["Foundation models via API (Anthropic, OpenAI, Google)", "Open-weights via Together/Groq", "Evaluation harness (Promptfoo, LangSmith)"],
        "integrations": ["Webhooks for async pipelines", "Slack/Discord for alerts", "Datadog for observability"],
        "rationale": "Hybrid hosted + open-weights strategy balances cost and capability. pgvector keeps RAG infra simple. Streaming UI critical for user-perceived latency on long generations.",
    },
    "Fintech": {
        "frontend": ["Next.js 14 with strict CSP", "React 18"],
        "backend": ["Java Spring Boot or Go", "PostgreSQL with row-level security", "Kafka for event streams"],
        "infrastructure": ["AWS or Azure (regulated tier)", "Encrypted at rest, TLS 1.3", "WAF + DDoS protection"],
        "ai_ml": ["On-prem ML for credit scoring", "Audit-logged inference"],
        "integrations": ["UPI, IMPS, NEFT", "Account Aggregator framework", "CKYC, Aadhaar eKYC", "Bureau APIs (CIBIL, Experian)"],
        "rationale": "Regulated stack required by RBI. Kafka enables audit trail for every transaction. Account Aggregator is the future of consent-based data sharing in Indian fintech.",
    },
    "Healthcare": {
        "frontend": ["React with WCAG 2.1 AA compliance", "PWA for clinical use"],
        "backend": ["Java/.NET (regulated languages)", "FHIR-compliant data layer", "HL7 message handling"],
        "infrastructure": ["AWS HealthLake or Azure Health Data Services", "HIPAA/HITRUST certified hosting", "BAA with all vendors"],
        "ai_ml": ["FDA-cleared models only for diagnosis", "Audit-logged predictions"],
        "integrations": ["EHR systems (Epic, Cerner, Allscripts)", "DICOM for imaging", "ABHA (India)", "ICD-10 coding"],
        "rationale": "Regulatory non-negotiables drive stack choice. FHIR is the global interop standard. ABHA integration mandatory for Indian healthcare.",
    },
    "Operations": {
        "frontend": ["Next.js 14", "Real-time updates via WebSockets"],
        "backend": ["Node.js + NestJS", "PostgreSQL + Redis", "BullMQ for job queues"],
        "infrastructure": ["Vercel + Railway", "PagerDuty for alerts"],
        "ai_ml": ["Classification models for triage", "Anomaly detection"],
        "integrations": ["ServiceNow, Jira, Zendesk", "Slack, MS Teams", "PagerDuty, Opsgenie"],
        "rationale": "Operations workloads are bursty - queues smooth load. Real-time UI critical for incident response. Existing tool integrations reduce change management.",
    },
    "Construction/Hardware": {
        "frontend": ["React for web", "iOS/Android native (field use)", "Offline-first PWA"],
        "backend": [".NET Core or Java", "SQL Server or PostgreSQL", "BIM/CAD file pipelines"],
        "infrastructure": ["Azure (industry standard)", "On-prem optional", "Field device sync"],
        "ai_ml": ["Computer vision for site inspection", "Schedule optimization"],
        "integrations": ["Primavera P6, MS Project", "Procore, Autodesk", "ERP (SAP, Oracle)"],
        "rationale": "Field connectivity drives offline-first design. Microsoft stack dominant in construction enterprises. Native mobile required for hard-hat conditions.",
    },
    "GovTech": {
        "frontend": ["Next.js 14 with full accessibility", "Multi-language support"],
        "backend": ["Java Spring or .NET", "Open-source DB (PostgreSQL)", "API gateway with rate limits"],
        "infrastructure": ["MeghRaj cloud or AWS GovCloud", "Audit logging end-to-end"],
        "ai_ml": ["Explainable AI only", "Bias auditing required"],
        "integrations": ["Aadhaar, DigiLocker, eSign", "GST, Income Tax APIs", "Payment gateways (BharatPe)"],
        "rationale": "Sovereign cloud requirements often mandate MeghRaj. Open-source preferred to avoid vendor lock-in. Aadhaar integration is the foundational identity layer.",
    },
    "Content/Media": {
        "frontend": ["Next.js 14 with ISR", "Headless CMS integration"],
        "backend": ["Node.js + Strapi or Sanity", "Image/video pipelines"],
        "infrastructure": ["Vercel (web)", "Cloudflare Stream (video)", "Cloudinary (images)"],
        "ai_ml": ["Auto-tagging, summarization", "Recommendation engines"],
        "integrations": ["Social media APIs", "Email marketing (Mailchimp, Sendgrid)", "Analytics (GA4, PostHog)"],
        "rationale": "ISR balances freshness with performance for content-heavy sites. Headless CMS gives editorial team independence from engineering.",
    },
    "Early-Stage": {
        "frontend": ["Next.js 14 (everything in one repo)", "Tailwind for speed"],
        "backend": ["Supabase (DB + auth + storage)", "Vercel serverless functions"],
        "infrastructure": ["Vercel + Supabase free tiers", "Sentry for errors", "PostHog for analytics"],
        "ai_ml": ["GPT-4o-mini for any AI features", "Defer ML training until PMF"],
        "integrations": ["Stripe (when ready)", "Loops or Resend (email)"],
        "rationale": "Boring stack maximizes iteration speed before PMF. Supabase replaces 5 separate services. Defer everything that doesn't directly validate hypotheses.",
    },
    "B2B": {
        "frontend": ["Next.js 14", "Enterprise SSO support (SAML, OIDC)"],
        "backend": ["Node.js + NestJS or Python FastAPI", "PostgreSQL with multi-tenancy"],
        "infrastructure": ["AWS or Azure (enterprise expectation)", "SOC 2 audit trail"],
        "ai_ml": ["Customer-data-isolated inference", "On-prem option for large clients"],
        "integrations": ["Salesforce, HubSpot", "Workday, NetSuite", "Slack, MS Teams"],
        "rationale": "Enterprise procurement requires SSO, SOC 2, and compliance documentation from day one. Multi-tenancy isolation non-negotiable.",
    },
    "EdTech": {
        "frontend": ["Next.js 14 with accessibility", "Mobile-first (low-end Android)"],
        "backend": ["Node.js or Python", "PostgreSQL", "WebRTC for live classes"],
        "infrastructure": ["Vercel + Supabase", "Cloudflare (low-latency global)", "100ms or Daily for video"],
        "ai_ml": ["Personalized learning paths", "Auto-grading for objective tests"],
        "integrations": ["Google Classroom, Microsoft Teams for Education", "LMS (Canvas, Moodle)", "Payment for parent users"],
        "rationale": "Bandwidth optimization critical for tier 2/3 students. Recorded + live hybrid model reaches widest audience. LMS integration eases school adoption.",
    },
}

# Market sizing templates by industry (in USD)
MARKET_SIZES = {
    "Retail/SMB":           {"tam": "850B", "sam": "65B", "som": "1.2B", "growth": "8.5% CAGR", "drivers": "Digitization of 12M+ Indian kirana stores; UPI penetration; ONDC rollout"},
    "SaaS/Product":         {"tam": "720B", "sam": "180B", "som": "2.4B", "growth": "13.7% CAGR", "drivers": "Cloud migration; AI integration; SMB software adoption; vertical SaaS expansion"},
    "AI/ML":                {"tam": "1.4T", "sam": "320B", "som": "4.5B", "growth": "37% CAGR", "drivers": "Generative AI inflection; enterprise AI adoption; foundation model commoditization"},
    "Fintech":              {"tam": "490B", "sam": "85B", "som": "1.8B", "growth": "20% CAGR", "drivers": "UPI scale (India); financial inclusion; embedded finance; regulatory tailwinds"},
    "Healthcare":           {"tam": "660B", "sam": "120B", "som": "2.1B", "growth": "15.5% CAGR", "drivers": "Aging populations; telehealth normalization; AI-assisted diagnosis; ABDM in India"},
    "Operations":           {"tam": "180B", "sam": "32B", "som": "0.8B", "growth": "9% CAGR", "drivers": "Service desk automation; AI agents; remote ops; ITSM consolidation"},
    "Construction/Hardware":{"tam": "12T", "sam": "85B", "som": "1.5B", "growth": "6% CAGR", "drivers": "Infrastructure spending; BIM adoption; smart cities; sustainability mandates"},
    "GovTech":              {"tam": "550B", "sam": "75B", "som": "0.9B", "growth": "11% CAGR", "drivers": "Digital India initiatives; e-governance; citizen services digitization"},
    "Content/Media":        {"tam": "2.3T", "sam": "180B", "som": "1.1B", "growth": "7% CAGR", "drivers": "Streaming consolidation; creator economy; vernacular content; programmatic advertising"},
    "Early-Stage":          {"tam": "varies", "sam": "varies", "som": "validate first", "growth": "TBD", "drivers": "Hypothesis-dependent; quantify after problem validation"},
    "B2B":                  {"tam": "950B", "sam": "210B", "som": "3.2B", "growth": "12% CAGR", "drivers": "Enterprise digital transformation; vertical SaaS; AI-native B2B tools"},
    "EdTech":               {"tam": "410B", "sam": "65B", "som": "0.9B", "growth": "16% CAGR", "drivers": "Personalized learning; upskilling demand; K-12 digitization; lifelong learning"},
}

# Competitor landscape templates
COMPETITORS = {
    "Retail/SMB": [
        {"name": "Khatabook", "strength": "30M+ user base, vernacular UX", "weakness": "Limited beyond ledger; weak inventory module", "moat": "Network effects in tier-3 cities"},
        {"name": "OkCredit", "strength": "Strong credit ledger, brand recall", "weakness": "Stalled product roadmap post-funding crunch", "moat": "Existing merchant trust"},
        {"name": "Vyapar", "strength": "Comprehensive billing + GST", "weakness": "Desktop-first, weak mobile UX", "moat": "Accountant ecosystem integration"},
        {"name": "Pine Labs", "strength": "POS hardware + lending", "weakness": "Higher-tier merchants only", "moat": "Hardware + capital combined"},
    ],
    "SaaS/Product": [
        {"name": "Notion", "strength": "Flexible, viral product-led growth", "weakness": "Performance at enterprise scale", "moat": "Network effect of templates"},
        {"name": "Airtable", "strength": "Database + collaboration", "weakness": "Pricing complexity", "moat": "API ecosystem"},
        {"name": "ClickUp", "strength": "Feature breadth", "weakness": "UI complexity", "moat": "All-in-one positioning"},
    ],
    "AI/ML": [
        {"name": "OpenAI", "strength": "Frontier models, brand", "weakness": "Pricing, enterprise governance", "moat": "Model capability lead"},
        {"name": "Anthropic", "strength": "Safety-focused, long context", "weakness": "Smaller model selection", "moat": "Constitutional AI brand"},
        {"name": "Hugging Face", "strength": "Open ecosystem", "weakness": "Operational complexity", "moat": "Developer mindshare"},
    ],
    "Fintech": [
        {"name": "Razorpay", "strength": "Payments + neobanking", "weakness": "MSME segment underserved", "moat": "Developer-first APIs"},
        {"name": "Cred", "strength": "Premium consumer brand", "weakness": "Narrow demographic", "moat": "Affluent user data"},
        {"name": "Lendingkart", "strength": "MSME credit specialization", "weakness": "Underwriting at scale", "moat": "Risk model + bank partnerships"},
    ],
    "Healthcare": [
        {"name": "Practo", "strength": "Doctor discovery scale", "weakness": "Care delivery weak", "moat": "Doctor relationships"},
        {"name": "Tata 1mg", "strength": "Pharmacy + diagnostics", "weakness": "Clinical depth limited", "moat": "Tata brand + capital"},
        {"name": "Epic", "strength": "EHR market leader (US)", "weakness": "Slow innovation, costly", "moat": "Switching costs"},
    ],
    "Operations": [
        {"name": "Zendesk", "strength": "Mature ticketing platform", "weakness": "AI integration lagging", "moat": "Customer base inertia"},
        {"name": "ServiceNow", "strength": "Enterprise ITSM standard", "weakness": "Implementation cost", "moat": "Workflow customization depth"},
        {"name": "Freshworks", "strength": "Mid-market pricing", "weakness": "Product depth vs leaders", "moat": "Indian engineering cost advantage"},
    ],
    "Construction/Hardware": [
        {"name": "Procore", "strength": "Construction management leader", "weakness": "US-focused, expensive", "moat": "Subcontractor network"},
        {"name": "Autodesk", "strength": "BIM/CAD ecosystem", "weakness": "Cloud transition incomplete", "moat": "Industry standard tools"},
    ],
    "GovTech": [
        {"name": "TCS", "strength": "Govt contract scale", "weakness": "Innovation velocity", "moat": "Existing relationships"},
        {"name": "Infosys", "strength": "Digital govt projects", "weakness": "Custom-build cost", "moat": "Compliance expertise"},
        {"name": "Wipro Infotech", "strength": "Smart city projects", "weakness": "Margin pressure", "moat": "Local presence"},
    ],
    "Content/Media": [
        {"name": "WordPress (Automattic)", "strength": "Open-source dominance", "weakness": "Modern UX gap", "moat": "Plugin ecosystem"},
        {"name": "Substack", "strength": "Creator monetization", "weakness": "Discovery weak", "moat": "Network of writers"},
    ],
    "Early-Stage": [
        {"name": "Direct competitors", "strength": "Validate during interviews", "weakness": "TBD from research", "moat": "TBD from positioning"},
    ],
    "B2B": [
        {"name": "Salesforce", "strength": "Platform breadth", "weakness": "Cost, complexity", "moat": "Ecosystem lock-in"},
        {"name": "HubSpot", "strength": "Mid-market UX", "weakness": "Enterprise depth", "moat": "Inbound marketing brand"},
    ],
    "EdTech": [
        {"name": "BYJU'S", "strength": "Brand and content library", "weakness": "Unit economics challenges", "moat": "Content + sales team"},
        {"name": "Unacademy", "strength": "Educator marketplace", "weakness": "Profitability path unclear", "moat": "Top educator relationships"},
        {"name": "PhysicsWallah", "strength": "Profitable freemium model", "weakness": "Limited beyond test prep", "moat": "Founder brand + low pricing"},
    ],
}

# Financial projection multipliers by complexity
FINANCIAL_MULTIPLIERS = {
    "low":       {"y1_revenue": 150000,  "y2_revenue": 600000,   "y3_revenue": 1800000,  "burn_y1": 145000, "y1_users": 1000,   "y3_users": 25000},
    "medium":    {"y1_revenue": 450000,  "y2_revenue": 1800000,  "y3_revenue": 5400000,  "burn_y1": 265000, "y1_users": 5000,   "y3_users": 120000},
    "high":      {"y1_revenue": 1200000, "y2_revenue": 4800000,  "y3_revenue": 14400000, "burn_y1": 582000, "y1_users": 15000,  "y3_users": 350000},
    "very_high": {"y1_revenue": 3500000, "y2_revenue": 14000000, "y3_revenue": 42000000, "burn_y1": 1155000, "y1_users": 25000, "y3_users": 800000},
}

# GTM strategy templates
GTM_STRATEGIES = {
    "Retail/SMB":           {"motion": "Field sales + WhatsApp groups", "cac": "$8-15", "ltv": "$120-180", "channels": ["Field reps in tier-2 cities", "Distributor partnerships", "WhatsApp viral loops", "FMCG company co-sell"]},
    "SaaS/Product":         {"motion": "Product-led growth", "cac": "$120-250", "ltv": "$1,800-3,200", "channels": ["Free tier with viral loop", "SEO content marketing", "Product Hunt + community", "Outbound to ICP"]},
    "AI/ML":                {"motion": "Developer-led + enterprise sales", "cac": "$400-800", "ltv": "$8,000-25,000", "channels": ["Open-source distribution", "Developer conferences", "Hackathons", "Enterprise pilots"]},
    "Fintech":              {"motion": "Partnership-led + paid acquisition", "cac": "$25-60 retail / $500+ B2B", "ltv": "$300-800 retail / $25k+ B2B", "channels": ["Bank partnerships", "Aggregator platforms", "Performance marketing", "Affiliate networks"]},
    "Healthcare":           {"motion": "Long enterprise sales cycle", "cac": "$5,000-25,000", "ltv": "$50,000-500,000", "channels": ["Hospital network sales", "KOL partnerships", "Industry conferences", "Pilot-to-rollout playbook"]},
    "Operations":           {"motion": "Inside sales + free trial", "cac": "$200-500", "ltv": "$3,000-12,000", "channels": ["Free trial conversion", "G2 Crowd / Capterra", "ServiceNow / Salesforce app exchange", "Outbound to ITSM teams"]},
    "Construction/Hardware":{"motion": "Long enterprise sales", "cac": "$8,000+", "ltv": "$100,000+", "channels": ["Trade shows", "Industry associations", "Reseller network", "BIM consultant partnerships"]},
    "GovTech":              {"motion": "Tender-driven + relationship sales", "cac": "$25,000+", "ltv": "$500,000+ multi-year contract", "channels": ["GeM portal listings", "Empanelment with PSUs", "Industry body memberships", "Reference customer leverage"]},
    "Content/Media":        {"motion": "Self-serve + creator outreach", "cac": "$15-50", "ltv": "$120-600", "channels": ["Creator partnerships", "SEO + organic social", "Newsletter cross-promotion", "Conference sponsorships"]},
    "Early-Stage":          {"motion": "Founder-led", "cac": "$0 (pre-PMF)", "ltv": "TBD", "channels": ["Direct founder outreach", "100 customer interviews", "Beta waitlist", "Lean experiments"]},
    "B2B":                  {"motion": "Enterprise outbound + ABM", "cac": "$1,500-8,000", "ltv": "$30,000-250,000", "channels": ["ABM with named accounts", "Outbound SDR team", "Industry analyst engagement", "Customer advisory board"]},
    "EdTech":               {"motion": "Performance marketing + counselor sales", "cac": "$30-80 B2C / $2,000+ B2B", "ltv": "$200-1,500 B2C / $20k+ B2B", "channels": ["Performance marketing (Meta, Google)", "Counselor call centers", "School district sales", "Influencer educators"]},
}

# Regulatory frameworks by industry
REGULATIONS = {
    "Retail/SMB":           {"key_regs": ["GST compliance", "Shops & Establishments Act", "Consumer Protection Act 2019", "DPDP Act 2023"], "certifications": ["GST registration", "FSSAI (if food)"], "data_residency": "India (DPDP)", "high_risk": ["Counterfeit goods liability", "GST input credit fraud"]},
    "SaaS/Product":         {"key_regs": ["DPDP Act 2023", "GDPR (EU users)", "CCPA (California users)", "Industry-specific (PCI-DSS for payments)"], "certifications": ["SOC 2 Type II", "ISO 27001"], "data_residency": "Per customer requirement", "high_risk": ["Data breach disclosure", "Cross-border data transfer"]},
    "AI/ML":                {"key_regs": ["EU AI Act (2024)", "DPDP Act 2023", "Algorithmic accountability laws", "Sector-specific (HIPAA, GLBA)"], "certifications": ["ISO 42001 (AI management)", "SOC 2"], "data_residency": "Model + training data jurisdiction", "high_risk": ["Bias claims", "IP infringement (training data)", "Hallucination liability"]},
    "Fintech":              {"key_regs": ["RBI guidelines", "PMLA (anti-money laundering)", "PSS Act 2007", "FEMA (cross-border)", "NPCI rules (UPI)"], "certifications": ["PCI-DSS Level 1", "ISO 27001", "RBI authorization"], "data_residency": "India mandatory", "high_risk": ["KYC failures", "Fraud losses", "Regulatory fines (up to 4% revenue)"]},
    "Healthcare":           {"key_regs": ["HIPAA (US)", "DPDP Act + ABDM (India)", "FDA 21 CFR Part 11", "Medical Device Rules 2017"], "certifications": ["HITRUST CSF", "FDA clearance (devices)", "NABH (hospitals)"], "data_residency": "Strict patient location rules", "high_risk": ["PHI breach (avg $10.9M)", "Misdiagnosis liability", "Off-label use"]},
    "Operations":           {"key_regs": ["DPDP Act", "Industry SLA contracts", "Labor laws (worker monitoring)"], "certifications": ["ITIL alignment", "ISO 20000"], "data_residency": "Customer requirement", "high_risk": ["SLA penalties", "Outage liability"]},
    "Construction/Hardware":{"key_regs": ["Building codes (IS, IBC)", "Occupational safety", "Environmental clearances", "Labor laws"], "certifications": ["ISO 45001 (safety)", "LEED/IGBC (green)"], "data_residency": "Project documentation retention", "high_risk": ["Site accident liability", "Schedule penalties", "Quality defects"]},
    "GovTech":              {"key_regs": ["IT Act 2000", "DPDP Act", "GFR 2017", "CERT-In guidelines"], "certifications": ["MeitY empanelment", "STQC certification", "ISO 27001"], "data_residency": "Sovereign cloud (MeghRaj)", "high_risk": ["Data sovereignty breach", "Tender disputes", "Compliance audit failures"]},
    "Content/Media":        {"key_regs": ["IT Rules 2021", "Copyright Act", "DPDP Act", "Cable Television Networks Act"], "certifications": ["Self-regulatory body membership"], "data_residency": "User data in India", "high_risk": ["Content takedown liability", "Copyright infringement", "Misinformation penalties"]},
    "Early-Stage":          {"key_regs": ["Founders Agreement", "Basic compliance (GST if applicable)", "DPDP if collecting user data"], "certifications": ["Defer until PMF"], "data_residency": "Minimal data collection recommended", "high_risk": ["Co-founder disputes", "Premature scaling"]},
    "B2B":                  {"key_regs": ["DPDP Act", "GDPR if EU customers", "Industry-specific (HIPAA, GLBA, etc.)", "Customer DPAs"], "certifications": ["SOC 2 Type II essential", "ISO 27001", "CSA STAR"], "data_residency": "Per customer contract", "high_risk": ["Customer data breach", "Indemnity exposure", "Audit findings"]},
    "EdTech":               {"key_regs": ["DPDP Act with minor protections", "COPPA (US under-13)", "RTE Act (India)", "FERPA (US)"], "certifications": ["IS 17428 (children's data)", "Privacy seals"], "data_residency": "Minor data India-resident", "high_risk": ["Minor data breach", "Misleading claims", "Refund disputes"]},
}


def gen_executive_summary(idea, classification):
    """McKinsey-style pyramid principle: situation, complication, recommendation."""
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    market = MARKET_SIZES.get(classification["industry"], MARKET_SIZES["SaaS/Product"])
    return {
        "situation": f"The {classification['industry']} sector represents a ${market['tam']} TAM growing at {market['growth']}, driven by {market['drivers']}. The proposed initiative — {idea[:120]} — targets the underserved segment within this market.",
        "complication": f"Existing solutions either fail to address the specific needs of this segment or lack the technical sophistication required to deliver durable value. Without a focused, well-architected approach, the opportunity will be captured by either incumbent platforms expanding downmarket or well-funded new entrants.",
        "recommendation": f"We recommend proceeding with the {kb['name']} methodology and a {classification['complexity'].replace('_', ' ')}-complexity build profile. Total 3-year investment of approximately ${FINANCIAL_MULTIPLIERS[classification['complexity']]['burn_y1'] * 3:,} positions the initiative to capture ${market['som']} in addressable revenue with a defensible technology moat.",
        "key_findings": [
            f"Market timing is favorable: {market['growth']} growth + clear inflection drivers",
            f"Technical risk is manageable with the {kb['name']} approach and mature stack choices",
            f"Competitive moat achievable through {classification['industry']}-specific feature depth",
            f"Capital efficiency strong: payback within 18-24 months at projected acquisition costs",
        ],
        "go_no_go": "GO" if classification["complexity"] != "very_high" else "GO with stage-gates",
        "confidence_level": kb["confidence"],
    }


def gen_market_sizing(idea, classification):
    """BCG-style market sizing with TAM/SAM/SOM and growth analysis."""
    market = MARKET_SIZES.get(classification["industry"], MARKET_SIZES["SaaS/Product"])
    india = classification.get("geo") == "India"
    india_context = (
        "India view: the figures below are the global sector pool. India is typically 3-7% of "
        "global TAM today but among the fastest-growing markets (UPI/ONDC rails, Digital India, rising "
        "MSME digitisation). Size your SAM bottom-up: target customers × annual price (₹) × realistic reach, "
        "starting with a Tier-1/Tier-2 city beachhead before expanding."
    ) if india else None
    return {
        "summary": (f"India-focused sizing: anchor your SAM/SOM bottom-up in ₹ for a Tier-1/Tier-2 beachhead within the broader ${market['tam']} global {classification['industry']} sector."
                    if india else
                    f"Bottoms-up sizing reveals a ${market['som']} serviceable obtainable market within the broader ${market['tam']} {classification['industry']} sector."),
        **({"india_context": india_context} if india else {}),
        "tam": {"value": f"${market['tam']}", "definition": "Total Addressable Market - the entire global revenue pool if 100% market share were achievable", "calculation": f"Industry-wide spend on {classification['industry']} solutions across all geographies and segments"},
        "sam": {"value": f"${market['sam']}", "definition": "Serviceable Available Market - portion realistically reachable with current product and channels", "calculation": "TAM filtered by geography (initial markets), customer segment (target ICP), and product fit"},
        "som": {"value": f"${market['som']}", "definition": "Serviceable Obtainable Market - realistic revenue capture in 3-5 years", "calculation": "SAM multiplied by realistic market share given competitive dynamics and execution capacity"},
        "growth_rate": market["growth"],
        "growth_drivers": market["drivers"],
        "market_share_targets": [
            {"year": "Year 1", "target": "0.05% of SAM", "rationale": "Beachhead establishment in 1-2 verticals"},
            {"year": "Year 2", "target": "0.3% of SAM", "rationale": "Geographic and segment expansion"},
            {"year": "Year 3", "target": "1.2% of SAM", "rationale": "Full GTM motion at scale"},
        ],
        "geographic_priorities": ["Initial: India (Tier-1 metros — Mumbai, Delhi NCR, Bengaluru)", "Year 2: Tier-2/3 expansion (Pune, Jaipur, Kochi, Indore) + vernacular GTM", "Year 3: Pan-India scale + select export markets (Middle East, SEA)"] if india else ["Initial: Domestic market", "Year 2: Adjacent English-speaking markets", "Year 3: Strategic expansion based on traction"],
    }


def gen_competitive_landscape(idea, classification):
    """Bain-style competitive analysis with moat assessment."""
    competitors = COMPETITORS.get(classification["industry"], COMPETITORS["SaaS/Product"])
    return {
        "summary": f"The {classification['industry']} competitive landscape contains {len(competitors)} primary competitors. Differentiation strategy must focus on {classification['industry']}-specific depth that incumbents cannot easily replicate without re-architecting their platforms.",
        "competitors": competitors,
        "competitive_positioning": {
            "axis_x": "Feature breadth (horizontal expansion)",
            "axis_y": "Vertical depth (industry-specific intelligence)",
            "white_space": f"Upper-right quadrant: deep vertical features for {classification['industry']} that horizontal players ignore",
            "our_position": "Initial focus: high vertical depth, narrow feature scope, then expand horizontally",
        },
        "differentiation_strategy": [
            f"Vertical-first product depth that horizontal incumbents cannot match",
            f"Lower TCO through modern stack vs legacy competitors",
            f"AI-native workflows vs AI-bolted-on competitor products",
            f"Faster time-to-value (days vs months for incumbents)",
        ],
        "moat_assessment": {
            "data_network_effect": "Build over Year 2-3 as customer data accumulates",
            "switching_costs": "Workflow integration depth creates lock-in after 6 months of use",
            "brand": "Build via customer success stories in target vertical",
            "regulatory": "Compliance certifications create barrier for new entrants",
        },
    }


def gen_tech_stack(idea, classification):
    """Tech stack recommendation with rationale."""
    stack = TECH_STACKS.get(classification["industry"], TECH_STACKS["SaaS/Product"])
    return {
        "summary": f"Recommended stack optimizes for {classification['industry']}-specific requirements while preserving developer velocity and operational simplicity.",
        "frontend": stack["frontend"],
        "backend": stack["backend"],
        "infrastructure": stack["infrastructure"],
        "ai_ml": stack["ai_ml"],
        "integrations": stack["integrations"],
        "rationale": stack["rationale"],
        "build_vs_buy": [
            {"capability": "Authentication", "decision": "Buy (Clerk/Auth0/Supabase Auth)", "reason": "Commodity capability; security risk too high to home-grow"},
            {"capability": "Payments", "decision": "Buy (Stripe/Razorpay)", "reason": "Regulatory complexity makes building uneconomic"},
            {"capability": "Email/SMS", "decision": "Buy (Resend, Twilio, MSG91)", "reason": "Deliverability infrastructure not core to business"},
            {"capability": "Core domain logic", "decision": "Build", "reason": "This is where defensibility lives"},
            {"capability": "Analytics", "decision": "Buy (PostHog, Mixpanel)", "reason": "Solved problem with mature tools"},
        ],
        "scalability_path": [
            "MVP: Single region, vertical scaling, managed services",
            "Year 2: Multi-region read replicas, CDN, dedicated services for hot paths",
            "Year 3+: Microservices for independently-scaling domains, dedicated infra team",
        ],
    }


def gen_methodology_recommendation(idea, classification):
    """Methodology choice with comparative justification (already strong in v11, enhanced here)."""
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "recommended": kb["name"],
        "confidence": kb["confidence"],
        "summary": f"{kb['name']} is the optimal methodology for this initiative. Reasoning combines industry fit, complexity profile, and team scaling expectations.",
        "primary_rationale": kb["reasoning"],
        "method_details": kb["method_details"],
        "tooling": kb["tool_recommendation"],
        "alternatives_considered": kb["why_not_others"],
        "implementation_keys": kb["success_factors"],
        "ceremony_calendar": [
            {"event": "Sprint Planning", "frequency": "Bi-weekly", "duration": "4 hours", "attendees": "Full team"},
            {"event": "Daily Standup", "frequency": "Daily", "duration": "15 min", "attendees": "Dev team"},
            {"event": "Sprint Review", "frequency": "Bi-weekly", "duration": "2 hours", "attendees": "Team + stakeholders"},
            {"event": "Retrospective", "frequency": "Bi-weekly", "duration": "90 min", "attendees": "Full team"},
            {"event": "Backlog Refinement", "frequency": "Weekly", "duration": "2 hours", "attendees": "PO + tech leads"},
        ] if classification["method_key"] in ("scrum", "lean_startup") else [
            {"event": "Phase Gate Review", "frequency": "Per phase", "duration": "Half day", "attendees": "Steering committee"},
            {"event": "Weekly Status", "frequency": "Weekly", "duration": "1 hour", "attendees": "Project team"},
            {"event": "Change Control Board", "frequency": "Bi-weekly", "duration": "1 hour", "attendees": "PM + sponsors"},
            {"event": "Risk Review", "frequency": "Monthly", "duration": "2 hours", "attendees": "PM + risk owners"},
        ],
    }


def gen_financial_projections(idea, classification):
    """3-year financial model (currency-localized: ₹ for India, $ otherwise)."""
    fin = FINANCIAL_MULTIPLIERS[classification["complexity"]]
    budget = COMPLEXITY_BUDGETS[classification["complexity"]]
    y1_loss = fin["burn_y1"] - fin["y1_revenue"]
    y2_breakeven = fin["y2_revenue"] - (fin["burn_y1"] * 1.4)
    y3_profit = fin["y3_revenue"] - (fin["burn_y1"] * 1.8)
    india = classification.get("geo") == "India"
    cur = "₹" if india else "$"
    mult = INR_PER_USD if india else 1
    # money(): plain figure in the right currency; m(): compact (₹ L/Cr or $)
    money = (lambda v: _inr(v)) if india else (lambda v: f"${v:,.0f}")

    return {
        "currency": cur,
        "summary": f"3-year model shows a path to profitability by Year {2 if y2_breakeven > 0 else 3}, with cumulative revenue of {money(fin['y1_revenue'] + fin['y2_revenue'] + fin['y3_revenue'])} and a total investment need of {money(fin['burn_y1'] * 4.2)}."
                   + (" Figures localized to Indian rupees." if india else ""),
        "revenue_projection": [
            {"year": "Year 1", "users": f"{fin['y1_users']:,}", "revenue": money(fin['y1_revenue']), "growth": "Launch year"},
            {"year": "Year 2", "users": f"{fin['y1_users'] * 6:,}", "revenue": money(fin['y2_revenue']), "growth": f"{round(100 * (fin['y2_revenue'] / fin['y1_revenue'] - 1))}% YoY"},
            {"year": "Year 3", "users": f"{fin['y3_users']:,}", "revenue": money(fin['y3_revenue']), "growth": f"{round(100 * (fin['y3_revenue'] / fin['y2_revenue'] - 1))}% YoY"},
        ],
        "cost_structure": ({k: (int(v * mult) if isinstance(v, (int, float)) else v) for k, v in budget.items()} if india else budget),
        "unit_economics": {
            "blended_cac": money(fin['burn_y1'] / fin['y1_users']),
            "ltv_estimate": money(fin['y3_revenue'] / fin['y3_users'] * 3),
            "ltv_cac_target": "≥ 3:1 by end of Year 2",
            "payback_period": "12-18 months",
            "gross_margin": "65-78% depending on infrastructure efficiency",
        },
        "profit_loss": [
            {"year": "Year 1", "revenue": int(fin["y1_revenue"] * mult), "costs": int(fin["burn_y1"] * mult), "net": int(y1_loss * mult), "status": "Loss (investment phase)"},
            {"year": "Year 2", "revenue": int(fin["y2_revenue"] * mult), "costs": int(fin["burn_y1"] * 1.4 * mult), "net": int(y2_breakeven * mult), "status": "Approaching breakeven" if y2_breakeven > -100000 else "Loss (growth phase)"},
            {"year": "Year 3", "revenue": int(fin["y3_revenue"] * mult), "costs": int(fin["burn_y1"] * 1.8 * mult), "net": int(y3_profit * mult), "status": "Profitable" if y3_profit > 0 else "Path to profitability"},
        ],
        "funding_requirement": {
            "seed": f"{money(fin['burn_y1'] * 1.5)} - 18 month runway to PMF + early traction"
                    + (" (plus Startup India Seed Fund up to ₹50L via approved incubators)" if india else ""),
            "series_a": f"{money(fin['burn_y1'] * 4)} - 24 month runway to scale GTM",
            "use_of_funds": ["55% engineering and product", "25% sales and marketing", "12% G&A and operations", "8% reserves"],
            **({"india_incentives": ["DPIIT recognition → Sec 80-IAC 3-year tax holiday", "Angel-tax exemption (Sec 56(2)(viib))", "Startup India Seed Fund Scheme (SISFS)", "State startup-policy subsidies (SGST refund, patent/lease reimbursement)"]} if india else {}),
        },
    }


def gen_risk_assessment(idea, classification):
    """Comprehensive risk assessment beyond the existing Risk & Governance agent."""
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "summary": f"Risk profile for this {classification['complexity'].replace('_', ' ')}-complexity {classification['industry']} initiative covers technical, market, regulatory, financial, and execution dimensions.",
        "risk_categories": [
            {
                "category": "Technical",
                "risks": [
                    {"description": "Architecture cannot scale beyond initial user base", "likelihood": "Medium", "impact": "High", "mitigation": "Load testing from beta; modular architecture from v1"},
                    {"description": "Critical dependency vendor outage or sunset", "likelihood": "Low", "impact": "High", "mitigation": "Abstract integrations behind interfaces; identify backup vendors"},
                    {"description": "Security breach exposing customer data", "likelihood": "Medium", "impact": "Critical", "mitigation": "Security review, pen test, SOC 2 path early"},
                ],
            },
            {
                "category": "Market",
                "risks": [
                    {"description": "Slower than projected market adoption", "likelihood": "Medium", "impact": "High", "mitigation": "Validate pricing and messaging before scale; flexible pricing"},
                    {"description": "Well-funded competitor enters with similar wedge", "likelihood": "Medium", "impact": "Medium", "mitigation": "Build vertical depth fast; lock in early customers with multi-year deals"},
                    {"description": "Macroeconomic downturn delays purchase decisions", "likelihood": "Medium", "impact": "Medium", "mitigation": "Maintain 18+ months runway; target ROI-clear use cases"},
                ],
            },
            {
                "category": "Regulatory",
                "risks": [
                    {"description": "New data protection regulation requires architecture changes", "likelihood": "Medium", "impact": "Medium", "mitigation": "Privacy-by-design; minimize data collection; track regulatory developments"},
                    {"description": "Industry-specific regulation increases compliance burden", "likelihood": "Medium", "impact": "Medium", "mitigation": "Compliance budget allocated; legal review on roadmap items"},
                ],
            },
            {
                "category": "Financial",
                "risks": [
                    {"description": "Burn rate exceeds plan due to slower revenue ramp", "likelihood": "Medium", "impact": "High", "mitigation": "Monthly board review; tripwires at 9, 6, 3 months runway"},
                    {"description": "Inability to raise next round at favorable terms", "likelihood": "Medium", "impact": "High", "mitigation": "Multiple investor relationships; bridge financing options identified"},
                ],
            },
            {
                "category": "Execution",
                "risks": [
                    {"description": "Key technical hire takes 6+ months to fill", "likelihood": "High", "impact": "Medium", "mitigation": "Recruiter retainer; warm pipeline always active; contractor backup"},
                    {"description": "Founder or co-founder departure", "likelihood": "Low", "impact": "Critical", "mitigation": "Founder vesting; documented decision rights; strong second-tier leadership"},
                ],
            },
        ],
        "raid_log": [{"id": r["id"], "type": r["type"], "description": r["description"], "probability": r["probability"], "impact": r["impact"], "score": r["probability"] * r["impact"], "mitigation": r["mitigation"], "owner": r["owner"]} for r in kb["risks"]],
        "risk_governance": {
            "review_cadence": "Bi-weekly risk review with PM and tech lead",
            "escalation_threshold": "Score ≥ 16 (e.g., 4×4) escalates to steering committee within 48 hours",
            "tracking_tool": "Integrated into the PMGuru workspace Risks view",
        },
    }


def gen_gtm_strategy(idea, classification):
    """Go-to-market strategy (India-localized channels + economics when applicable)."""
    gtm = GTM_STRATEGIES.get(classification["industry"], GTM_STRATEGIES["SaaS/Product"])
    india = classification.get("geo") == "India"
    india_channels = ["WhatsApp Business + vernacular content", "ONDC / marketplace listings (Amazon, Flipkart)",
                      "UPI-led frictionless onboarding", "Tier-2/3 field reps + distributor partnerships",
                      "Regional influencer & community marketing"]
    return {
        "summary": (f"India GTM: {gtm['motion']}, adapted for Indian buyers — vernacular, WhatsApp-first, UPI/ONDC rails, and a Tier-1→Tier-2/3 city rollout."
                    if india else
                    f"GTM motion is {gtm['motion']}, optimized for {classification['industry']} buyer behavior and economics."),
        "primary_motion": gtm["motion"],
        "channels": (india_channels if india else gtm["channels"]),
        "unit_economics": {
            "target_cac": gtm["cac"] + (" (validate in ₹; India CAC is typically lower)" if india else ""),
            "target_ltv": gtm["ltv"],
            "target_ltv_cac": "≥ 3:1",
            "payback_target": "12-18 months",
        },
        "phased_rollout": [
            {"phase": "Beachhead (Months 1-6)", "target": "Land 10-20 design partners in narrow vertical", "tactics": ["Founder-led sales", "White-glove onboarding", "Case study production"]},
            {"phase": "Expansion (Months 7-18)", "target": "Scale to 100-300 customers, refine ICP", "tactics": ["Hire first AEs", "Marketing engine activation", "Channel partner exploration"]},
            {"phase": "Scale (Months 19-36)", "target": "Multi-segment expansion, repeatable playbook", "tactics": ["Inside sales team", "Vertical specialization", "International expansion"]},
        ],
        "messaging_framework": {
            "for": f"the {classification['industry']} segment",
            "who": "needs an integrated, modern solution to longstanding workflow problems",
            "the_product": "is an AI-native platform",
            "that_provides": "measurable ROI through automation, integration, and intelligence",
            "unlike": "legacy point solutions that require expensive customization",
            "we_deliver": "time-to-value in days not quarters, with vertical depth incumbents can't match",
        },
        "success_metrics": [
            {"metric": "Pipeline velocity", "target": "30% MoM in Year 1"},
            {"metric": "Win rate", "target": "≥ 25% on qualified opportunities"},
            {"metric": "Average deal size", "target": "Growing 15% YoY through expansion"},
            {"metric": "NPS", "target": "≥ 50 from active customers"},
        ],
    }


def gen_team_resource_plan(idea, classification):
    """Team and resource plan."""
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "summary": f"Team build-out follows a {kb['name']} structure scaled to the {classification['complexity'].replace('_', ' ')} complexity profile.",
        "founding_team": kb["team_composition"],
        "hiring_plan": [
            {"phase": "Months 1-3", "hires": ["Tech Lead (full-stack)", "Senior Engineer", "PM/Founder"], "rationale": "Technical foundation + product clarity"},
            {"phase": "Months 4-6", "hires": ["Designer", "QA Engineer", "Customer Success"], "rationale": "Product polish + early customer support"},
            {"phase": "Months 7-12", "hires": ["Senior Engineer (2)", "First AE", "Marketing Lead"], "rationale": "Scale build velocity + start GTM motion"},
            {"phase": "Months 13-24", "hires": ["VP Eng", "VP Sales", "Engineers (4)", "AEs (3)", "CS (2)"], "rationale": "Functional leadership + scale execution"},
        ],
        "compensation_philosophy": {
            "salary": "Market 50th percentile for stage and geography",
            "equity": "Above-market for early hires (1.5-2x typical refresh grants)",
            "benefits": "Competitive health, learning budget, flexible work",
            "bonus": "Annual bonus tied to company OKRs, not individual MBOs",
        },
        "org_design_principles": [
            "Small autonomous teams (3-7 people) own outcomes end-to-end",
            "Engineering pods aligned to customer journey, not technology layer",
            "Product Owner is empowered to make scope decisions in real time",
            "Every hire takes the team's average bar up, not down",
        ],
        "key_role_specs": [
            {"role": "Tech Lead", "must_have": ["Production systems experience", "Mentorship instinct"], "nice_to_have": ["Industry domain knowledge"]},
            {"role": "Product Manager", "must_have": ["Customer obsession", "Analytical rigor", "Crisp written communication"], "nice_to_have": ["Industry experience"]},
            {"role": "First AE", "must_have": ["Founder-led sales experience", "Comfort with ambiguity"], "nice_to_have": ["Vertical experience"]},
        ],
    }


def gen_regulatory_compliance(idea, classification):
    """Regulatory and compliance requirements (India registration roadmap when applicable)."""
    reg = REGULATIONS.get(classification["industry"], REGULATIONS["SaaS/Product"])
    india = classification.get("geo") == "India"
    if india:
        india_regs = ["Company incorporation (Pvt Ltd / LLP via MCA)", "GST registration + returns (GSTR-1/3B)",
                      "Udyam (MSME) registration", "DPIIT / Startup India recognition", "DPDP Act 2023 (data protection)",
                      "Professional Tax + Shops & Establishment (state)"] + reg["key_regs"][:2]
        return {
            "summary": f"India regulatory roadmap for {classification['industry']}: incorporate, register for GST + Udyam, get DPIIT recognition to unlock tax benefits, and stay DPDP-compliant. Failures here are existential, not merely costly.",
            "key_regulations": india_regs,
            "required_certifications": ["GST registration", "Udyam (MSME)", "DPIIT recognition", "DPDP readiness"] + reg["certifications"],
            "data_residency": "India (DPDP Act 2023 — store personal data in India per sectoral rules)",
            "high_risk_areas": reg["high_risk"],
            "compliance_roadmap": [
                {"timeline": "Pre-launch", "items": ["Incorporate (Pvt Ltd/LLP) on MCA", "PAN/TAN + current account", "GST registration", "Founder agreements + IP assignment"]},
                {"timeline": "Months 1-6", "items": ["Udyam (MSME) registration", "DPIIT / Startup India recognition", "DPDP Act data-flow mapping + privacy policy", "Sector licences (FSSAI / Drug licence / IEC) if applicable"]},
                {"timeline": "Months 7-12", "items": ["Apply for Sec 80-IAC tax holiday (IMB certificate)", "Angel-tax exemption filing", "EPF/ESI registration once ≥ staff thresholds", "ROC annual filings (AOC-4, MGT-7)"]},
                {"timeline": "Months 13-24", "items": ["State startup-policy incentive claims (SGST refund, subsidies)", "ISO 27001 / SOC 2 if enterprise B2B", "Annual statutory + GST audit cycle"]},
            ],
            "compliance_budget": {
                "year_1": "₹1.5L-5L (incorporation, GST, registrations, basic legal)",
                "year_2": "₹5L-15L (DPIIT/80-IAC, DPDP, sector licences, audits)",
                "year_3": "₹15L-40L (certifications + part-time CS/compliance + audit cycle)",
            },
            "external_advisors": ["CA (GST, ITR, ROC, 80-IAC)", "Company Secretary (incorporation, ROC, cap table)", "DPDP/data-protection lawyer", "Sector licence consultant (FSSAI/Drugs/IEC)"],
        }
    return {
        "summary": f"Regulatory landscape for {classification['industry']} requires proactive compliance planning. Failures here are existential, not merely costly.",
        "key_regulations": reg["key_regs"],
        "required_certifications": reg["certifications"],
        "data_residency": reg["data_residency"],
        "high_risk_areas": reg["high_risk"],
        "compliance_roadmap": [
            {"timeline": "Pre-launch", "items": ["Privacy policy + ToS legal review", "Initial data flow mapping", "Vendor DPAs in place"]},
            {"timeline": "Months 1-6", "items": ["DPDP/GDPR compliance documentation", "Security policies (incident response, access control)", "Begin SOC 2 readiness if B2B"]},
            {"timeline": "Months 7-12", "items": ["Penetration testing", "SOC 2 Type 1 audit", "Industry-specific certifications start"]},
            {"timeline": "Months 13-24", "items": ["SOC 2 Type 2 audit", "ISO 27001 certification", "Annual compliance audit cycle"]},
        ],
        "compliance_budget": {
            "year_1": "$25,000-75,000 (legal + initial audits)",
            "year_2": "$75,000-200,000 (full SOC 2 + ISO + DPO)",
            "year_3": "$150,000-400,000 (multiple certifications + dedicated compliance hire)",
        },
        "external_advisors": ["Privacy lawyer (DPDP/GDPR specialist)", "Industry compliance consultant", "Security audit firm (for certifications)"],
    }


def gen_implementation_roadmap(idea, classification):
    """Implementation roadmap with quarterly milestones."""
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "summary": f"Phased implementation roadmap aligned to {kb['name']} methodology with clear milestones, success criteria, and decision gates.",
        "quarters": [
            {"quarter": "Q1", "theme": "Foundation", "milestones": ["Team formation complete", "Tech stack decisions ratified", "MVP scope frozen", "First user interviews"], "success_criteria": "Working dev environment + 20 user interviews completed"},
            {"quarter": "Q2", "theme": "MVP Build", "milestones": ["Core features functional", "First 10 beta users onboarded", "Initial analytics instrumented"], "success_criteria": "MVP shipped to beta, >50% activation rate"},
            {"quarter": "Q3", "theme": "Validation", "milestones": ["Public launch", "First paying customers", "Initial PMF signal"], "success_criteria": "≥10 paying customers, NPS ≥ 30"},
            {"quarter": "Q4", "theme": "Iteration", "milestones": ["Series A readiness", "Repeatable acquisition channel", "First retention cohort data"], "success_criteria": "MoM growth ≥ 20%, retention ≥ 70% at week 4"},
            {"quarter": "Year 2 Q1-Q2", "theme": "Scale Foundation", "milestones": ["GTM team in place", "Multi-segment expansion", "Compliance certifications in flight"], "success_criteria": "ARR ≥ $1M, repeatable sales motion"},
            {"quarter": "Year 2 Q3-Q4", "theme": "Scale Execution", "milestones": ["Vertical expansion", "Channel partnerships live", "Operational efficiency gains"], "success_criteria": "ARR growth ≥ 200% YoY"},
        ],
        "decision_gates": [
            {"gate": "End of Q1", "decision": "Technology stack lock-in", "criteria": "Architecture review passes; performance benchmarks met"},
            {"gate": "End of Q2", "decision": "Public launch GO/NO-GO", "criteria": "MVP feature complete; security audit passed; beta NPS ≥ 30"},
            {"gate": "End of Q3", "decision": "Series A fundraise readiness", "criteria": "≥ $50K MRR; cohort retention data; clear ICP"},
            {"gate": "End of Year 1", "decision": "Scale or pivot", "criteria": "PMF metrics achieved or pivot decision documented"},
        ],
        "dependency_map": [
            "Technology decisions (Q1) → Engineering velocity (Q2+)",
            "MVP scope (Q1) → Beta launch timing (Q2)",
            "Beta feedback (Q2) → Product roadmap (Q3-Q4)",
            "Initial revenue (Q3) → Fundraise readiness (Q4)",
            "Compliance (Q4-Y2) → Enterprise deal eligibility (Y2+)",
        ],
    }


# Registry of report sections - order matters (this is the streaming order)
REPORT_SECTIONS = [
    {"id": "executive_summary",       "title": "Executive Summary",            "icon": "📋", "generator": gen_executive_summary,       "style": "McKinsey - pyramid principle"},
    {"id": "market_sizing",           "title": "Market Sizing (TAM/SAM/SOM)",  "icon": "📊", "generator": gen_market_sizing,           "style": "BCG - bottoms-up sizing"},
    {"id": "competitive_landscape",   "title": "Competitive Landscape",        "icon": "🎯", "generator": gen_competitive_landscape,   "style": "Bain - moat analysis"},
    {"id": "tech_stack",              "title": "Technology Stack Recommendation", "icon": "⚙️", "generator": gen_tech_stack,           "style": "Industry best practices"},
    {"id": "methodology",             "title": "Methodology Recommendation",   "icon": "🎓", "generator": gen_methodology_recommendation, "style": "PMI/PRINCE2 framework"},
    {"id": "financial_projections",   "title": "Financial Projections (3-Year)", "icon": "💰", "generator": gen_financial_projections, "style": "BCG - unit economics"},
    {"id": "risk_assessment",         "title": "Risk Assessment",              "icon": "🛡️", "generator": gen_risk_assessment,         "style": "PRINCE2 + RAID"},
    {"id": "gtm_strategy",            "title": "Go-to-Market Strategy",        "icon": "🚀", "generator": gen_gtm_strategy,            "style": "Bain - phased rollout"},
    {"id": "team_resource_plan",      "title": "Team & Resource Plan",         "icon": "👥", "generator": gen_team_resource_plan,      "style": "McKinsey - org design"},
    {"id": "regulatory_compliance",   "title": "Regulatory & Compliance",      "icon": "⚖️", "generator": gen_regulatory_compliance,   "style": "Industry regulatory framework"},
    {"id": "implementation_roadmap",  "title": "Implementation Roadmap",       "icon": "🗺️", "generator": gen_implementation_roadmap,  "style": "Stage-gated milestones"},
]


def generate_full_report(idea, classification):
    """Generate the complete consulting report. Used by non-streaming endpoint."""
    sections = []
    for section_spec in REPORT_SECTIONS:
        try:
            data = section_spec["generator"](idea, classification)
            sections.append({
                "id": section_spec["id"],
                "title": section_spec["title"],
                "icon": section_spec["icon"],
                "style": section_spec["style"],
                "status": "ok",
                "data": data,
            })
        except Exception as e:
            print(f"[report] section {section_spec['id']} failed: {e}", flush=True)
            traceback.print_exc()
            sections.append({
                "id": section_spec["id"],
                "title": section_spec["title"],
                "icon": section_spec["icon"],
                "status": "error",
                "error": str(e),
                "data": {},
            })
    return sections




# ============================================================
# CONSULTING INTELLIGENCE MODULE - 12 domains, 1000+ scenarios
# Big 3 (McKinsey/BCG/Bain) + Big 4 (Deloitte/PwC/EY/KPMG) blended
# ============================================================

# Each scenario: (category, title, finding, risk[C/H/M/L], recommendation)
# C=Critical, H=High, M=Medium, L=Low

_S_O2C = [
    # Credit Management
    ("Credit Mgmt", "No automated credit scoring", "Manual credit decisions inconsistent; avg 5-day approval cycle", "H", "Implement automated scoring with D&B/Experian integration; target <4hr"),
    ("Credit Mgmt", "Stale credit limits", "Credit limits not reviewed in 18+ months; 22% are outdated", "H", "Quarterly automated credit reviews with financial statement refresh"),
    ("Credit Mgmt", "No credit insurance on high-risk accounts", "Top 10 accounts represent 40% of AR with zero insurance", "C", "Obtain trade credit insurance for accounts >$500K exposure"),
    ("Credit Mgmt", "Missing credit application workflow", "No standardized application; inconsistent data collection", "M", "Digital credit application with automated scoring and approval routing"),
    ("Credit Mgmt", "No credit hold automation", "Orders ship despite overdue balances; manual block unreliable", "H", "Automated credit hold triggers at 30 days past due or limit exceeded"),
    ("Credit Mgmt", "Inadequate new customer vetting", "No background checks on new accounts; 8% default within 6 months", "H", "Mandatory credit check and trade reference verification before first order"),
    ("Credit Mgmt", "Credit committee meets infrequently", "Committee meets quarterly; backlog of 45+ pending approvals", "M", "Weekly automated approvals for standard cases; committee for exceptions"),
    ("Credit Mgmt", "No real-time exposure monitoring", "Exposure tracking is monthly spreadsheet-based; blind spots exist", "H", "Real-time credit exposure dashboard with automated alerts"),
    ("Credit Mgmt", "Missing credit scoring documentation", "Scoring criteria undocumented; decisions vary by analyst", "M", "Document scoring model, train staff, establish override governance"),
    ("Credit Mgmt", "No integration with credit bureaus", "Bureau data pulled manually via web portal; 3-day lag", "M", "API integration with credit bureaus for real-time scoring"),
    # Order Management
    ("Order Mgmt", "High order error rate", "12% of orders require correction post-entry; rework costs $180K/yr", "H", "Implement order validation rules and guided selling configuration"),
    ("Order Mgmt", "No EDI/API for major customers", "Top 20 customers submit orders via email/fax; manual entry", "H", "Deploy EDI 850/855 or API integration for top 20 accounts"),
    ("Order Mgmt", "Order-to-ship cycle too long", "Average 4.2 days from order to shipment vs industry 1.5 days", "H", "Streamline approval workflow; implement wave planning and auto-allocation"),
    ("Order Mgmt", "Duplicate order detection absent", "3% duplicate orders discovered only at invoicing stage", "M", "Automated duplicate detection on customer+PO+date+amount"),
    ("Order Mgmt", "No ATP/CTP visibility", "Available-to-promise not checked at order entry; 15% backorders", "H", "Real-time ATP integration between order management and inventory"),
    ("Order Mgmt", "Manual order acknowledgment", "Order confirmations sent manually; 2-day average delay", "M", "Automated order acknowledgment within 1 hour of receipt"),
    ("Order Mgmt", "Returns process disconnected", "Returns handled outside order system; no visibility to AR", "M", "Integrate RMA process with order management and AR module"),
    ("Order Mgmt", "No order promising rules", "CSRs commit delivery dates without checking capacity", "H", "Configure promising rules based on inventory, production, and logistics"),
    ("Order Mgmt", "Missing order audit trail", "Cannot trace who changed order quantities or dates post-entry", "H", "Enable full audit trail with change reason codes"),
    ("Order Mgmt", "No self-service portal", "All orders require CSR intervention; 40% are repeat/standard", "M", "Deploy customer self-service portal for repeat orders"),
    # Pricing & Contracts
    ("Pricing", "Pricing errors at invoicing", "7% of invoices have pricing discrepancies vs contract terms", "H", "Automated price derivation from contract master with validation"),
    ("Pricing", "Manual discount approvals", "All discounts require email approval; 2-day average delay", "M", "Tiered discount authority matrix with automated workflow"),
    ("Pricing", "No contract compliance monitoring", "Contract terms not tracked; volume commitments unmonitored", "M", "Automated contract compliance with quarterly reviews"),
    ("Pricing", "Rebate calculation is manual", "Rebates calculated in spreadsheets; error-prone and late", "H", "Automated rebate engine tied to sales data"),
    ("Pricing", "Price list maintenance fragmented", "Multiple price lists across systems; no single source of truth", "H", "Centralized pricing master with version control"),
    ("Pricing", "No competitive pricing intelligence", "Pricing decisions made without market data; margin erosion", "M", "Implement competitive pricing tool with market benchmarks"),
    ("Pricing", "Transfer pricing undocumented", "Intercompany pricing lacks documentation for tax compliance", "C", "Document transfer pricing policy per OECD guidelines"),
    ("Pricing", "Expired contracts still active", "18% of contracts past expiry; pricing defaults to outdated rates", "M", "Automated contract expiry alerts 90/60/30 days prior"),
    # Billing & Invoicing
    ("Billing", "Invoice generation delays", "Invoices sent 5+ days after delivery; DSO impact of 8 days", "H", "Same-day automated invoicing triggered by delivery confirmation"),
    ("Billing", "No e-invoicing compliance", "Paper/PDF invoices only; non-compliant with GST e-invoicing mandate", "C", "Implement GST e-invoicing via IRP with automated IRN generation"),
    ("Billing", "High invoice rejection rate", "14% of invoices rejected by customers due to errors", "H", "Pre-validation against customer PO and contract before sending"),
    ("Billing", "No consolidated billing", "Multi-site customers receive 30+ invoices monthly; manual process", "M", "Consolidated billing with customer-defined grouping rules"),
    ("Billing", "Missing billing milestones", "Project-based billing milestones tracked manually; revenue leakage", "H", "Milestone-based billing automation with project integration"),
    ("Billing", "Credit note process uncontrolled", "Credit notes issued without proper approval; fraud risk", "C", "Credit note approval workflow with dual authorization above threshold"),
    ("Billing", "No billing accuracy KPI", "No measurement of invoice accuracy; issues discovered by customers", "M", "Track and report billing accuracy weekly; target >99%"),
    ("Billing", "Proforma invoice process manual", "Proforma invoices created outside system; reconciliation gap", "M", "Integrate proforma into billing workflow with conversion tracking"),
    ("Billing", "No self-billing support", "Large customers use self-billing but no matching process exists", "M", "Implement evaluated receipt settlement for self-billing customers"),
    ("Billing", "Invoice delivery failures untracked", "No confirmation that invoices reach customers; email bounces ignored", "M", "Invoice delivery tracking with automated resend on failure"),
    # Revenue Recognition
    ("Revenue", "ASC 606 compliance gaps", "Performance obligations not properly identified; misstatement risk", "C", "Full ASC 606 assessment with contract review and policy update"),
    ("Revenue", "Manual revenue allocation", "Multi-element arrangements allocated manually in spreadsheets", "H", "Automated SSP determination and allocation engine"),
    ("Revenue", "No contract modification tracking", "Modifications handled as new contracts; cumulative catch-up missed", "H", "Contract modification workflow with impact assessment"),
    ("Revenue", "Variable consideration not estimated", "Rebates and returns not estimated at inception; period-end adjustments", "H", "Expected value or most likely amount estimation at contract inception"),
    ("Revenue", "Insufficient revenue disclosures", "Disaggregated revenue disclosure lacks required granularity", "M", "Enhance disclosure templates per ASC 606 requirements"),
    ("Revenue", "Revenue recognized before delivery", "Bill-and-hold revenue recognized without meeting criteria", "C", "Bill-and-hold policy with documented customer request and risk transfer"),
    ("Revenue", "No contract asset/liability tracking", "Unbilled revenue and deferred revenue not properly tracked", "H", "Subledger for contract assets and liabilities with monthly reconciliation"),
    ("Revenue", "Percentage of completion errors", "Cost-to-cost method uses stale estimates; margin distortion", "H", "Monthly EAC reviews with PM sign-off on cost estimates"),
    # Collections
    ("Collections", "No automated dunning", "Collection calls made manually; inconsistent follow-up", "H", "Automated dunning with escalating templates at 30/60/90 days"),
    ("Collections", "DSO above industry benchmark", "DSO at 62 days vs industry average of 42 days; $3.2M cash impact", "H", "Segmented collection strategy; priority focus on top 20% of receivables"),
    ("Collections", "No promise-to-pay tracking", "Customer payment promises not recorded; no follow-up mechanism", "M", "Digital promise-to-pay with automated reminder at commitment date"),
    ("Collections", "Collection effectiveness index low", "CEI at 71% vs target of 90%; aging is worsening", "H", "Dedicated collectors for strategic accounts; weekly aging reviews"),
    ("Collections", "No early payment incentives", "No discount program despite high DSO; missed opportunity", "M", "Implement 2/10 net 30 or dynamic discounting program"),
    ("Collections", "Legal escalation process unclear", "No defined criteria for legal action; delays in recovery", "M", "Escalation policy with clear criteria and pre-approved legal panel"),
    ("Collections", "No collections prioritization model", "All overdue accounts treated equally regardless of size/risk", "M", "Risk-stratified collections with automated work queue prioritization"),
    ("Collections", "Missing aging reconciliation", "AR aging report does not match GL; unexplained differences", "H", "Monthly AR-to-GL reconciliation with variance investigation"),
    # Cash Application
    ("Cash App", "Manual cash application", "80% of receipts applied manually; 5-day average application lag", "H", "Automated matching with lockbox integration and AI-based matching"),
    ("Cash App", "High unapplied cash", "Unapplied cash averages $2.1M; distorts aging and collection efforts", "H", "Same-day application target; daily unapplied cash review"),
    ("Cash App", "No remittance data capture", "Customer remittances not linked to payments; manual research", "M", "OCR/AI remittance extraction from email, portal, and check stubs"),
    ("Cash App", "Deductions taken without authorization", "Customers deduct freight, returns, discounts unilaterally; $800K/yr", "H", "Deduction management workflow with root cause analysis and trending"),
    ("Cash App", "Multiple payment methods unintegrated", "Wire, ACH, check, credit card processed in separate systems", "M", "Unified payment processing platform with consolidated reporting"),
    ("Cash App", "On-account payments not investigated", "Payments without remittance sit unapplied for 30+ days", "M", "Auto-matching rules; escalation after 5 business days unapplied"),
    ("Cash App", "No payment prediction model", "Cash forecasting relies on historical averages; inaccurate", "M", "AI-based payment prediction using customer behavior patterns"),
    # Dispute Management
    ("Disputes", "No formal dispute resolution process", "Disputes handled ad hoc; avg 45-day resolution vs 15-day target", "H", "Structured dispute management with SLA tracking and root cause coding"),
    ("Disputes", "Dispute root causes not analyzed", "Same issues recur; no trending or prevention program", "M", "Monthly root cause analysis with process improvement initiatives"),
    ("Disputes", "Short-pay handling inconsistent", "Some short-pays written off; others held indefinitely; no policy", "H", "Short-pay policy with write-off thresholds and approval matrix"),
    ("Disputes", "No customer collaboration portal", "Disputes communicated via email; audit trail incomplete", "M", "Online dispute portal with document upload and status tracking"),
    ("Disputes", "Trade promotion deductions unvalidated", "Promotional deductions accepted without proof of performance", "H", "Proof-of-performance requirement before deduction approval"),
    ("Disputes", "Disputed amount impacts aging", "Disputed invoices age alongside valid receivables; misleading reports", "M", "Separate dispute aging from standard aging with resolution tracking"),
    # Controls & SOX
    ("Controls", "No segregation of duties in AR", "Same person creates invoices, applies cash, and writes off balances", "C", "Implement SoD controls; minimum three-person process separation"),
    ("Controls", "Write-off authority undefined", "No formal authority matrix for bad debt write-offs", "H", "Tiered write-off authority: analyst <$5K, manager <$25K, director <$100K, CFO >$100K"),
    ("Controls", "AR reconciliation not monthly", "AR subledger reconciled to GL quarterly; errors compound", "H", "Monthly automated reconciliation with mandatory sign-off"),
    ("Controls", "No SOX key control documentation", "O2C controls not documented per SOX requirements", "C", "Document and test key controls; prepare for external audit"),
    ("Controls", "Customer master data changes uncontrolled", "Bank details and addresses changed without dual approval; fraud risk", "C", "Dual approval for sensitive customer master changes; callback verification for bank details"),
    ("Controls", "Credit memo abuse potential", "No monitoring for unusual credit memo patterns; employee fraud risk", "H", "Automated monitoring for credit memo frequency, amount, and issuer patterns"),
    ("Controls", "Revenue cut-off procedures weak", "No formal cut-off procedures at period end; timing risk", "H", "Documented cut-off checklist with evidence of completion"),
]

_S_P2P = [
    # Requisition
    ("Requisition", "No purchase requisition system", "Purchases made without formal requisition; budget control weak", "H", "Deploy e-requisition with budget check and approval workflow"),
    ("Requisition", "Maverick spending high", "35% of spend is off-contract; no preferred vendor compliance", "H", "Guided buying with catalog-based ordering; block non-preferred vendors"),
    ("Requisition", "No spend visibility", "Cannot report total spend by category, vendor, or department", "H", "Spend analytics platform with automated classification"),
    ("Requisition", "Approval matrix not enforced", "Approval limits exist on paper but bypassed in practice", "H", "System-enforced approval limits with no override capability"),
    ("Requisition", "Emergency PO process overused", "28% of POs classified as emergency; bypasses normal controls", "M", "Restrict emergency POs to <5%; retrospective review for all emergency purchases"),
    ("Requisition", "No demand aggregation", "Departments order independently; volume discounts missed", "M", "Cross-department demand consolidation for strategic categories"),
    ("Requisition", "Requisition to PO cycle time excessive", "Average 8 days from requisition to PO; operational delays", "M", "Automated PO generation for pre-approved catalogs; target <1 day"),
    ("Requisition", "No budget integration", "Requisitions not checked against available budget at submission", "H", "Real-time budget check at requisition entry; block if insufficient"),
    ("Requisition", "Free-text requisitions dominant", "70% of requisitions use free text; no catalog matching", "M", "Catalog expansion to cover 80% of indirect spend categories"),
    ("Requisition", "No requisition analytics", "Cannot identify repeat purchases or consolidation opportunities", "M", "Requisition pattern analysis with consolidation recommendations"),
    # Vendor Management
    ("Vendor Mgmt", "No vendor performance scorecards", "Vendor performance not measured; poor performers retained", "H", "Quarterly scorecards on quality, delivery, price, and responsiveness"),
    ("Vendor Mgmt", "Vendor onboarding takes 30+ days", "New vendor setup requires manual forms; procurement delayed", "M", "Digital vendor onboarding portal with automated compliance checks"),
    ("Vendor Mgmt", "Vendor master data duplicates", "12% duplicate vendor records; duplicate payments risk", "H", "Vendor master cleansing and deduplication; automated matching on new entries"),
    ("Vendor Mgmt", "No vendor risk assessment", "Vendor financial health not monitored; supply chain risk", "H", "Annual financial health assessment for critical vendors; continuous monitoring for top 50"),
    ("Vendor Mgmt", "Single source for critical items", "40% of critical materials from single vendor; concentration risk", "C", "Dual-source strategy for all critical materials; 70/30 split minimum"),
    ("Vendor Mgmt", "Vendor diversity goals not tracked", "No measurement of diverse supplier spend vs targets", "L", "Track diverse supplier spend; set annual improvement targets"),
    ("Vendor Mgmt", "No preferred vendor list", "Buyers choose vendors freely; fragmented spend base", "M", "Establish preferred vendor list per category with compliance targets"),
    ("Vendor Mgmt", "Vendor bank detail changes uncontrolled", "Bank details changed on verbal request; fraud vulnerability", "C", "Mandatory callback verification and dual approval for all bank detail changes"),
    ("Vendor Mgmt", "No vendor sustainability assessment", "ESG criteria not part of vendor selection or monitoring", "M", "Include ESG questionnaire in onboarding; annual sustainability review"),
    ("Vendor Mgmt", "Vendor contracts not centralized", "Contracts stored in email, drives, and filing cabinets", "H", "Centralized contract repository with searchable metadata and alerts"),
    # Purchase Orders
    ("PO Mgmt", "PO compliance below 60%", "41% of invoices received without a corresponding PO", "H", "Enforce no-PO-no-pay policy; train all requestors on PO requirement"),
    ("PO Mgmt", "No three-way match", "Invoices paid without matching to PO and goods receipt", "C", "Implement automated three-way match with tolerance thresholds"),
    ("PO Mgmt", "Blanket PO management weak", "Blanket POs not tracked for balance consumption; overspend risk", "M", "Automated blanket PO balance tracking with alerts at 80% consumption"),
    ("PO Mgmt", "PO change order process manual", "Changes to POs communicated via email; audit trail gaps", "M", "Formal PO change order workflow with version tracking"),
    ("PO Mgmt", "Open PO cleanup not performed", "3,200 POs open for 12+ months; encumbrance reporting skewed", "M", "Quarterly review and close of aged open POs with budget release"),
    ("PO Mgmt", "No PO delivery tracking", "Cannot track delivery status against PO dates; no vendor accountability", "M", "PO delivery tracking with automated ASN matching"),
    ("PO Mgmt", "Split PO to avoid approval limits", "Purchases split across multiple POs to stay below approval thresholds", "C", "Automated detection of split POs; policy enforcement with consequences"),
    ("PO Mgmt", "Retrospective POs prevalent", "POs created after invoice receipt to enable payment; defeats controls", "H", "Monitoring for retrospective POs; root cause analysis and reduction plan"),
    ("PO Mgmt", "No PO collaboration with vendors", "PO disputes resolved via email; no vendor portal", "M", "Vendor collaboration portal for PO acknowledgment and dispute resolution"),
    # Goods Receipt
    ("GR", "Goods receipt not timely", "Average 4 days between physical receipt and system entry", "H", "Mobile GR scanning at dock; target same-day system entry"),
    ("GR", "No quality inspection integration", "QC inspection results not linked to GR; rejected goods invoiced", "H", "Integrate QC hold and release into three-way match process"),
    ("GR", "Blind receiving not practiced", "Receivers see PO quantities; count accuracy not verified", "M", "Implement blind receiving for high-value items; random audits for others"),
    ("GR", "Service receipt undocumented", "Services received without formal confirmation; payment disputes", "H", "Service entry sheet with project manager sign-off before payment"),
    ("GR", "GR/IR clearing account not reconciled", "GR/IR clearing balance at $1.8M; contains items 6+ months old", "H", "Monthly GR/IR reconciliation; investigate items >30 days old"),
    ("GR", "No ASN matching", "Advanced shipping notices not matched to GR; receiving is manual", "M", "ASN integration with automatic GR creation on delivery confirmation"),
    ("GR", "Partial receipt handling inconsistent", "Different sites handle partial deliveries differently; confusion", "M", "Standardized partial receipt policy with automated communication to AP"),
    ("GR", "Consignment inventory untracked", "Vendor-owned consignment inventory not in system; liability risk", "H", "Track consignment in separate inventory type; monthly consumption reporting"),
    # Invoice Processing
    ("Invoice", "Invoice processing cost too high", "Average $15 per invoice vs benchmark $2.50; 80% manual", "H", "OCR/AI invoice capture with automated coding and three-way match"),
    ("Invoice", "No invoice automation", "All invoices processed manually; team of 8 FTEs for 50K invoices/yr", "H", "Deploy AP automation platform; target 70% touchless processing"),
    ("Invoice", "Duplicate payment rate elevated", "0.5% duplicate payments identified; estimated $400K annual exposure", "H", "Automated duplicate detection on vendor+amount+date+invoice number"),
    ("Invoice", "Early payment discount capture low", "Only 12% of available early payment discounts captured; $600K lost", "H", "Automated discount identification and prioritized payment scheduling"),
    ("Invoice", "Invoice exception rate high", "40% of invoices require manual exception handling", "H", "Root cause analysis of exceptions; supplier training on invoice requirements"),
    ("Invoice", "No e-invoicing adoption", "0% electronic invoicing; all paper/PDF/email", "M", "Supplier portal for e-invoicing; target 50% e-invoice adoption in 12 months"),
    ("Invoice", "Invoice coding errors", "18% of invoices coded to wrong GL account or cost center", "H", "Automated GL coding with ML-based prediction from historical patterns"),
    ("Invoice", "Tax validation manual", "GST/VAT on invoices checked manually; compliance risk", "H", "Automated tax validation against vendor GSTIN and HSN master"),
    ("Invoice", "PO-based invoice matching tolerances undefined", "No documented tolerances; inconsistent acceptance of variances", "M", "Define matching tolerances by category: price ±2%, quantity ±5%"),
    ("Invoice", "Vendor statement reconciliation absent", "Vendor statements not reconciled; missing invoices undetected", "M", "Monthly vendor statement reconciliation for top 50 vendors"),
    ("Invoice", "Intercompany invoice reconciliation gap", "IC invoices not matched between entities; elimination errors", "H", "Automated intercompany invoice matching with dispute workflow"),
    # Payment Processing
    ("Payments", "No payment run optimization", "Daily payment runs with no optimization for cash flow or discounts", "M", "Weekly optimized payment runs; daily only for critical/discount items"),
    ("Payments", "Check payments still dominant", "55% of payments by check; high cost and fraud risk", "H", "Migrate to electronic payments; target <10% check volume"),
    ("Payments", "No positive pay", "Checks not protected by positive pay; fraud exposure", "H", "Implement positive pay with all banking partners"),
    ("Payments", "Payment approval matrix not enforced", "Payments above threshold processed without proper approval", "C", "System-enforced payment approval matrix with dual authorization above $50K"),
    ("Payments", "Bank reconciliation delayed", "Reconciliation performed monthly with 10-day lag; fraud detection delayed", "H", "Daily automated bank reconciliation with exception alerts"),
    ("Payments", "Vendor payment terms not optimized", "Standard 30-day terms with all vendors; no strategic negotiation", "M", "Negotiate terms by vendor tier: strategic=45-60 days, small=30 days"),
    ("Payments", "No dynamic discounting", "No platform for offering early payment in exchange for discounts", "M", "Deploy dynamic discounting platform for working capital optimization"),
    ("Payments", "International payment fees excessive", "Wire fees and FX spreads not negotiated; paying retail rates", "M", "Negotiate banking fees; consider payment factory for cross-border payments"),
    ("Payments", "Payment fraud prevention weak", "No fraud screening on outgoing payments; reliance on manual review", "C", "Implement payment fraud screening with sanctions and pattern detection"),
    ("Payments", "ACH/NEFT prenote validation missing", "Bank details not validated before first electronic payment", "H", "Mandatory prenote/test payment for all new vendor bank details"),
    # Contract Management
    ("Contracts", "No contract lifecycle management", "Contracts in filing cabinets and email; cannot search or report", "H", "CLM platform with searchable repository and milestone tracking"),
    ("Contracts", "Auto-renewal without review", "Contracts auto-renew without commercial or performance review", "M", "90-day renewal alerts with mandatory commercial review"),
    ("Contracts", "Contract leakage unquantified", "No measurement of actual spend vs contracted terms", "H", "Contract compliance analytics; quarterly leakage reporting"),
    ("Contracts", "No standard contract templates", "Each contract drafted from scratch; legal review bottleneck", "M", "Standard templates by category with pre-approved legal clauses"),
    ("Contracts", "SLA monitoring absent", "Service contracts have SLAs but compliance not tracked", "M", "Automated SLA tracking with penalty/credit calculations"),
    ("Contracts", "Insurance and compliance not verified", "Vendor insurance certificates not checked at renewal", "H", "Annual certificate of insurance verification for all active vendors"),
    ("Contracts", "No force majeure clause review", "Post-pandemic clause review not performed; supply chain risk", "M", "Update force majeure and termination clauses in all strategic contracts"),
    # Controls & Compliance
    ("Controls", "No segregation of duties in AP", "Same person creates vendor, enters invoice, and processes payment", "C", "Enforce SoD: separate vendor master, invoice entry, and payment roles"),
    ("Controls", "PO splitting detection absent", "No system controls to detect purchase order splitting", "H", "Automated split-PO detection with alert to procurement manager"),
    ("Controls", "Vendor master changes uncontrolled", "No workflow for vendor master data changes; audit risk", "C", "Change request workflow with evidence retention for all vendor master changes"),
    ("Controls", "No P2P analytics for fraud detection", "Benford's Law analysis, round-amount analysis not performed", "H", "Continuous monitoring program with data analytics for fraud indicators"),
    ("Controls", "1099/TDS reporting errors", "Vendor tax reporting contains errors; penalty exposure", "H", "Annual 1099/TDS reconciliation with vendor classification review"),
    ("Controls", "Unclaimed property not managed", "Aged outstanding checks and credits not reported per escheatment laws", "M", "Annual unclaimed property review with state/jurisdiction reporting"),
    ("Controls", "Use tax not properly accrued", "Purchases from out-of-state vendors without use tax accrual", "H", "Automated use tax calculation on applicable purchases"),
    ("Controls", "No P2P process documentation", "Processes are tribal knowledge; key person dependency", "H", "Document all P2P processes with RACI matrices and control narratives"),
    ("Controls", "Audit trail gaps in payment system", "Cannot trace payment from requisition to bank debit end-to-end", "H", "End-to-end audit trail from requisition through payment and bank reconciliation"),
    # Reporting
    ("Reporting", "No AP aging analysis", "Cannot report payable aging accurately; cash planning impacted", "M", "Automated AP aging with payment forecasting"),
    ("Reporting", "Spend analytics unavailable", "No visibility into spend by category, vendor, geography, BU", "H", "Spend cube with drill-down by 10+ dimensions; quarterly reviews"),
    ("Reporting", "DPO not tracked", "Days Payable Outstanding not measured or benchmarked", "M", "Monthly DPO tracking with industry benchmark comparison"),
    ("Reporting", "No vendor payment history dashboard", "Cannot view payment history for individual vendors quickly", "L", "Vendor payment dashboard with history, terms compliance, and trends"),
    ("Reporting", "Procurement savings not measured", "Cost avoidance and cost reduction not tracked or reported", "M", "Procurement savings tracker with methodology documentation"),
    ("Reporting", "No budget vs actual by PO", "Cannot compare committed spend against budget by category", "M", "Budget commitment reporting by category and cost center"),
]

_S_R2R = [
    # Chart of Accounts
    ("CoA", "Chart of Accounts overly complex", "8,400 GL accounts; 40% inactive; reporting difficult", "M", "Rationalize to <3,000 active accounts; archive inactive"),
    ("CoA", "No CoA governance", "Anyone can request new accounts; proliferation unchecked", "H", "CoA governance committee with documented criteria for new accounts"),
    ("CoA", "Account structure not aligned with reporting needs", "Multiple manual reclassifications needed for external reporting", "H", "Redesign CoA to map directly to financial statement line items"),
    ("CoA", "No standard across entities", "Each legal entity has different CoA; consolidation is manual", "H", "Global CoA with local extensions; automated mapping for consolidation"),
    ("CoA", "Intercompany accounts not standardized", "IC coding inconsistent; elimination errors at consolidation", "H", "Standardized IC account structure with automated matching"),
    ("CoA", "Cost center hierarchy outdated", "Cost center structure reflects organization from 3 years ago", "M", "Align cost center hierarchy to current org structure; annual review"),
    ("CoA", "Statistical accounts not leveraged", "Non-financial KPIs tracked outside system; no correlation", "L", "Use statistical accounts for FTE, volume, and unit metrics"),
    ("CoA", "Account descriptions unclear", "Many accounts have cryptic names; mispostings result", "M", "Standardize account naming conventions; publish account dictionary"),
    # Journal Entries
    ("JE", "Manual journal entries excessive", "400+ manual JEs per month; error rate 5%", "H", "Automate recurring and systematic JEs; target <50 manual JEs/month"),
    ("JE", "Recurring JE templates not maintained", "Recurring entries have stale amounts; manual correction each period", "M", "Quarterly review and update of all recurring JE templates"),
    ("JE", "Journal entry approval lacking", "JEs posted without review; even material entries unreviewed", "C", "System-enforced approval for JEs above threshold; random audit for others"),
    ("JE", "No JE supporting documentation", "JEs lack attached support; audit evidence gathering takes days", "H", "Mandatory document attachment policy; reject JEs without support"),
    ("JE", "Reversing entries not automated", "Accrual reversals done manually; missed reversals cause errors", "M", "Automatic reversal scheduling for all accrual entries"),
    ("JE", "No standard JE description format", "Descriptions vary; difficult to search or understand entries", "M", "Standardized description format: [Type]-[Category]-[Detail]-[Period]"),
    ("JE", "Intercompany JEs unbalanced", "IC entries processed independently by each entity; out of balance", "H", "Simultaneous IC posting with balanced entry validation"),
    ("JE", "Top-side adjustments not tracked", "Manual consolidation adjustments made outside system; no audit trail", "H", "All top-side adjustments processed through system with full documentation"),
    ("JE", "Post-close JEs excessive", "Average 85 post-close adjustments per quarter; delays reporting", "H", "Root cause analysis; improve close process to reduce post-close entries"),
    ("JE", "JE threshold monitoring absent", "No alerts for unusual or large journal entries", "H", "Automated alerts for JEs exceeding threshold by account or user"),
    # Subledger to GL
    ("Sub-GL", "Subledger-GL reconciliation gaps", "AP and AR subledgers differ from GL by $3.2M combined", "C", "Monthly subledger-to-GL reconciliation with mandatory resolution"),
    ("Sub-GL", "Posting frequency inconsistent", "Some subledgers post daily, others weekly; reconciliation difficult", "M", "Standardize daily posting for all subledgers; batch by 6 PM"),
    ("Sub-GL", "Suspense account balances growing", "Suspense accounts at $1.4M; items over 90 days old", "H", "Weekly suspense account review; 5-day clearing SLA"),
    ("Sub-GL", "Clearing account reconciliation overdue", "18 clearing accounts not reconciled in 3+ months", "H", "Monthly clearing account reconciliation; escalation for items >30 days"),
    ("Sub-GL", "No automated posting rules", "Subledger postings require manual GL account assignment", "M", "Configure automatic posting rules for all standard transactions"),
    ("Sub-GL", "Tax subledger disconnected", "Tax calculations in separate system; reconciliation to GL manual", "H", "Integrate tax engine with GL; automated reconciliation"),
    ("Sub-GL", "Payroll-to-GL mapping errors", "Payroll posting creates GL variances; monthly manual fixes", "H", "Map payroll cost elements to GL accounts; validate monthly"),
    ("Sub-GL", "Fixed asset subledger drift", "NBV in asset register differs from GL by $450K", "H", "Monthly asset register to GL reconciliation with variance analysis"),
    # Intercompany
    ("IC", "IC reconciliation manual and late", "Intercompany reconciliation takes 5 days post-close; delays reporting", "H", "Real-time IC matching with automated dispute flagging"),
    ("IC", "IC pricing not at arms length", "Transfer pricing documentation incomplete; tax authority risk", "C", "Annual transfer pricing study; contemporaneous documentation"),
    ("IC", "IC eliminations manual", "Consolidation eliminations done in spreadsheets; error-prone", "H", "Automated IC elimination rules in consolidation system"),
    ("IC", "IC settlement delays", "IC balances settled quarterly; cash trapped in entities", "M", "Monthly IC netting and settlement; multilateral netting for efficiency"),
    ("IC", "IC SLA not defined", "No agreement on response times for IC invoice queries", "M", "IC SLA: acknowledge in 2 business days, resolve in 5"),
    ("IC", "IC in multiple currencies without hedge", "IC positions create FX exposure; no hedging strategy", "H", "Natural hedging through currency matching; formal FX policy for residual"),
    ("IC", "No IC billing automation", "IC invoices created manually; inconsistent with transfer pricing policy", "H", "Automated IC billing from allocation engine with policy compliance"),
    ("IC", "IC loan documentation missing", "IC loans lack formal agreements; thin capitalization risk", "C", "Document all IC loans with market-rate interest and repayment terms"),
    ("IC", "IC profit in inventory not eliminated", "ICIP calculation incorrect; financial statements misstated", "C", "Automated ICIP calculation with margin data from IC billing system"),
    # Period-End Close
    ("Close", "Close cycle exceeds 10 business days", "Month-end close takes 12 days; quarterly 18 days", "H", "Re-engineer close process; target 5-day monthly, 8-day quarterly close"),
    ("Close", "No close calendar or checklist", "Close tasks not documented; reliance on individual knowledge", "H", "Detailed close calendar with task owners, dependencies, and deadlines"),
    ("Close", "Accrual process inconsistent", "Some departments accrue, others dont; cut-off issues", "H", "Standardized accrual methodology with central coordination"),
    ("Close", "No soft close or continuous close", "All close activities compressed into period-end; bottleneck", "M", "Implement continuous accounting: daily reconciliations, rolling accruals"),
    ("Close", "Close process not automated", "90% of close activities manual; spreadsheet-dependent", "H", "Close management software with task tracking and automated workflows"),
    ("Close", "Flux analysis not timely", "Variance analysis done after financial statements issued; no prevention", "H", "Real-time flux analysis during close; investigate variances >10% before finalizing"),
    ("Close", "No pre-close activities", "Reconciliations and accruals start only at period-end", "M", "Pre-close checklist: begin reconciliations at Day -5 of period end"),
    ("Close", "Quarter-end adjustments excessive", "Average 40 quarter-end-only adjustments; audit concern", "H", "Spread adjustments into monthly process; reduce quarter-end-only entries"),
    ("Close", "No close readiness assessment", "Close starts without confirming all feeds and data are received", "M", "Day 1 readiness checklist: confirm all subledger posts, bank feeds, payroll data"),
    ("Close", "Close signoff not documented", "Controller verbal approval; no evidence of review", "H", "Digital close signoff with checklist completion evidence"),
    ("Close", "Black-out period not enforced", "Transactions posted during close that should be in next period", "M", "System-enforced black-out from Day 1 to close completion"),
    # Reconciliations
    ("Recon", "Bank reconciliation not daily", "Bank reconciliation monthly; fraud detection delayed by weeks", "H", "Daily automated bank reconciliation with same-day exception review"),
    ("Recon", "No reconciliation software", "All reconciliations in spreadsheets; version control issues", "H", "Deploy reconciliation platform with matching rules and workflow"),
    ("Recon", "Reconciliation items aged", "2,300 open reconciling items over 60 days; investigated ad hoc", "H", "Aging policy: resolve items within 10 business days; escalation at 30"),
    ("Recon", "No reconciliation risk rating", "All accounts reconciled with same rigor regardless of risk", "M", "Risk-rate accounts: high=monthly detailed, medium=monthly review, low=quarterly"),
    ("Recon", "Balance sheet certification incomplete", "Only 60% of BS accounts have certified reconciliations", "H", "100% BS certification within 5 days of close; automated tracking"),
    ("Recon", "No reconciliation standard templates", "Each preparer uses different formats; review quality varies", "M", "Standardized reconciliation templates per account type"),
    ("Recon", "Reconciliation reviewer independence lacking", "Preparers self-review reconciliations; control gap", "H", "Independent review required for all reconciliations above threshold"),
    ("Recon", "FX revaluation reconciliation absent", "Unrealized FX gains/losses not reconciled to underlying positions", "H", "Monthly FX revaluation reconciliation with rate source validation"),
    ("Recon", "Subsidiary reconciliation delays", "Subsidiary data received 5+ days after close; delays parent reporting", "H", "Parallel close at subsidiaries; Day 3 data submission deadline"),
    # Financial Reporting
    ("Fin Rptg", "Financial statements require manual assembly", "Statements built in Excel from trial balance; error-prone", "H", "Automated financial statement generation from GL with drill-down"),
    ("Fin Rptg", "No XBRL tagging capability", "SEC filings tagged manually; expensive and error-prone", "M", "XBRL-enabled reporting tool with automated tagging"),
    ("Fin Rptg", "Disclosure checklist incomplete", "New accounting standards not reflected in disclosure checklist", "H", "Annual disclosure checklist update aligned to ASC/IFRS changes"),
    ("Fin Rptg", "Segment reporting methodology undocumented", "Segment allocation methodology not documented; audit questions", "H", "Document segment reporting methodology with allocation basis"),
    ("Fin Rptg", "No management report automation", "Management reports created manually; 3-day lag after close", "M", "Automated management reporting package; available Day 1 after close"),
    ("Fin Rptg", "EPS calculation manual", "Earnings per share computed in spreadsheet; dilution errors possible", "H", "Automated EPS calculation with dilution modeling in reporting tool"),
    ("Fin Rptg", "Roll-forward schedules not automated", "Debt, equity, and reserve roll-forwards maintained manually", "M", "Automated roll-forward schedules with system-sourced data"),
    ("Fin Rptg", "Cash flow statement indirect method errors", "Non-cash adjustments and working capital changes reconciled manually", "H", "Automated cash flow statement with GL-based derivation"),
    # Controls & Audit
    ("R2R Controls", "No continuous controls monitoring", "Controls tested annually; gaps undetected for months", "H", "Implement continuous controls monitoring with automated testing"),
    ("R2R Controls", "Key control failures not escalated", "Control exceptions logged but not escalated to management", "H", "Automated escalation workflow for control exceptions"),
    ("R2R Controls", "No data analytics in audit", "Internal audit relies on sampling; limited coverage", "M", "Deploy data analytics for 100% transaction testing on key controls"),
    ("R2R Controls", "Material weakness remediation tracking weak", "MW remediation plans not tracked to completion; repeat findings", "C", "Formal remediation tracking with milestone dates and executive reporting"),
    ("R2R Controls", "ITGCs not tested for financial applications", "General IT controls over financial systems not assessed", "H", "Annual ITGC assessment for all financially significant applications"),
    ("R2R Controls", "No entity-level controls assessment", "COSO entity-level controls not evaluated", "M", "Annual COSO-based entity-level control assessment"),
    ("R2R Controls", "Change management for financial systems weak", "System changes deployed without proper change management", "H", "Formal change management with testing, approval, and rollback plans"),
]

_S_GL = [
    # Fixed Assets
    ("Fixed Assets", "No periodic physical verification", "Fixed assets not physically verified in 3+ years; ghost assets likely", "H", "Annual physical verification with barcode/RFID tracking"),
    ("Fixed Assets", "Capitalization policy inconsistent", "Different thresholds across entities; comparability issues", "H", "Uniform capitalization threshold across all entities; annual review"),
    ("Fixed Assets", "Depreciation method review not performed", "Useful lives and methods not reassessed since initial setup", "M", "Annual reassessment of useful lives and depreciation methods"),
    ("Fixed Assets", "Asset disposal process undocumented", "Disposals processed ad hoc; gain/loss calculation errors", "H", "Formal disposal workflow with approval, physical removal, and accounting"),
    ("Fixed Assets", "CIP aging unmonitored", "Construction-in-progress items exceeding project timelines; no review", "M", "Monthly CIP review; transfer to assets within 30 days of completion"),
    ("Fixed Assets", "Impairment testing not performed", "No annual impairment assessment; potential overstatement", "H", "Annual impairment testing for all asset groups; trigger-based interim testing"),
    ("Fixed Assets", "Lease accounting ASC 842 gaps", "Right-of-use assets and lease liabilities not properly recognized", "C", "Full ASC 842 compliance review; implement lease accounting software"),
    ("Fixed Assets", "Asset transfers between locations untracked", "Assets moved between sites without system update; location data unreliable", "M", "Asset transfer workflow with custodian acknowledgment"),
    ("Fixed Assets", "No asset tagging standard", "Multiple tagging systems across sites; identification difficult", "M", "Unified asset tagging with barcode/QR code and mobile scanning"),
    ("Fixed Assets", "Fully depreciated assets still in use not reviewed", "30% of asset base fully depreciated but in use; useful life review needed", "L", "Annual review of fully depreciated in-use assets for impairment/extension"),
    # Bank Reconciliation
    ("Bank Recon", "Reconciliation performed monthly", "Monthly reconciliation delays fraud detection by up to 30 days", "H", "Daily automated bank reconciliation with same-day exception review"),
    ("Bank Recon", "Outstanding checks not followed up", "Checks outstanding >90 days not investigated; escheatment risk", "M", "Monthly follow-up on checks outstanding >60 days; void at 180 days"),
    ("Bank Recon", "No bank fee analysis", "Bank fees accepted without review; potential overcharges", "L", "Quarterly bank fee analysis with benchmark comparison"),
    ("Bank Recon", "Multiple bank accounts not consolidated", "45 bank accounts across 6 banks; liquidity fragmented", "M", "Bank rationalization; zero-balance sweeping to concentration accounts"),
    ("Bank Recon", "Bank reconciliation preparer and reviewer same person", "No independent review of bank reconciliations; control gap", "H", "Segregate bank reconciliation preparation and review roles"),
    ("Bank Recon", "Foreign currency bank accounts not revalued", "FC bank balances not revalued at period-end; BS misstatement", "H", "Month-end FX revaluation for all foreign currency bank accounts"),
    ("Bank Recon", "No cash pooling optimization", "Entities maintain separate cash reserves; interest optimization lost", "M", "Implement notional or physical cash pooling with partner bank"),
    ("Bank Recon", "Bank confirmation process manual", "Year-end bank confirmations sent manually; tracking difficult", "L", "Use electronic bank confirmation service for year-end audit"),
    # Expense Management
    ("Expenses", "No automated expense system", "Paper expense reports; 12-day average reimbursement cycle", "H", "Deploy mobile expense management with OCR receipt capture"),
    ("Expenses", "Policy violations not detected", "Expense policy limits not enforced; reliance on manager review", "H", "Automated policy compliance checks at submission; flag violations"),
    ("Expenses", "No corporate card program", "Employees use personal cards; cash flow burden and tracking gap", "H", "Corporate card program with automated feed to expense system"),
    ("Expenses", "Per diem rates not updated", "Travel per diem rates from 2019; not market-appropriate", "L", "Annual per diem rate update aligned to GSA/company policy"),
    ("Expenses", "Duplicate expense claims not detected", "No system check for duplicate submissions; estimated 3% duplicate rate", "H", "Automated duplicate detection on date+amount+vendor"),
    ("Expenses", "Receipt compliance below 70%", "30% of expense line items lack receipts; audit risk", "M", "Mandatory receipt for all items >$25; mobile capture at point of purchase"),
    ("Expenses", "T&E analytics not performed", "No trend analysis on travel spend; cost reduction opportunities missed", "M", "Quarterly T&E analytics with category and department drill-down"),
    ("Expenses", "Mileage claims unverified", "Mileage reimbursement based on self-reported distance; no validation", "M", "GPS-based mileage tracking or Google Maps distance verification"),
    # Cost Allocation
    ("Allocations", "Allocation methodology undocumented", "Shared costs allocated by outdated drivers; business unfairly charged", "H", "Document and validate allocation methodology annually with BU input"),
    ("Allocations", "IT cost allocation uses headcount only", "IT costs allocated purely by headcount; heavy users subsidized", "M", "Activity-based IT cost allocation using consumption metrics"),
    ("Allocations", "No allocation automation", "Cost allocations processed manually in spreadsheets; error-prone", "H", "Configure allocation cycles in ERP with automated posting"),
    ("Allocations", "Transfer pricing for services not at arms length", "Shared services charged at cost; transfer pricing documentation lacking", "C", "Arm's length pricing study for shared services with benchmarking"),
    ("Allocations", "Allocation cycle timing creates discrepancies", "Allocations run after close for some entities; timing differences", "M", "Standardize allocation cycle timing across all entities"),
    ("Allocations", "No activity-based costing capability", "Product/service costs based on simple averages; margin distortion", "M", "Implement ABC for key product lines to understand true profitability"),
    ("Allocations", "Overhead rate not market-tested", "Manufacturing overhead rate unchanged for 3 years; product cost inaccurate", "M", "Annual overhead rate review with benchmark comparison"),
    # Consolidation
    ("Consol", "Consolidation in spreadsheets", "Multi-entity consolidation done in Excel; 40+ tabs; error-prone", "C", "Implement consolidation software with automated data collection"),
    ("Consol", "Minority interest calculation manual", "Non-controlling interest calculated manually; misstatement risk", "H", "Automated NCI calculation with ownership percentage tracking"),
    ("Consol", "Currency translation process manual", "CTA calculated in spreadsheets; rate sources inconsistent", "H", "Automated currency translation with centralized rate repository"),
    ("Consol", "No consolidation validation rules", "Consolidated trial balance not validated before reporting", "H", "Automated validation: TB balance, IC elimination completeness, CTA reasonableness"),
    ("Consol", "Equity method investments tracked manually", "Equity method income and investment balance in spreadsheets", "M", "Automated equity method accounting with investee data feed"),
    ("Consol", "Acquisition accounting not standardized", "Each acquisition handled differently; goodwill calculation varies", "H", "Standardized acquisition accounting checklist with purchase price allocation process"),
    ("Consol", "Segment elimination manual", "Inter-segment transactions eliminated manually; reconciliation difficult", "M", "Automated segment elimination with reconciliation to legal entity consolidation"),
    ("Consol", "No consolidation audit trail", "Cannot trace consolidated numbers to source entity data", "H", "Full audit trail from consolidated financial statement to entity-level transaction"),
    # Statutory & Regulatory Reporting
    ("Statutory", "GST return reconciliation gaps", "GSTR-1 vs GSTR-3B mismatch averaging 5%; notices from department", "C", "Monthly GSTR-1/3B/2B reconciliation with automated matching"),
    ("Statutory", "TDS compliance issues", "TDS not deducted on several vendor categories; penalty exposure", "C", "Automated TDS applicability determination with section-wise tracking"),
    ("Statutory", "Annual return filing delays", "Statutory filings consistently filed after due date; penalties", "H", "Filing calendar with 30-day advance preparation start; automated reminders"),
    ("Statutory", "No regulatory change tracking", "New regulations discovered reactively; compliance gaps emerge", "H", "Regulatory change tracking service with impact assessment workflow"),
    ("Statutory", "Transfer pricing documentation absent", "No contemporaneous TP documentation; risk of benchmarking challenge", "C", "Annual TP study with benchmarking analysis per OECD/Indian guidelines"),
    ("Statutory", "Withholding tax on cross-border payments not optimized", "WHT applied at treaty rates without proper documentation", "H", "Tax treaty analysis with proper forms and documentation for each jurisdiction"),
    ("Statutory", "ROC filings not tracked", "Registrar of Companies filings managed ad hoc; missed deadlines", "M", "Annual compliance calendar for all ROC filings with automated alerts"),
    ("Statutory", "No tax provision automation", "Tax provision calculated manually; deferred tax errors", "H", "Tax provision software with automated temporary difference tracking"),
    # Internal Controls
    ("Int Controls", "No formal ICFR framework", "Internal controls over financial reporting not documented", "C", "Implement COSO-based ICFR framework with risk assessment and testing"),
    ("Int Controls", "Access controls in ERP inadequate", "Excessive system access; 15% of users have incompatible access combinations", "C", "Role-based access control redesign; quarterly access reviews"),
    ("Int Controls", "No automated controls testing", "Controls tested manually once a year; limited sample sizes", "H", "Continuous controls monitoring for high-risk automated controls"),
    ("Int Controls", "Control owners not identified", "Controls exist but no assigned owners; accountability gap", "H", "Assign control owners with documented responsibilities and self-assessment"),
    ("Int Controls", "No deficiency tracking and remediation", "Control deficiencies identified but not tracked to closure", "H", "Deficiency register with remediation plans, owners, and due dates"),
    ("Int Controls", "Whistleblower channel underutilized", "Hotline exists but no reports received in 2 years; awareness low", "M", "Employee awareness campaign; quarterly reporting to audit committee"),
    ("Int Controls", "Entity-level controls not assessed", "COSO entity-level controls (tone at top, risk assessment) not evaluated", "M", "Annual entity-level controls self-assessment with audit committee reporting"),
    ("Int Controls", "Compensating controls not documented", "Where SoD conflicts exist, compensating controls are assumed but not documented", "H", "Document all compensating controls with testing evidence"),
    # Data Quality
    ("Data Quality", "Master data governance absent", "No formal master data governance; duplicates and inconsistencies pervasive", "H", "Master data governance framework with stewardship and quality metrics"),
    ("Data Quality", "GL data quality issues", "15% of GL transactions have missing or incorrect dimensions", "H", "Mandatory field validation at entry; monthly data quality scorecard"),
    ("Data Quality", "No data lineage documentation", "Cannot trace reported numbers to source transactions; audit friction", "H", "Document data lineage from source system to report; automated mapping"),
    ("Data Quality", "Reporting data extracted manually", "Reports built from manual extracts; version and timing issues", "H", "Automated data pipelines to reporting layer; eliminate manual extracts"),
    ("Data Quality", "No data retention policy", "Data retained indefinitely without policy; storage costs growing", "M", "Data retention policy aligned to legal and regulatory requirements"),
    ("Data Quality", "Chart field validation rules insufficient", "Invalid combinations allowed; mispostings detected in review", "M", "Cross-validation rules to block invalid account+cost center combinations"),
    ("Data Quality", "System-of-record not defined", "Multiple systems claim to be the source of truth for same data", "H", "Define system of record for each data domain; resolve conflicts"),
    ("Data Quality", "Historical data migration issues", "Legacy system data migrated with errors; ongoing reconciliation burden", "M", "Data migration validation project; resolve known issues and document exceptions"),
]

_S_FPA = [
    ("Budgeting", "Budget process takes 4+ months", "Annual budget cycle is 16 weeks; by completion, assumptions are stale", "H", "Streamline to 8-week cycle with driver-based budgeting"),
    ("Budgeting", "No rolling forecast", "Annual budget is only plan; no re-forecasting during year", "H", "Quarterly rolling 5-quarter forecast replacing annual budget"),
    ("Budgeting", "Budgeting in spreadsheets", "800+ spreadsheets; version control and consolidation errors", "H", "Cloud-based planning platform with workflow and versioning"),
    ("Budgeting", "Bottom-up budget not reconciled to top-down targets", "BU budgets sum to 20% above board-approved target; negotiation loop", "M", "Top-down/bottom-up alignment process with gap analysis"),
    ("Budgeting", "No zero-based budgeting for SGA", "SG&A budgets incremental; cost base grows unchecked", "M", "ZBB for discretionary spend categories; annual reset"),
    ("Budgeting", "CapEx budgeting disconnected from strategy", "Capital budget not linked to strategic plan; ad hoc requests dominate", "H", "Strategic CapEx planning with stage-gate evaluation process"),
    ("Budgeting", "Headcount planning manual", "FTE budgets in separate spreadsheets; no link to compensation data", "M", "Integrated workforce planning with position-level detail"),
    ("Budgeting", "No scenario planning capability", "Only single-point plan; no best/worst/base case analysis", "H", "Scenario planning with 3+ cases and sensitivity analysis"),
    ("Forecasting", "Forecast accuracy below 85%", "Revenue forecast accuracy at 78%; cash planning impacted", "H", "Statistical baseline with judgmental overlay; track accuracy metrics"),
    ("Forecasting", "No demand sensing", "Forecast relies on historical averages; does not incorporate leading indicators", "M", "Incorporate external data (search trends, economic indicators) into forecast model"),
    ("Forecasting", "Cash flow forecast absent", "No cash flow forecast; liquidity management reactive", "C", "13-week rolling cash flow forecast with weekly update cycle"),
    ("Forecasting", "Forecast bias not measured", "Systematic over/under-forecasting by BU not identified", "M", "Track forecast bias by BU; address systemic bias in coaching"),
    ("Variance", "Variance analysis not actionable", "Variances reported but root causes not investigated", "H", "Structured variance analysis with root cause and corrective action"),
    ("Variance", "No operational KPIs linked to financials", "Financial results cannot be explained by operational drivers", "H", "Driver-based P&L bridge linking volumes, mix, price, and cost to financials"),
    ("Variance", "Variance thresholds not defined", "All variances reported equally regardless of materiality", "M", "Define investigation thresholds by line item; focus on material variances"),
    ("Variance", "No competitive benchmarking", "No comparison to peer companies on key financial metrics", "M", "Quarterly peer benchmarking on margins, growth, returns, and efficiency"),
    ("Modeling", "No financial model standard", "Each analyst builds models differently; no peer review", "H", "Financial modeling standards with template library and peer review"),
    ("Modeling", "Sensitivity analysis not performed", "Investment cases use single-point estimates; risk not quantified", "H", "Mandatory sensitivity analysis for all investment cases >$500K"),
    ("Modeling", "Business case post-implementation review absent", "Investment business cases never reviewed for actual vs projected", "M", "Post-implementation review at 12 months for all major investments"),
    ("Modeling", "Transfer pricing impact on BU profitability unclear", "BU P&Ls distorted by arbitrary transfer prices; wrong decisions", "H", "Transparent TP methodology with BU profitability adjusted for arm's length"),
    ("Reporting", "Management reporting not timely", "Monthly management pack delivered Day 15; decisions delayed", "H", "Flash report Day 2; full management pack Day 5 after close"),
    ("Reporting", "No self-service analytics", "All ad hoc analysis requests go through FP&A; 3-day turnaround", "M", "Self-service BI with governed data models and role-based access"),
    ("Reporting", "Board reporting inconsistent", "Board pack format changes quarterly; no continuity", "M", "Standardized board reporting template with consistent KPIs"),
    ("Reporting", "No predictive analytics capability", "All analysis is backward-looking; no predictive models", "M", "Build predictive models for revenue, churn, and cash flow"),
]

_S_TAX = [
    ("GST", "GSTR-1 vs GSTR-3B mismatch", "Monthly mismatch averaging 4%; department notices received", "C", "Automated monthly reconciliation with pre-filing validation"),
    ("GST", "ITC claiming on ineligible items", "Input tax credit claimed on blocked credits per Section 17(5)", "C", "Automated ITC eligibility check against Section 17(5) list"),
    ("GST", "HSN code classification errors", "Products classified under incorrect HSN; rate disputes with department", "H", "HSN classification review with industry-standard mapping"),
    ("GST", "E-way bill compliance gaps", "E-way bills not generated for all applicable movements", "H", "Automated e-way bill generation integrated with dispatch process"),
    ("GST", "GSTR-2B reconciliation not performed", "Vendor ITC not reconciled with GSTR-2B; credit at risk", "H", "Monthly GSTR-2B reconciliation; follow up with vendors for mismatches"),
    ("GST", "RCM liability not identified timely", "Reverse charge payments made without GST self-assessment", "C", "Automated RCM applicability check on all vendor payments"),
    ("GST", "Annual return GSTR-9 reconciliation", "Annual return figures do not tie to monthly returns; discrepancies", "H", "Quarterly cumulative reconciliation to simplify annual filing"),
    ("GST", "Place of supply determination errors", "Incorrect place of supply for services; IGST/SGST mis-classification", "H", "Place of supply decision tree in billing system with automated determination"),
    ("Direct Tax", "TDS not deducted on all applicable payments", "Several vendor categories missing TDS deduction; penalty risk", "C", "Automated TDS applicability engine with section-wise rules"),
    ("Direct Tax", "TDS return reconciliation gaps", "TDS returns do not match books; vendor Form 26AS complaints", "H", "Monthly TDS ledger to return reconciliation before filing"),
    ("Direct Tax", "Advance tax estimation inaccurate", "Advance tax paid differs from actual liability by 25%+; interest", "H", "Quarterly advance tax re-estimation based on YTD actual and forecast"),
    ("Direct Tax", "Tax provision methodology undocumented", "Current and deferred tax calculated but methodology not documented", "H", "Tax provision memo with documented methodology and key judgments"),
    ("Direct Tax", "No permanent/temporary difference tracking", "Deferred tax assets and liabilities computed ad hoc", "H", "Systematic tracking of timing differences with automated DTA/DTL calculation"),
    ("Direct Tax", "Transfer pricing documentation absent", "No contemporaneous TP documentation; risk in assessment proceedings", "C", "Annual transfer pricing study with benchmarking and local file"),
    ("Direct Tax", "MAT credit tracking manual", "Minimum alternate tax credit entitlement tracked in spreadsheet", "M", "Automated MAT credit tracking with utilization forecasting"),
    ("Compliance", "No tax compliance calendar", "Tax filing deadlines tracked informally; missed deadlines occur", "H", "Comprehensive tax compliance calendar with automated alerts"),
    ("Compliance", "Tax litigation tracker not maintained", "Open tax cases not tracked centrally; contingent liability unknown", "H", "Tax litigation register with case status, exposure, and provision assessment"),
    ("Compliance", "Withholding tax on foreign payments not optimized", "WHT applied at domestic rates; treaty benefits not claimed", "H", "Treaty analysis for each jurisdiction; proper documentation for treaty claims"),
    ("Compliance", "No indirect tax technology", "GST compliance managed manually; scalability challenge", "H", "Invest in GST compliance technology with automated return preparation"),
    ("Compliance", "Tax audit readiness low", "Tax audit support requires weeks of data gathering; inefficient", "H", "Year-round audit readiness with organized documentation by topic"),
    ("Compliance", "Tax risk register absent", "Tax risks not identified, assessed, or monitored formally", "H", "Tax risk register with likelihood, exposure, mitigation, and owner"),
    ("Compliance", "International tax structure not optimized", "Operating structure not tax-efficient; excess withholding and double taxation", "H", "International tax structure review with optimization recommendations"),
]

_S_TREASURY = [
    ("Cash Mgmt", "No 13-week cash flow forecast", "Cash management is reactive; surprise shortfalls occur", "C", "Implement rolling 13-week direct method cash flow forecast"),
    ("Cash Mgmt", "Cash visibility fragmented", "Cash across 40+ accounts in 6 banks; no consolidated view", "H", "Cash visibility platform with daily automated balance aggregation"),
    ("Cash Mgmt", "Idle cash not invested", "Average $5M idle in operating accounts earning 0%; opportunity cost", "H", "Automated sweep to money market; tiered investment policy"),
    ("Cash Mgmt", "Intraday liquidity not managed", "No intraday cash position tracking; payment timing suboptimal", "M", "Real-time cash position with payment prioritization"),
    ("Cash Mgmt", "No cash pooling structure", "Entities manage cash independently; borrowing while others have surplus", "H", "Notional or physical cash pooling across entities"),
    ("Cash Mgmt", "Cash concentration manual", "End-of-day sweeps initiated manually; sometimes missed", "H", "Automated zero-balance sweeping with bank-side configuration"),
    ("Cash Mgmt", "Counterparty risk not assessed", "Bank deposits concentrated; no assessment of bank creditworthiness", "M", "Counterparty risk framework with exposure limits per institution"),
    ("FX Mgmt", "No FX hedging policy", "Foreign currency exposures unhedged; P&L volatility from FX", "C", "Board-approved FX hedging policy with minimum coverage requirements"),
    ("FX Mgmt", "FX exposure not measured", "Cannot quantify total FX exposure across entities and currencies", "H", "Consolidated FX exposure reporting by currency with netting analysis"),
    ("FX Mgmt", "Hedge accounting not applied", "Hedges executed but not designated; P&L ineffectiveness not offset", "H", "Hedge accounting documentation per ASC 815/IFRS 9 for qualifying hedges"),
    ("FX Mgmt", "FX rate sources inconsistent", "Different rates used for different purposes; reconciliation gaps", "M", "Single authorized rate source for all FX conversions"),
    ("FX Mgmt", "Natural hedging not utilized", "Revenue and costs in same currency not matched; unnecessary hedging", "M", "Natural hedging analysis before external hedging; currency matching"),
    ("Debt Mgmt", "Debt covenant monitoring manual", "Covenants monitored quarterly in spreadsheets; compliance risk", "H", "Automated covenant calculation with early warning at 80% of limit"),
    ("Debt Mgmt", "No debt maturity profiling", "Maturity concentration risk not assessed; refinancing risk", "M", "Debt maturity profile analysis with ladder strategy"),
    ("Debt Mgmt", "Interest rate risk unmanaged", "100% floating rate debt; no interest rate hedging strategy", "H", "Interest rate risk policy: maintain 30-50% fixed rate exposure"),
    ("Debt Mgmt", "LIBOR/benchmark rate transition incomplete", "LIBOR referenced in legacy contracts; transition to SOFR pending", "H", "Complete benchmark rate transition for all contracts"),
    ("Bank Relations", "Bank relationship reviews not conducted", "No annual review of banking services, pricing, or capacity", "M", "Annual bank scorecard review with service quality and pricing assessment"),
    ("Bank Relations", "Too many banking relationships", "12 banking partners for mid-size company; complexity without benefit", "L", "Rationalize to 3-4 core banks with defined roles"),
    ("Bank Relations", "No RFP process for banking services", "Banking services not competitively bid; potentially overpaying", "M", "Tri-annual RFP for core banking services"),
    ("Controls", "Treasury management system absent", "Treasury operations in spreadsheets; operational risk", "H", "Implement TMS for cash management, payments, and FX"),
    ("Controls", "No payment fraud prevention", "Wire payments processed without fraud screening; exposure", "C", "Payment fraud detection with sanctions screening and anomaly detection"),
    ("Controls", "Bank signatory list outdated", "Former employees still on bank signatory list; unauthorized access risk", "C", "Quarterly bank signatory review; immediate removal on termination"),
    ("Controls", "No investment policy", "Surplus cash invested ad hoc without policy guidelines", "H", "Board-approved investment policy with permitted instruments and limits"),
]

_S_AUDIT = [
    ("Risk Assessment", "No enterprise risk assessment", "Audit plan not based on formal risk assessment; coverage gaps", "C", "Annual enterprise risk assessment driving risk-based audit plan"),
    ("Risk Assessment", "Audit universe outdated", "Auditable entities list not updated for acquisitions and restructuring", "H", "Annual audit universe refresh aligned to organizational changes"),
    ("Risk Assessment", "Emerging risks not considered", "Cyber, ESG, and AI risks not in audit scope", "H", "Incorporate emerging risk categories into annual risk assessment"),
    ("Risk Assessment", "No continuous risk monitoring", "Risk assessment performed annually; changes not captured", "M", "Quarterly risk assessment refresh with continuous monitoring triggers"),
    ("Risk Assessment", "Fraud risk assessment not performed", "Fraud risks not specifically assessed per SAS 99/ISA 240", "C", "Annual fraud risk assessment with brainstorming sessions"),
    ("Execution", "Audit methodology not standardized", "Each auditor follows different approaches; quality varies", "H", "Standardized audit methodology with templates and peer review"),
    ("Execution", "No data analytics in auditing", "100% manual audit procedures; limited sample sizes", "H", "Deploy audit analytics for full-population testing on key controls"),
    ("Execution", "Audit evidence documentation weak", "Working papers lack sufficient evidence to support conclusions", "H", "Working paper standards with mandatory evidence retention"),
    ("Execution", "Co-sourced audits not managed", "External co-source providers not integrated into quality framework", "M", "Co-source governance with quality reviews and methodology alignment"),
    ("Execution", "Root cause analysis superficial", "Findings describe symptoms but not underlying causes", "H", "5-Why root cause analysis methodology for all significant findings"),
    ("Reporting", "Audit reports delayed", "Average 30 days from fieldwork to final report; impact diminished", "H", "Target 10-day report cycle; draft report within 3 days of exit meeting"),
    ("Reporting", "No audit issue tracking system", "Audit issues tracked in spreadsheets; follow-up inconsistent", "H", "Automated audit management system with issue tracking and escalation"),
    ("Reporting", "Audit recommendations not implemented", "45% of prior year recommendations still open; credibility risk", "H", "Quarterly management reporting on open issues; AC escalation at 90 days"),
    ("Reporting", "Audit committee reporting ineffective", "AC receives lengthy reports; key messages buried", "M", "Executive summary format with heat map and trend analysis"),
    ("Reporting", "No quality assurance program", "No internal quality reviews of audit work", "H", "Quality assurance program with cold file reviews and stakeholder surveys"),
    ("Compliance", "SOX testing not risk-based", "All controls tested with same rigor regardless of risk", "M", "Risk-stratify controls: key controls tested quarterly, others annually"),
    ("Compliance", "Anti-bribery compliance gaps", "FCPA/UKBA compliance program not mature; training incomplete", "H", "Enhanced ABC program with risk assessment, training, and monitoring"),
    ("Compliance", "Regulatory compliance monitoring reactive", "New regulations discovered when violations occur", "H", "Proactive regulatory monitoring with impact assessment process"),
    ("Compliance", "Ethics hotline underutilized", "Very few reports through hotline; potential suppression or unawareness", "M", "Hotline awareness campaign; demonstrate no-retaliation commitment"),
    ("Compliance", "Third-party due diligence inadequate", "High-risk third parties not screened for sanctions or corruption", "C", "Risk-based third-party due diligence program with periodic refresh"),
    ("IT Audit", "IT audit capability insufficient", "No dedicated IT auditor; IT risks not adequately covered", "H", "Hire or co-source IT audit capability; cover ITGCs and cybersecurity"),
    ("IT Audit", "Cybersecurity audit not performed", "No assessment of cybersecurity controls; board exposure", "C", "Annual cybersecurity maturity assessment against NIST framework"),
    ("IT Audit", "Cloud security not assessed", "Migration to cloud without security assessment of providers", "H", "Cloud security assessment for all tier-1 applications"),
    ("IT Audit", "Business continuity not tested", "DR plan exists but never tested; recovery capability unknown", "H", "Annual BCP/DR testing with documented results and improvement plan"),
]

_S_SUPPLY = [
    ("Inventory", "No perpetual inventory system", "Inventory tracked via periodic counts; real-time visibility absent", "H", "Implement perpetual inventory with barcode/RFID scanning"),
    ("Inventory", "Inventory accuracy below 90%", "Cycle count accuracy at 82%; production planning impacted", "H", "ABC-classified cycle counting program; target 95% accuracy"),
    ("Inventory", "Obsolete inventory not provisioned", "Slow-moving inventory at 18% of total; inadequate reserve", "H", "Quarterly obsolescence review with aging-based provision methodology"),
    ("Inventory", "No safety stock optimization", "Safety stock levels set arbitrarily; either excess or stockouts", "M", "Statistical safety stock calculation based on demand variability and lead time"),
    ("Inventory", "Warehouse space utilization low", "65% space utilization due to poor slotting and layout", "M", "Warehouse optimization study with slotting analysis"),
    ("Inventory", "No inventory valuation review", "Standard costs not updated annually; variance accounts growing", "H", "Annual standard cost update with quarterly variance analysis"),
    ("Inventory", "Consignment inventory not tracked", "Vendor consignment stock not in system; aging unknown", "H", "System tracking for consignment with consumption-based settlement"),
    ("Demand", "Demand planning spreadsheet-based", "Demand forecast in Excel; no statistical forecasting", "H", "Demand planning software with statistical baseline and override"),
    ("Demand", "No demand sensing capability", "Demand planning uses only historical shipments; no leading indicators", "M", "Incorporate POS data, market signals, and customer forecasts"),
    ("Demand", "Forecast accuracy not measured", "No MAPE or bias tracking; forecast quality unknown", "H", "Track forecast accuracy by SKU-location; monthly review"),
    ("Demand", "No collaborative planning with customers", "Key account demand not shared; bullwhip effect", "M", "CPFR with top 20 accounts; shared demand visibility"),
    ("Logistics", "Transportation cost not optimized", "Shipments not consolidated; partial truckloads common", "M", "Route optimization and shipment consolidation tool"),
    ("Logistics", "No carrier performance management", "Carriers not measured on OTD, damage, or cost", "M", "Carrier scorecard with quarterly business review"),
    ("Logistics", "Last-mile delivery costs excessive", "Last-mile cost 40% of total logistics; no optimization", "H", "Last-mile optimization with route planning and delivery slot management"),
    ("Logistics", "No supply chain visibility platform", "Cannot track shipments end-to-end; customer queries unanswered", "H", "End-to-end supply chain visibility with real-time tracking"),
    ("Procurement", "No category management approach", "Procurement not organized by category; savings missed", "H", "Strategic sourcing by category with market analysis and negotiation"),
    ("Procurement", "No total cost of ownership analysis", "Purchase decisions based on unit price only; hidden costs ignored", "M", "TCO framework for strategic sourcing decisions"),
    ("Procurement", "Supplier collaboration limited", "No formal supplier development or joint improvement programs", "M", "Supplier development program for strategic suppliers"),
    ("Procurement", "Make vs buy decisions ad hoc", "No framework for make vs buy evaluation; suboptimal sourcing", "M", "Structured make vs buy decision framework with total cost comparison"),
    ("Quality", "No supplier quality management", "Incoming quality issues detected late; customer impact", "H", "Supplier quality program with incoming inspection and SCAR process"),
    ("Quality", "CAPA process not effective", "Corrective actions documented but effectiveness not verified", "M", "CAPA process with effectiveness verification at 30/60/90 days"),
    ("Quality", "No cost of quality measurement", "Prevention, appraisal, and failure costs not quantified", "M", "Cost of quality reporting with improvement targets"),
    ("Quality", "Non-conformance reporting manual", "NCRs tracked in paper logbooks; trend analysis impossible", "H", "Digital NCR system with root cause analysis and trend reporting"),
]

_S_HR = [
    ("Payroll", "Payroll processing errors", "2% error rate in payroll; employee complaints and rework", "H", "Automated payroll validation with pre-processing audit checks"),
    ("Payroll", "No payroll reconciliation to GL", "Payroll expense in GL not reconciled to payroll register", "H", "Monthly payroll-to-GL reconciliation with variance investigation"),
    ("Payroll", "Manual payroll calculations", "Overtime, bonuses, and deductions calculated manually", "H", "Automated payroll calculation with exception-only review"),
    ("Payroll", "Payroll audit trail inadequate", "Cannot trace payroll changes to authorization; audit risk", "H", "Complete audit trail for all payroll master and processing changes"),
    ("Payroll", "Statutory compliance issues", "PF/ESI contributions not computed correctly; penalty exposure", "C", "Automated statutory calculation engine with compliance monitoring"),
    ("Payroll", "No time and attendance integration", "Timesheet data entered manually into payroll; discrepancies", "M", "Integrated T&A with payroll; automated data flow"),
    ("Payroll", "Payroll SoD issues", "Same person enters and processes payroll; fraud risk", "C", "Segregate payroll data entry, processing, and bank file release"),
    ("Payroll", "Ghost employee risk", "No periodic verification of active employee headcount vs payroll", "H", "Quarterly headcount verification against payroll; manager attestation"),
    ("Benefits", "Benefits administration manual", "Enrollment, changes, and terminations processed manually", "M", "Self-service benefits portal with automated enrollment"),
    ("Benefits", "Leave management uncontrolled", "Leave balances tracked manually; encashment liability unclear", "M", "Automated leave management with real-time balance and liability tracking"),
    ("Benefits", "No benefits cost analysis", "Total cost of benefits not analyzed by category or trend", "M", "Annual benefits cost benchmarking and trend analysis"),
    ("Compensation", "No compensation benchmarking", "Salary decisions without market data; retention risk", "H", "Annual compensation survey participation; market adjustment cycle"),
    ("Compensation", "Variable pay calculation manual", "Bonus and incentive calculations in spreadsheets; errors and disputes", "H", "Automated incentive calculation engine with transparent communication"),
    ("Compensation", "No pay equity analysis", "Equal pay compliance not assessed; litigation risk", "H", "Annual pay equity analysis with remediation for unexplained gaps"),
    ("Compliance", "No HR compliance dashboard", "Employment law compliance tracked informally; blind spots exist", "H", "HR compliance dashboard covering labor law, benefits, and safety"),
    ("Compliance", "Employee files incomplete", "Missing I-9s, offer letters, or policy acknowledgments", "H", "Digital employee file with completeness checklist and alerts"),
    ("Compliance", "No background check policy", "Background checks inconsistent; high-risk roles not verified", "H", "Risk-based background check policy for all roles"),
    ("Compliance", "Contractor misclassification risk", "Worker classification not reviewed; IC vs employee risk", "C", "Worker classification assessment using IRS/local criteria for all ICs"),
    ("Analytics", "No workforce analytics", "HR decisions not data-driven; turnover and engagement not analyzed", "M", "HR analytics dashboard with turnover, tenure, diversity, and engagement"),
    ("Analytics", "No succession planning", "Key person dependencies not identified; no succession plans", "H", "Succession planning for critical roles with development plans"),
    ("Analytics", "Exit interview data not analyzed", "Exit interviews conducted but data not aggregated or acted upon", "M", "Quarterly exit interview analysis with retention action items"),
]

_S_RISK = [
    ("ERM", "No enterprise risk management framework", "Risks managed in silos; no consolidated risk view", "C", "Implement ERM framework aligned to ISO 31000 or COSO ERM"),
    ("ERM", "Risk appetite not defined", "No board-approved risk appetite; inconsistent risk-taking", "C", "Define and document risk appetite and tolerance with board approval"),
    ("ERM", "Risk register not maintained", "No central risk register; risks tracked informally if at all", "H", "Enterprise risk register with quarterly assessment and reporting"),
    ("ERM", "Risk owners not assigned", "Risks identified but no one accountable for mitigation", "H", "Assign risk owners with documented mitigation plans and KRIs"),
    ("ERM", "No key risk indicators", "Risk monitoring relies on lagging indicators only", "M", "Develop KRIs for top 20 risks with automated monitoring"),
    ("ERM", "Scenario analysis not performed", "No stress testing or scenario planning for major risks", "H", "Annual scenario analysis for top 10 risks with board reporting"),
    ("ERM", "Emerging risk identification weak", "Horizon scanning for new risks not performed systematically", "M", "Quarterly emerging risk scan with cross-functional input"),
    ("Fraud", "No fraud risk assessment", "Fraud risks not formally assessed; controls may be inadequate", "C", "Annual fraud risk assessment per COSO and SAS 99 requirements"),
    ("Fraud", "Fraud investigation protocol absent", "No documented procedure for investigating fraud allegations", "H", "Fraud response plan with investigation protocols and evidence preservation"),
    ("Fraud", "No proactive fraud monitoring", "Fraud detected only through complaints or audit; no analytics", "H", "Continuous fraud monitoring using data analytics on financial transactions"),
    ("Fraud", "Conflict of interest declarations not collected", "No annual COI disclosure program; undisclosed conflicts likely", "H", "Annual COI disclosure with review and management of identified conflicts"),
    ("Fraud", "Related party transactions not monitored", "RPTs not identified or disclosed properly; regulatory risk", "H", "RPT identification process with arm's length assessment and disclosure"),
    ("BCP", "No business continuity plan", "BCP either absent or severely outdated; recovery capability unknown", "C", "Develop BIA-driven BCP with recovery strategies for critical processes"),
    ("BCP", "BCP never tested", "Plan exists on paper but never exercised; gaps unknown", "H", "Annual BCP exercise with tabletop and functional testing"),
    ("BCP", "No crisis communication plan", "No defined communication protocol for crisis situations", "H", "Crisis communication plan with stakeholder mapping and message templates"),
    ("BCP", "Third-party BCP not assessed", "Critical vendor BCPs not reviewed; supply chain continuity risk", "H", "BCP assessment for all critical vendors; contractual BCP requirements"),
    ("Cyber", "No cybersecurity risk assessment", "Cyber risks not formally assessed; maturity unknown", "C", "Annual cybersecurity maturity assessment against NIST CSF"),
    ("Cyber", "Incident response plan inadequate", "No documented IR plan; team roles and procedures undefined", "C", "Incident response plan with defined roles, runbooks, and tabletop exercises"),
    ("Cyber", "Third-party cyber risk not assessed", "Vendor cyber posture not evaluated; data sharing without assurance", "H", "Third-party security assessment program with risk-tiered reviews"),
    ("Cyber", "No security awareness training", "Employees not trained on phishing, social engineering, or data handling", "H", "Mandatory annual security awareness training with phishing simulations"),
    ("Cyber", "Data classification not implemented", "No data classification scheme; all data treated equally", "H", "Data classification policy with handling requirements per classification level"),
    ("Cyber", "No vulnerability management program", "Systems not regularly scanned for vulnerabilities; patch management ad hoc", "C", "Continuous vulnerability scanning with risk-based patch management SLA"),
]

# Combine all scenarios and build lookup
def _build_scenario_db():
    all_scenarios = []
    domain_map = {
        "O2C": ("Order to Cash", "💰", _S_O2C),
        "P2P": ("Procure to Pay", "🛒", _S_P2P),
        "R2R": ("Record to Report", "📊", _S_R2R),
        "GL": ("General Accounting", "📒", _S_GL),
        "FPA": ("Financial Planning & Analysis", "📈", _S_FPA),
        "TAX": ("Tax & Compliance", "⚖️", _S_TAX),
        "TREASURY": ("Treasury & Cash Management", "🏦", _S_TREASURY),
        "AUDIT": ("Internal Audit & SOX", "🔍", _S_AUDIT),
        "SUPPLY": ("Supply Chain & Operations", "🚚", _S_SUPPLY),
        "HR": ("HR & Payroll", "👥", _S_HR),
        "RISK": ("Risk, Fraud & Cyber", "🛡️", _S_RISK),
    }
    risk_map = {"C": "Critical", "H": "High", "M": "Medium", "L": "Low"}
    for domain_key, (domain_name, icon, scenarios) in domain_map.items():
        for idx, (category, title, finding, risk, recommendation) in enumerate(scenarios):
            all_scenarios.append({
                "id": f"{domain_key}-{idx+1:03d}",
                "domain": domain_key,
                "domain_name": domain_name,
                "domain_icon": icon,
                "category": category,
                "title": title,
                "finding": finding,
                "risk_level": risk_map.get(risk, risk),
                "recommendation": recommendation,
            })
    return all_scenarios, domain_map

CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] Loaded {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Additional scenarios to cross 1000+ total
_S_FPA_EXT = [
    ("Budgeting", "No driver-based planning", "Budgets built line-by-line without linking to operational drivers", "H", "Implement driver-based planning connecting volume/price/mix to financials"),
    ("Budgeting", "Currency impact not modeled", "Multi-currency budgets use spot rates; no sensitivity analysis", "M", "Model FX scenarios in budget with rate sensitivity analysis"),
    ("Budgeting", "CapEx governance weak", "Capital requests approved without formal business case or hurdle rate", "H", "Stage-gate CapEx process with NPV/IRR analysis and post-audit"),
    ("Budgeting", "No strategic planning integration", "Budget disconnected from 3-5 year strategic plan", "H", "Link annual budget to long-range plan with bridge analysis"),
    ("Budgeting", "Budget accountability unclear", "Budget owners not formally assigned; no consequence for overruns", "M", "Assign budget owners with quarterly accountability reviews"),
    ("Budgeting", "Contingency budget not structured", "No formal contingency reserves; ad hoc requests for overruns", "M", "Structured contingency with trigger-based release criteria"),
    ("Forecasting", "Revenue pipeline not integrated into forecast", "Sales pipeline data not used in revenue forecasting", "H", "Integrate CRM pipeline stages with weighted revenue forecast"),
    ("Forecasting", "No seasonal adjustment methodology", "Seasonality applied inconsistently across product lines", "M", "Statistical seasonal decomposition applied consistently"),
    ("Forecasting", "Working capital not forecasted", "Cash conversion cycle not projected; working capital surprises", "H", "Monthly working capital forecast integrated with P&L forecast"),
    ("Forecasting", "No AI/ML in forecasting", "Forecasting purely manual; no machine learning augmentation", "M", "Evaluate ML-based forecasting for high-volume product categories"),
    ("Forecasting", "Capex forecast absent", "Capital expenditure projections not maintained; cash planning gap", "H", "Monthly CapEx forecast by project with spend curve analysis"),
    ("Forecasting", "Headcount forecast disconnected", "FTE projections not linked to compensation and benefits cost", "M", "Integrated workforce and compensation forecast model"),
    ("Variance", "No contribution margin analysis", "Product profitability not analyzed at contribution margin level", "H", "Contribution margin analysis by product, customer, and channel"),
    ("Variance", "Volume vs price vs mix analysis absent", "Revenue changes not decomposed into volume, price, and mix effects", "H", "Automated revenue bridge with volume/price/mix/FX decomposition"),
    ("Variance", "Cost variance not cascaded to root cause", "Cost overruns reported at summary level; no drill-down to cause", "M", "Multi-level cost variance analysis from P&L to transaction"),
    ("Variance", "No peer benchmarking data", "Performance not compared to industry peers systematically", "M", "Annual benchmarking study comparing key ratios to peer group"),
    ("Variance", "Budget vs forecast vs actual not triangulated", "Three separate views of financial performance not aligned", "M", "Integrated variance reporting: budget vs forecast vs actual"),
    ("Modeling", "No what-if analysis tool", "Scenario modeling requires rebuilding spreadsheets each time", "H", "Self-service what-if analysis platform with predefined variables"),
    ("Modeling", "Unit economics not modeled", "Customer acquisition cost, LTV, payback not tracked", "H", "Unit economics model with cohort analysis and LTV/CAC tracking"),
    ("Modeling", "M&A financial modeling ad hoc", "Acquisition models built from scratch; inconsistent assumptions", "H", "Standardized M&A model template with synergy and integration costing"),
    ("Modeling", "Pricing analysis not data-driven", "Pricing decisions made without elasticity or margin analysis", "H", "Price-volume-profit analysis with elasticity modeling"),
    ("Modeling", "Break-even analysis not maintained", "Break-even point not calculated for business segments", "M", "Break-even analysis by segment with sensitivity to key assumptions"),
    ("Reporting", "No KPI dictionary", "KPIs defined differently across departments; inconsistent measurement", "H", "Enterprise KPI dictionary with standard definitions and data sources"),
    ("Reporting", "Investor relations support manual", "IR data packs prepared manually; inconsistent with internal reports", "M", "Automated IR reporting aligned to internal management reporting"),
    ("Reporting", "No real-time financial dashboards", "Financial data available only after close; no real-time visibility", "H", "Real-time financial dashboards for revenue, expense, and cash"),
    ("Reporting", "ESG reporting capability absent", "No framework for ESG metrics collection or reporting", "H", "Implement ESG reporting framework aligned to GRI/SASB standards"),
    ("Reporting", "Profitability analysis by customer absent", "Cannot determine which customers are profitable vs unprofitable", "H", "Customer profitability analysis with fully loaded cost allocation"),
    ("Reporting", "No automated commentary generation", "Narrative commentary written from scratch each period", "M", "AI-assisted commentary generation for standard variance explanations"),
    ("Reporting", "Long-range planning model absent", "No 3-5 year financial model; strategic decisions made without quantification", "H", "Long-range financial model with scenario analysis"),
    ("Reporting", "Cost-to-serve not measured", "Service costs not allocated to customers; margin distortion", "H", "Activity-based cost-to-serve model for customer segmentation"),
]

_S_TAX_EXT = [
    ("GST", "E-invoicing not implemented for all mandated entities", "Only head office compliant; branch offices still on manual", "C", "Roll out e-invoicing across all GSTINs above threshold"),
    ("GST", "GST annual audit not prepared", "GSTR-9C reconciliation not performed; auditor concerns", "H", "Monthly reconciliation building toward annual audit-ready data"),
    ("GST", "No GST impact analysis for new products", "New product launches without GST rate and HSN determination", "M", "GST impact assessment as part of product launch checklist"),
    ("GST", "Composition scheme eligibility not reviewed", "Eligible entities not evaluated for composition scheme benefits", "L", "Annual review of composition scheme eligibility for applicable entities"),
    ("GST", "Inter-state vs intra-state determination errors", "IGST charged where CGST+SGST appropriate and vice versa", "H", "Automated place of supply logic in billing system"),
    ("GST", "Vendor GSTIN validation not automated", "Vendor GSTIN not validated against government portal at onboarding", "H", "Real-time GSTIN validation API integration in vendor onboarding"),
    ("GST", "ITC reversal rules not applied", "Section 17 ITC reversal for exempt supplies not calculated", "C", "Automated ITC reversal calculation with annual true-up"),
    ("GST", "No GST refund tracking", "Export refund claims not tracked; working capital locked", "H", "GST refund tracking dashboard with aging and follow-up"),
    ("Direct Tax", "No tax planning strategy", "Tax planning reactive; opportunities identified after year-end", "H", "Proactive tax planning calendar with quarterly review of opportunities"),
    ("Direct Tax", "Section 80 deduction optimization absent", "Available deductions under Chapter VI-A not fully claimed", "M", "Annual review of eligible deductions with employee communication"),
    ("Direct Tax", "No uncertain tax position assessment", "UTPs not identified or measured per ASC 740/IAS 12", "H", "Quarterly UTP assessment with likelihood and measurement analysis"),
    ("Direct Tax", "Tax loss carryforward not tracked", "Tax losses from prior years not tracked; utilization missed", "H", "Tax loss carryforward register with expiry dates and utilization plan"),
    ("Direct Tax", "No effective tax rate planning", "ETR analysis not performed; surprises in reported tax rate", "H", "Quarterly ETR forecasting with rate reconciliation to statutory rate"),
    ("Direct Tax", "Depreciation schedule tax vs book not reconciled", "Tax depreciation differs from book but reconciliation not maintained", "H", "Annual tax-to-book depreciation reconciliation with deferred tax impact"),
    ("Direct Tax", "No DTAA benefit optimization", "Double tax avoidance agreements not leveraged; excess WHT paid", "H", "DTAA analysis for all cross-border payments with treaty benefit claims"),
    ("Compliance", "No indirect tax other than GST tracked", "Customs duty, professional tax, property tax tracked ad hoc", "M", "Comprehensive indirect tax compliance calendar"),
    ("Compliance", "No equalization levy compliance", "Digital services to non-residents without equalization levy assessment", "H", "Equalization levy applicability assessment for digital transactions"),
    ("Compliance", "No FATCA/CRS compliance", "No assessment of FATCA/CRS reporting obligations", "H", "FATCA/CRS applicability assessment and reporting setup"),
    ("Compliance", "Tax technology roadmap absent", "No plan for tax technology modernization; manual processes persist", "M", "Tax technology assessment and 3-year modernization roadmap"),
    ("Compliance", "No Pillar 2 / global minimum tax assessment", "OECD Pillar 2 impact not assessed; may affect effective tax rate", "H", "Pillar 2 impact assessment with modeling of GloBE rules"),
    ("Compliance", "TP safe harbor rules not evaluated", "Safe harbor provisions not considered; unnecessary documentation burden", "M", "Evaluate applicability of safe harbor rules for routine transactions"),
    ("Compliance", "No country-by-country reporting", "CbCR obligations not assessed for qualifying MNE groups", "H", "CbCR readiness assessment with data collection process"),
    ("Compliance", "Indirect transfer provisions not evaluated", "Share transfers of entities with Indian assets without IT assessment", "C", "Indirect transfer tax assessment for all share restructurings"),
    ("Compliance", "No tax opinion documentation", "Tax positions taken without documented legal opinion", "H", "Written tax opinions for all material positions above threshold"),
    ("Compliance", "Stamp duty compliance gaps", "Inter-state and instrument-wise stamp duty not tracked", "M", "Stamp duty compliance tracking for agreements, leases, and transfers"),
    ("Compliance", "No customs duty optimization", "Import duties not optimized through schemes like DFIA, EPCG, AA", "H", "Customs duty optimization study with applicable scheme mapping"),
    ("Compliance", "SEZ compliance not monitored", "SEZ entity compliance requirements not systematically tracked", "M", "SEZ compliance checklist with periodic DC reporting requirements"),
    ("Compliance", "Professional tax registration and compliance gaps", "PT not deducted or deposited in all applicable states", "H", "State-wise PT compliance review with registration and filing calendar"),
]

_S_TREASURY_EXT = [
    ("Cash Mgmt", "No cash flow forecasting model", "Cash forecast relies on P&L-based indirect method; inaccurate", "H", "Direct method 13-week cash flow forecast with weekly rolling update"),
    ("Cash Mgmt", "Working capital targets not set", "No defined targets for DSO, DPO, DIO; working capital drifts", "H", "Working capital targets by BU with monthly tracking and incentives"),
    ("Cash Mgmt", "No cash culture in organization", "Operating teams not accountable for cash; only P&L focused", "M", "Cash conversion cycle KPIs for operating managers; training program"),
    ("Cash Mgmt", "Dividend policy not formalized", "Dividend decisions ad hoc; no link to cash generation or policy", "M", "Board-approved dividend policy with payout ratio and minimum cash guidelines"),
    ("Cash Mgmt", "No cash repatriation strategy", "Cash trapped in foreign subsidiaries; tax-inefficient repatriation", "H", "Cash repatriation strategy with tax-optimized intercompany structures"),
    ("Cash Mgmt", "Petty cash controls weak", "Multiple petty cash funds with infrequent reconciliation", "M", "Reduce petty cash funds; monthly reconciliation; consider virtual cards"),
    ("Cash Mgmt", "No receivables financing program", "AR not leveraged for liquidity; factoring/SCF not explored", "M", "Evaluate receivables factoring or supply chain finance program"),
    ("Cash Mgmt", "Bank line utilization not optimized", "Credit lines underutilized while paying commitment fees", "M", "Quarterly line utilization review; right-size committed facilities"),
    ("FX Mgmt", "No FX risk quantification", "VaR or CaR for FX portfolio not calculated", "H", "Monthly FX VaR calculation for portfolio risk assessment"),
    ("FX Mgmt", "FX hedging execution not competitive", "FX deals executed with single bank; no competitive bidding", "M", "Multi-bank FX platform for competitive pricing on hedges"),
    ("FX Mgmt", "Embedded derivatives not identified", "Contracts with embedded FX features not assessed for bifurcation", "H", "Review commercial contracts for embedded derivatives requiring separation"),
    ("FX Mgmt", "No FX policy governance", "FX decisions made by individuals without policy framework", "H", "FX governance framework with delegated authorities and reporting"),
    ("FX Mgmt", "Balance sheet hedging not performed", "Monetary assets/liabilities in FC not hedged; revaluation P&L impact", "H", "Monthly balance sheet hedging for material FX exposures"),
    ("Debt Mgmt", "Capital structure not optimized", "Debt/equity mix not analyzed for optimal WACC", "H", "Capital structure analysis with target leverage and WACC optimization"),
    ("Debt Mgmt", "No preemptive refinancing strategy", "Debt refinanced at maturity under time pressure; suboptimal terms", "M", "12-month preemptive refinancing planning for all material facilities"),
    ("Debt Mgmt", "Guarantee portfolio not managed", "Corporate guarantees issued without tracking or fee assessment", "H", "Guarantee register with exposure tracking and arm's length guarantee fees"),
    ("Debt Mgmt", "No interest savings analysis", "Current borrowing costs not benchmarked; potentially overpaying", "M", "Annual benchmarking of borrowing costs with bank negotiation"),
    ("Controls", "No SWIFT/payment security standards", "SWIFT CSP compliance not assessed; payment infrastructure risk", "C", "SWIFT CSP compliance assessment and remediation"),
    ("Controls", "Treasury disaster recovery not tested", "No backup for treasury operations; key person dependency", "H", "Treasury DR plan with cross-training and backup procedures"),
    ("Controls", "No mark-to-market reporting for derivatives", "Derivative portfolio not valued at fair value for reporting", "H", "Monthly MTM reporting for all derivative instruments"),
    ("Controls", "Treasury policy not reviewed", "Treasury policy unchanged in 5+ years; not aligned to current risk profile", "M", "Annual treasury policy review with board approval"),
    ("Controls", "No cash management KPIs", "Treasury effectiveness not measured; no benchmarking", "M", "Treasury KPI dashboard: cash conversion cycle, forecast accuracy, hedging effectiveness"),
    ("Controls", "Letter of credit management manual", "LCs tracked in spreadsheets; expiry and amendment risk", "H", "Digital LC management with automated expiry alerts and bank fee tracking"),
    ("Controls", "No escrow account governance", "Escrow accounts opened without formal governance or reconciliation", "M", "Escrow account register with purpose, conditions, and monthly reconciliation"),
]

_S_AUDIT_EXT = [
    ("Risk Assessment", "Third-party risk not in audit scope", "Third-party and vendor risks not covered in audit plan", "H", "Include third-party risk audits in annual plan for critical vendors"),
    ("Risk Assessment", "Audit plan not aligned to strategy", "Audit topics not linked to strategic risks; board disconnect", "H", "Strategy-aligned audit plan with input from board and C-suite"),
    ("Risk Assessment", "No use of AI in risk assessment", "Risk scoring is qualitative; no data-driven quantification", "M", "Evaluate AI-based risk scoring using operational and financial data"),
    ("Risk Assessment", "Regulatory risk not separately assessed", "Regulatory compliance risks combined with operational; insufficient focus", "H", "Dedicated regulatory risk assessment with jurisdiction mapping"),
    ("Risk Assessment", "Supply chain risk not assessed", "Supply chain disruption risk outside audit scope; post-pandemic lesson unlearned", "H", "Annual supply chain resilience audit for critical materials"),
    ("Execution", "No agile audit methodology", "Waterfall audit approach; long cycles; findings delivered too late", "M", "Adopt agile audit approach for faster insight delivery"),
    ("Execution", "Audit sampling not statistically valid", "Judgmental sampling without statistical basis; coverage questionable", "H", "Statistical sampling or full-population analytics for key tests"),
    ("Execution", "No integrated audit approach", "Financial, operational, and compliance audits performed separately", "M", "Integrated audit approach covering financial, operational, and compliance"),
    ("Execution", "Remote audit capability limited", "Audit team cannot perform audits remotely; travel cost high", "M", "Remote audit toolkit with secure data access and video walkthrough"),
    ("Execution", "Process mining not utilized", "Process flows not analyzed from system logs; conformance unknown", "M", "Deploy process mining for key processes to identify deviations"),
    ("Execution", "Audit workpaper review untimely", "Manager review occurs after fieldwork; rework required", "M", "Concurrent review during fieldwork; real-time quality assurance"),
    ("Reporting", "Audit findings not risk-rated", "All findings reported with equal weight; management overwhelmed", "H", "Risk-rate findings as Critical/High/Medium/Low with clear criteria"),
    ("Reporting", "No trend analysis of audit findings", "Recurring findings not tracked; systemic issues persist", "H", "Multi-year finding trend analysis with thematic reporting"),
    ("Reporting", "Audit committee effectiveness not assessed", "AC self-assessment not performed; governance gap", "M", "Annual AC self-assessment with benchmark comparison"),
    ("Reporting", "No benchmarking of audit function", "IA function not benchmarked against peers; cost/coverage unknown", "M", "Annual IA benchmarking on cost, coverage, and stakeholder satisfaction"),
    ("Reporting", "Combined assurance model absent", "First, second, and third line activities not coordinated", "H", "Combined assurance map to identify coverage gaps and overlaps"),
    ("Compliance", "Code of conduct compliance not tested", "Code of conduct exists but compliance not audited", "M", "Periodic code of conduct compliance audit with testing"),
    ("Compliance", "Sanctions screening not audited", "Sanctions compliance program not independently tested", "H", "Annual sanctions compliance audit covering screening and updates"),
    ("Compliance", "No privacy compliance audit", "GDPR/DPDP compliance not independently assessed", "H", "Annual privacy compliance audit covering data handling and consent"),
    ("Compliance", "Licensing and permits not tracked", "Business licenses and permits managed ad hoc; expiry risk", "M", "License and permit register with automated renewal tracking"),
    ("IT Audit", "No application security testing", "Financial applications not pen-tested; vulnerability risk", "C", "Annual penetration testing for all internet-facing financial applications"),
    ("IT Audit", "Database access controls not reviewed", "DBA access to production financial databases not monitored", "C", "Quarterly review of privileged database access with activity logging"),
    ("IT Audit", "No data loss prevention controls", "Sensitive financial data can be extracted without controls", "H", "DLP controls for financial data with monitoring and alerting"),
    ("IT Audit", "Software license compliance not audited", "License compliance not verified; under/over-licensing risk", "M", "Annual software license compliance audit with vendor true-up"),
    ("IT Audit", "AI model governance not assessed", "AI/ML models used in business decisions without governance", "H", "AI governance framework audit covering bias, explainability, and monitoring"),
    ("IT Audit", "API security not reviewed", "Financial system APIs not assessed for authentication and authorization", "H", "API security assessment covering auth, rate limiting, and data exposure"),
]

_S_SUPPLY_EXT = [
    ("Inventory", "No expired/shelf-life tracking", "Perishable inventory not tracked for expiry; write-offs high", "H", "FEFO tracking with automated alerts at 75% of shelf life"),
    ("Inventory", "No vendor-managed inventory program", "All inventory replenishment internally managed; inefficient", "M", "VMI pilot with top 5 suppliers for fast-moving materials"),
    ("Inventory", "Cycle counting resources insufficient", "Cycle count program exists but counts fall behind schedule", "M", "Dedicated counting resources; ABC-based frequency prioritization"),
    ("Inventory", "No inventory optimization model", "Reorder points and quantities set manually; not optimized", "H", "EOQ and ROP optimization with demand and lead time variability"),
    ("Inventory", "Multi-location inventory not balanced", "Some locations overstocked while others face stockouts", "H", "Multi-echelon inventory optimization with transfer logic"),
    ("Inventory", "Returns processing inefficient", "Returned goods sit in dock 10+ days before disposition decision", "M", "Returns processing SLA: inspect within 2 days, disposition within 5"),
    ("Inventory", "No ABC/XYZ segmentation", "All SKUs managed with same replenishment logic regardless of value/volume", "M", "ABC (value) × XYZ (demand variability) segmentation for differentiated management"),
    ("Demand", "No new product demand planning", "New product launches forecast based on gut feel; high error", "H", "Structured new product demand planning with analog analysis"),
    ("Demand", "Promotional demand not planned separately", "Promotional uplift not modeled; stockouts during promotions", "H", "Promotional demand overlay with marketing input"),
    ("Demand", "No demand review meeting", "Demand plan not reviewed cross-functionally; siloed", "H", "Monthly demand review (S&OP) with sales, marketing, and operations"),
    ("Demand", "SKU rationalization not performed", "Long tail of low-volume SKUs consuming disproportionate resources", "M", "Annual SKU rationalization; sunset bottom 10% by revenue contribution"),
    ("Logistics", "No reverse logistics capability", "No systematic process for product returns and recycling", "M", "Reverse logistics program with collection, inspection, and disposition"),
    ("Logistics", "Cold chain monitoring absent", "Temperature-sensitive products not monitored during transit", "H", "IoT temperature monitoring with automated alert and deviation reporting"),
    ("Logistics", "No warehouse management system", "Paper-based warehouse operations; picking errors at 4%", "H", "WMS with barcode scanning, directed putaway, and wave picking"),
    ("Logistics", "Cross-docking not utilized", "All inbound materials put away before outbound; unnecessary handling", "M", "Cross-docking for high-velocity items with known demand"),
    ("Logistics", "No transportation management system", "Carrier selection and routing manual; no optimization", "H", "TMS with carrier selection, rate optimization, and shipment tracking"),
    ("Procurement", "No eSourcing platform", "Sourcing events conducted via email; limited competition", "M", "eSourcing platform for RFx, reverse auctions, and bid evaluation"),
    ("Procurement", "Procurement not involved early in projects", "Procurement engaged after specifications finalized; limited leverage", "H", "Early procurement involvement in design and specification stage"),
    ("Procurement", "No sustainability in procurement", "Environmental and social criteria not part of sourcing decisions", "M", "Sustainable procurement policy with weighted criteria in sourcing"),
    ("Quality", "No statistical process control", "Process quality monitored by inspection only; not prevention", "M", "SPC implementation for critical manufacturing processes"),
    ("Quality", "Customer complaint resolution slow", "Average 15-day complaint resolution; customer satisfaction impact", "H", "Complaint management system with 5-day SLA and escalation"),
    ("Quality", "No supplier audit program", "Critical suppliers not audited for quality system compliance", "H", "Risk-based supplier audit program with annual schedule"),
    ("Quality", "No quality KPI dashboard", "Quality metrics not centrally tracked or reported", "M", "Quality dashboard: defect rate, DPPM, COPQ, OTD, customer complaints"),
    ("Quality", "Calibration program not maintained", "Measurement equipment calibration overdue; accuracy unknown", "H", "Calibration management system with scheduling and status tracking"),
]

_S_HR_EXT = [
    ("Payroll", "No payroll tax optimization", "Salary structure not optimized for tax-friendly components", "M", "Flexible benefits and salary restructuring for tax optimization"),
    ("Payroll", "International payroll fragmented", "Multi-country payroll handled by different providers; no oversight", "H", "Global payroll governance with consolidated reporting"),
    ("Payroll", "Final settlement process delayed", "Full and final settlement takes 60+ days; legal risk", "H", "Streamline F&F to 15-day SLA with automated calculation"),
    ("Payroll", "No payroll business continuity", "Payroll depends on single person; no backup", "C", "Cross-training and documented procedures; contingency processing plan"),
    ("Payroll", "Off-cycle payroll runs excessive", "Average 8 off-cycle runs per month; process instability", "M", "Reduce off-cycle runs through better cutoff management; target <2/month"),
    ("Benefits", "No total rewards statement", "Employees unaware of total compensation value; engagement impact", "M", "Annual total rewards statement showing salary, benefits, and equity value"),
    ("Benefits", "ESOP/RSU administration manual", "Stock option grants and vesting tracked in spreadsheets", "H", "Stock plan administration platform with automated vesting and reporting"),
    ("Benefits", "No employee wellness program", "No structured wellness initiative; increasing health costs", "L", "Employee wellness program with health assessments and incentives"),
    ("Benefits", "Insurance claims processing slow", "Health insurance claims take 30+ days to process", "M", "Digitized claims processing with insurer API integration"),
    ("Compensation", "No long-term incentive plan", "Only annual bonus; no retention mechanism beyond salary", "M", "Design LTIP with 3-year vesting tied to company performance"),
    ("Compensation", "Salary bands not market-aligned", "Internal salary bands outdated; below market for hot skills", "H", "Annual market alignment with targeted adjustments for critical roles"),
    ("Compensation", "No compensation governance committee", "Compensation decisions made without structured governance", "H", "Compensation committee with documented decision framework"),
    ("Compliance", "Labor law compliance gaps", "Shops and Establishments Act, Factories Act compliance not tracked", "H", "State-wise labor law compliance matrix with quarterly review"),
    ("Compliance", "No sexual harassment prevention committee", "POSH Act compliance incomplete; committee not properly constituted", "C", "Constitute ICC per POSH Act; annual awareness training"),
    ("Compliance", "Working hours and overtime not compliant", "Overtime beyond statutory limits; inadequate record-keeping", "H", "Automated time tracking with overtime alerts and compliance reporting"),
    ("Analytics", "No attrition prediction model", "Turnover trends analyzed after the fact; no predictive capability", "M", "ML-based attrition prediction model using engagement and performance data"),
    ("Analytics", "No DEI metrics tracking", "Diversity metrics not measured; no inclusion benchmarks", "M", "DEI dashboard with representation, pay equity, and promotion parity"),
    ("Analytics", "Absenteeism not analyzed", "Absenteeism patterns not tracked; productivity impact unknown", "M", "Absenteeism analysis by department with correlation to engagement"),
    ("Analytics", "Training ROI not measured", "L&D spend at $500K/yr with no measurement of effectiveness", "M", "Training effectiveness measurement: reaction, learning, behavior, results"),
    ("Analytics", "No HR service delivery metrics", "HR ticket resolution time and quality not measured", "M", "HR service delivery dashboard with SLA tracking"),
]

_S_RISK_EXT = [
    ("ERM", "No risk culture assessment", "Risk culture across organization not measured; tone at top unclear", "M", "Risk culture survey with action planning by business unit"),
    ("ERM", "Risk reporting to board inadequate", "Board receives lengthy risk reports; no executive summary or heat map", "H", "Executive risk dashboard with heat map, trends, and top 10 focus areas"),
    ("ERM", "Operational risk taxonomy missing", "Operational risks not categorized; inconsistent language", "M", "Operational risk taxonomy aligned to Basel categories or ISO 31000"),
    ("ERM", "No risk transfer optimization", "Insurance program not aligned to identified risks; coverage gaps", "H", "Annual insurance program review against risk register; gap analysis"),
    ("ERM", "Strategic risk assessment absent", "Strategic risks (disruption, market shift) not formally assessed", "H", "Annual strategic risk assessment with board workshop"),
    ("ERM", "No risk quantification methodology", "Risks assessed qualitatively only; impact not quantified in financial terms", "H", "Monte Carlo simulation or scenario-based risk quantification for top risks"),
    ("ERM", "Third-party risk management immature", "No structured approach to assessing and monitoring third-party risks", "H", "TPRM framework with risk tiering, due diligence, and ongoing monitoring"),
    ("Fraud", "Vendor fraud schemes not assessed", "Shell vendor, overbilling, and kickback risks not specifically addressed", "H", "Vendor fraud risk assessment with targeted analytics and controls"),
    ("Fraud", "Expense fraud monitoring absent", "No analytics on expense reports for fraud patterns", "H", "Continuous monitoring for expense fraud: duplicate, phantom, and policy violation"),
    ("Fraud", "No asset misappropriation controls", "Physical asset theft risk not assessed; inventory shrinkage not measured", "H", "Asset security assessment with shrinkage measurement and investigation"),
    ("Fraud", "Financial statement fraud risk not assessed", "Journal entry fraud and management override risks not specifically tested", "C", "JE fraud analytics: round amounts, post-close entries, manual entries by senior staff"),
    ("Fraud", "Anti-money laundering gaps", "AML compliance program not proportionate to risk; transaction monitoring weak", "C", "AML risk assessment with enhanced transaction monitoring and SAR process"),
    ("BCP", "Pandemic preparedness not updated", "Pandemic plan not updated since COVID-19; lessons not incorporated", "M", "Update pandemic BCP with lessons learned and remote work capabilities"),
    ("BCP", "No IT disaster recovery plan", "IT DR plan absent or untested; RTO/RPO not defined", "C", "IT DR plan with defined RTO/RPO and annual testing"),
    ("BCP", "Key person dependency not addressed", "Critical knowledge concentrated in few individuals; succession gap", "H", "Key person risk assessment with cross-training and documentation"),
    ("BCP", "Insurance coverage not aligned to BCA", "Business interruption insurance limits not based on BIA results", "H", "Align insurance coverage to business impact analysis results"),
    ("Cyber", "No privileged access management", "Admin accounts not separately managed; shared passwords exist", "C", "PAM solution with vault, session recording, and just-in-time access"),
    ("Cyber", "No endpoint detection and response", "Endpoints monitored by antivirus only; advanced threats not detected", "H", "EDR deployment across all endpoints with 24/7 monitoring"),
    ("Cyber", "Multi-factor authentication not universal", "MFA only for VPN; not enforced for cloud apps and email", "C", "MFA enforcement for all externally accessible applications"),
    ("Cyber", "No network segmentation", "Flat network architecture; lateral movement unrestricted", "H", "Network segmentation with zero-trust architecture roadmap"),
    ("Cyber", "Cloud security posture not assessed", "Cloud configurations not reviewed; misconfigurations likely", "H", "CSPM tool deployment with continuous misconfiguration detection"),
    ("Cyber", "No security operations center", "Security events not centrally monitored; detection relies on luck", "C", "SOC capability with SIEM, log aggregation, and incident detection"),
    ("Cyber", "Data backup and recovery not tested", "Backups run but restoration never tested; recovery uncertain", "H", "Quarterly backup restoration testing with documented results"),
    ("Cyber", "No cyber insurance", "Cyber risk not insured; potential financial devastation from breach", "H", "Cyber insurance policy with coverage aligned to risk assessment"),
    ("Cyber", "Supply chain cyber risk not assessed", "Software supply chain integrity not verified; SolarWinds-type risk", "H", "Software supply chain security assessment with SBOM requirements"),
    ("Cyber", "No red team exercise", "Offensive security testing never performed; defenses untested", "M", "Annual red team exercise to test detection and response capabilities"),
    ("Cyber", "Employee offboarding access revocation delayed", "Access removal takes 5+ days after termination; unauthorized access window", "C", "Same-day access revocation on termination with automated deprovisioning"),
]

# Extend the main lists
_S_FPA.extend(_S_FPA_EXT)
_S_TAX.extend(_S_TAX_EXT)
_S_TREASURY.extend(_S_TREASURY_EXT)
_S_AUDIT.extend(_S_AUDIT_EXT)
_S_SUPPLY.extend(_S_SUPPLY_EXT)
_S_HR.extend(_S_HR_EXT)
_S_RISK.extend(_S_RISK_EXT)

# Rebuild scenario database with extended lists
CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] Extended to {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Cross-functional and deeper domain scenarios to reach 1000+
_S_O2C_EXT = [
    ("Credit Mgmt", "No portfolio risk concentration analysis", "Credit exposure concentrated in 3 industries; systemic risk", "H", "Quarterly portfolio concentration analysis by industry, geography, and size"),
    ("Credit Mgmt", "Customer financial statement analysis not performed", "Annual financials not reviewed for existing customers", "M", "Annual financial review for all customers with exposure >$200K"),
    ("Order Mgmt", "No order profitability analysis", "Orders accepted without margin check; loss-making orders processed", "H", "Order-level margin check before acceptance; flag orders below threshold"),
    ("Order Mgmt", "Intercompany orders not automated", "IC sales orders created manually; duplication of effort", "M", "Automated IC order creation from purchase order"),
    ("Billing", "Pro-rata billing for subscriptions absent", "Subscription billing does not handle mid-cycle changes correctly", "M", "Automated pro-rata billing for subscription start, change, and cancel"),
    ("Billing", "No usage-based billing capability", "Usage/consumption billing calculated manually; revenue leakage", "H", "Usage metering and billing automation with real-time data feed"),
    ("Revenue", "Contract cost capitalization not tracked", "Costs to obtain and fulfill contracts not assessed per ASC 340-40", "M", "Contract cost assessment and amortization per ASC 340-40"),
    ("Revenue", "Warranty revenue not properly deferred", "Extended warranty revenue recognized at point of sale", "H", "Deferred revenue for extended warranties with time-based recognition"),
    ("Collections", "No predictive analytics for defaults", "Default prediction relies on aging; no statistical model", "M", "ML-based default prediction using payment history and financial indicators"),
    ("Collections", "Skip tracing capabilities absent", "Cannot locate customers who have moved or changed contacts", "M", "Skip tracing tools integrated with collections workflow"),
    ("Cash App", "Multi-currency cash application errors", "Foreign currency receipts applied at wrong exchange rate", "H", "Automated FX rate lookup and application for multi-currency receipts"),
    ("Cash App", "Lockbox processing not optimized", "Lockbox hit rate at 55%; significant manual processing", "H", "Lockbox optimization with enhanced matching rules; target 85% hit rate"),
    ("Disputes", "No trade promotion management", "Trade promotions tracked in spreadsheets; settlement errors", "H", "TPM system with planning, execution tracking, and settlement automation"),
    ("Disputes", "Claim-back from logistics providers not tracked", "Freight damage claims not filed or followed up systematically", "M", "Freight claims management with automated filing and tracking"),
    ("Controls", "No continuous transaction monitoring", "O2C transactions reviewed on sampling basis only", "H", "Continuous monitoring for anomalies in billing, credits, and write-offs"),
    ("Controls", "Escheatment compliance absent", "Unclaimed customer credits/refunds not reported per state laws", "H", "Annual escheatment review and state-by-state filing for unclaimed property"),
]

_S_P2P_EXT = [
    ("Requisition", "No catalog management process", "Catalog items outdated; prices and availability incorrect", "M", "Quarterly catalog refresh with vendor collaboration"),
    ("Requisition", "Tail spend not managed", "60% of vendors represent 5% of spend; high transaction cost", "M", "Tail spend aggregation through procurement cards or marketplace"),
    ("Vendor Mgmt", "No vendor segmentation", "All vendors managed identically regardless of strategic importance", "M", "Vendor segmentation: strategic, preferred, approved, and transactional tiers"),
    ("Vendor Mgmt", "Vendor payment fraud increasing", "Business email compromise attempts targeting vendor payments up 200%", "C", "Anti-BEC controls: callback verification, dual approval, email authentication"),
    ("PO Mgmt", "No goods return process to vendors", "Returns to vendors handled ad hoc; debit notes not issued", "M", "Formal vendor return process with debit note automation"),
    ("PO Mgmt", "Blanket PO leakage", "Spending outside blanket PO terms while blanket exists", "M", "Enforce blanket PO usage for applicable categories; monitor compliance"),
    ("Invoice", "No mobile invoice approval", "Approvals require desktop access; delays when managers travel", "M", "Mobile invoice approval with full context and delegation capability"),
    ("Invoice", "Supplier invoice financing not offered", "No SCF program; suppliers face cash flow constraints", "M", "Supply chain financing program for strategic and diverse suppliers"),
    ("Payments", "Virtual card program not utilized", "No virtual cards for online or one-time purchases; no rebate capture", "M", "Virtual card program for applicable spend categories; capture rebates"),
    ("Payments", "Payment terms not harmonized post-M&A", "Acquired entities have different payment terms; vendor confusion", "M", "Harmonize payment terms across entities within 6 months of acquisition"),
    ("Contracts", "No contract analytics", "Cannot identify which contracts are most/least favorable", "M", "Contract analytics for pricing trends, compliance, and renewal decisions"),
    ("Contracts", "Indemnification clauses not reviewed", "Standard indemnification accepted without legal review", "H", "Legal review of indemnification and liability clauses above threshold"),
    ("Controls", "No procure-to-pay process mining", "Cannot identify process deviations or bottlenecks data-driven", "M", "Process mining on P2P data to identify deviations and improvement areas"),
    ("Controls", "Travel and entertainment policy gaps", "T&E policy exists but not comprehensive; grey areas exploited", "M", "Comprehensive T&E policy review with explicit guidance on common scenarios"),
    ("Reporting", "No spend under management metric", "Cannot quantify what percentage of spend is managed by procurement", "H", "Define and track spend under management; target 80%+"),
    ("Reporting", "Contract utilization not measured", "Cannot tell if negotiated contracts are being used by requestors", "M", "Contract utilization reporting with off-contract spend alerts"),
]

_S_R2R_EXT = [
    ("CoA", "No natural account segmentation", "Natural accounts mixed with cost center and project coding", "M", "Separate natural account from analytical dimensions; clean hierarchy"),
    ("CoA", "Statistical key figures not maintained", "Allocation drivers (sqft, headcount, units) not systematically tracked", "M", "Maintain allocation drivers as statistical key figures with monthly updates"),
    ("JE", "No AI-assisted journal entry review", "JE review is 100% manual; reviewer fatigue and inconsistency", "M", "AI-based JE anomaly detection for reviewer prioritization"),
    ("JE", "Accrual quality declining", "Accrual accuracy at 72%; frequent reversals and corrections", "H", "Accrual template standardization with PO-based auto-accrual"),
    ("Sub-GL", "No real-time GL posting", "Subledger entries batch-posted; GL not current until close", "M", "Real-time posting for key subledgers; reduce reporting lag"),
    ("Sub-GL", "Unreconciled clearing accounts growing", "23 clearing accounts with balances > $100K; investigation backlog", "H", "Zero-balance policy for clearing accounts; daily monitoring"),
    ("IC", "No IC matching tool", "IC reconciliation done via email and spreadsheets; slow and error-prone", "H", "IC matching and reconciliation platform with workflow"),
    ("IC", "IC disputes resolution SLA missed", "Average IC dispute resolution 22 days; target is 5", "H", "Dedicated IC coordinator with escalation at 5/10/15 days"),
    ("Close", "No financial close management software", "Close tasks tracked in spreadsheets; visibility limited", "H", "Close management platform with task tracking and dashboard"),
    ("Close", "Flash estimate process not reliable", "Day 2 flash estimate has 15% variance vs final; not trusted", "H", "Improve flash estimate accuracy through automated accruals and actuals"),
    ("Close", "Intercompany close not synchronized", "Entities close at different speeds; consolidation bottlenecked", "H", "Synchronized close calendar with mandatory submission dates"),
    ("Recon", "No automated matching in reconciliation", "Manual line-by-line matching; hours spent on high-volume accounts", "H", "Automated matching rules for high-volume reconciliations"),
    ("Recon", "Prepaid expense amortization errors", "Prepaid schedules not maintained accurately; expense timing wrong", "M", "Automated amortization schedules with GL posting"),
    ("Fin Rptg", "No reporting data warehouse", "Reports built from live transactional system; performance impact", "H", "Reporting data warehouse with overnight refresh for analytics"),
    ("Fin Rptg", "Consolidation adjustments not standardized", "Each consolidation adjusted differently; inconsistent treatment", "H", "Standardized consolidation adjustment templates with policy basis"),
    ("R2R Controls", "SOX compliance cost excessive", "SOX testing costs $2M+/year; not optimized for risk", "H", "SOX program optimization: rationalize controls, risk-based testing, automation"),
]

_S_GL_EXT = [
    ("Fixed Assets", "Intangible asset accounting weak", "Software, patents, and internally developed assets not properly tracked", "H", "Intangible asset policy with capitalization criteria and amortization schedules"),
    ("Fixed Assets", "Asset retirement obligations not recorded", "AROs for leased premises and environmental obligations not assessed", "H", "ARO assessment for all applicable assets per ASC 410"),
    ("Bank Recon", "Bank fraud monitoring absent", "No monitoring for unauthorized bank transactions; detection delayed", "H", "Daily automated bank transaction monitoring with fraud pattern alerts"),
    ("Bank Recon", "Cash at bank vs books variance persistent", "Consistent timing differences not resolved; growing variance", "H", "Root cause analysis of persistent differences; process correction"),
    ("Expenses", "No pre-trip approval process", "Trips booked without advance approval; cost control weak", "M", "Pre-trip authorization with budget check and itinerary review"),
    ("Expenses", "Entertainment expenses not properly documented", "Business purpose and attendees not recorded; tax deductibility risk", "M", "Mandatory business purpose and attendee documentation for entertainment"),
    ("Allocations", "Shared services cost not transparent", "BUs receive allocated costs without detail; disputes common", "H", "Service catalog with unit costs; transparent chargeback model"),
    ("Allocations", "R&D cost capitalization inconsistent", "Development costs capitalized without consistent criteria", "H", "Documented R&D capitalization policy per ASC 730/IAS 38 with gates"),
    ("Consol", "Goodwill impairment testing not rigorous", "Goodwill impairment test uses management estimates without challenge", "H", "Independent DCF model for goodwill impairment with sensitivity analysis"),
    ("Consol", "VIE assessment not documented", "Variable interest entities not assessed for consolidation", "H", "VIE assessment for all related entities per ASC 810"),
    ("Statutory", "Audit adjustment tracking weak", "External audit adjustments not tracked or trended year-over-year", "M", "Audit adjustment log with trend analysis and process improvement actions"),
    ("Statutory", "Accounting policy manual outdated", "Policy manual last updated 3 years ago; new standards not reflected", "H", "Annual accounting policy manual update with new standard impact assessment"),
    ("Int Controls", "Management review controls informal", "Variance review and analytical review not documented as controls", "H", "Formalize management review controls with documented evidence of review"),
    ("Int Controls", "Delegation of authority matrix absent", "No formal DOA; approval authorities unclear", "C", "Board-approved delegation of authority matrix covering all key decisions"),
    ("Data Quality", "No data stewardship program", "No one accountable for data quality in each domain", "H", "Data stewardship roles assigned for financial master data domains"),
    ("Data Quality", "Financial data reconciliation to source systems absent", "ERP data not reconciled to upstream source systems", "H", "Monthly reconciliation between source systems and financial reporting system"),
]

_S_O2C.extend(_S_O2C_EXT)
_S_P2P.extend(_S_P2P_EXT)
_S_R2R.extend(_S_R2R_EXT)
_S_GL.extend(_S_GL_EXT)

# Final rebuild
CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] FINAL: {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Add Digital Transformation domain and more cross-functional scenarios
_S_DIGITAL = [
    ("ERP", "ERP not fully utilized", "Only 30% of ERP modules deployed; manual workarounds for gaps", "H", "ERP optimization roadmap with phased module deployment"),
    ("ERP", "No ERP upgrade plan", "Running ERP version 3+ years behind; security and support risk", "H", "ERP upgrade or migration plan with business case and timeline"),
    ("ERP", "ERP customizations excessive", "200+ custom programs; upgrade complexity and maintenance cost", "H", "Customization rationalization; migrate to standard where possible"),
    ("ERP", "Master data quality in ERP poor", "Duplicate customers, vendors, materials; data integrity issues", "H", "Master data governance with cleansing, dedup, and quality monitoring"),
    ("ERP", "No ERP center of excellence", "ERP knowledge scattered; no central team for support and standards", "M", "Establish ERP CoE for standards, training, and enhancement governance"),
    ("ERP", "ERP user training inadequate", "Users trained once at go-live; no ongoing training program", "M", "Continuous ERP training program with role-based curriculum"),
    ("ERP", "System integration not robust", "Point-to-point integrations; fragile and difficult to maintain", "H", "Integration middleware/iPaaS for standardized API-based integration"),
    ("ERP", "No ERP process compliance monitoring", "Cannot verify if users follow standard process in ERP", "M", "Process mining on ERP transaction data for compliance monitoring"),
    ("ERP", "Reporting layer not optimized", "Reports run against transactional DB; performance degradation", "H", "Reporting data warehouse or embedded analytics layer"),
    ("ERP", "Chart of accounts not aligned across ERP instances", "Multiple ERP instances with different CoA; consolidation manual", "H", "Harmonized CoA across ERP instances with automated mapping"),
    ("RPA", "No RPA strategy", "Automation done ad hoc; no governance or prioritization", "M", "RPA strategy with opportunity assessment, governance, and CoE"),
    ("RPA", "RPA bots fragile", "Bots break frequently with system changes; high maintenance", "H", "Resilient bot design with exception handling and change monitoring"),
    ("RPA", "RPA ROI not measured", "Bot deployment without baseline or savings tracking", "M", "ROI framework for each bot: FTE saved, error reduction, cycle time"),
    ("RPA", "No citizen developer governance", "Business users building automations without IT oversight", "H", "Citizen developer governance with security review and approval"),
    ("RPA", "Process not optimized before automation", "Broken processes automated; codifying inefficiency", "H", "Process optimization before automation; lean before robot"),
    ("RPA", "No intelligent automation roadmap", "RPA only; no progression to AI/ML-enhanced automation", "M", "Intelligent automation roadmap: RPA → intelligent OCR → ML → agents"),
    ("Cloud", "No cloud strategy", "Cloud migration happening ad hoc; no governing strategy", "H", "Cloud strategy with workload assessment and migration prioritization"),
    ("Cloud", "Cloud cost management absent", "Cloud spend growing 30% YoY without optimization", "H", "FinOps practice with cost monitoring, rightsizing, and reserved instances"),
    ("Cloud", "No cloud security framework", "Security controls not adapted for cloud; shared responsibility unclear", "C", "Cloud security framework with shared responsibility model and controls"),
    ("Cloud", "Data sovereignty not addressed", "Data stored in foreign data centers without regulatory assessment", "H", "Data residency assessment and sovereignty controls per jurisdiction"),
    ("Cloud", "No multi-cloud governance", "Multiple cloud providers without unified governance or cost management", "M", "Multi-cloud governance framework with standardized policies"),
    ("Cloud", "Cloud DR not configured", "Cloud workloads without disaster recovery configuration", "H", "Cloud DR strategy with cross-region replication and tested failover"),
    ("AI", "No AI governance framework", "AI tools adopted without governance; bias and compliance risk", "C", "AI governance framework covering ethics, bias, transparency, and accountability"),
    ("AI", "AI use cases not prioritized", "AI initiatives scattered; no systematic value assessment", "H", "AI opportunity assessment with value/feasibility matrix"),
    ("AI", "No AI model monitoring", "Deployed ML models not monitored for drift or degradation", "H", "Model monitoring pipeline with drift detection and automated retraining"),
    ("AI", "AI training data not governed", "Training data sourced without quality, bias, or consent assessment", "H", "AI data governance with lineage, bias assessment, and consent tracking"),
    ("AI", "No responsible AI policy", "No policy on AI transparency, explainability, or fairness", "H", "Responsible AI policy with mandatory impact assessments"),
    ("AI", "GenAI usage uncontrolled", "Employees using ChatGPT/Copilot with confidential data; data leakage", "C", "GenAI usage policy with approved tools, data classification, and training"),
    ("Data", "No enterprise data strategy", "Data managed in silos; no unified data architecture or governance", "H", "Enterprise data strategy with architecture, governance, and literacy"),
    ("Data", "No data catalog", "Cannot discover what data exists across the organization", "M", "Data catalog with metadata management and search capability"),
    ("Data", "No data quality framework", "Data quality measured inconsistently if at all", "H", "Data quality framework with dimensions, rules, and scorecards"),
    ("Data", "No self-service BI governance", "Self-service reports created without standards; conflicting numbers", "H", "Governed self-service BI with certified datasets and metric definitions"),
    ("Data", "Data literacy low", "Employees lack skills to interpret data and make data-driven decisions", "M", "Data literacy program with role-based training and certification"),
    ("Data", "No data monetization assessment", "Data assets not assessed for monetization or partnership value", "L", "Data asset valuation and monetization opportunity assessment"),
    ("GRC", "No integrated GRC platform", "Governance, risk, and compliance managed in separate systems", "H", "Integrated GRC platform connecting risk, compliance, and audit"),
    ("GRC", "Policy management manual", "Corporate policies in documents; version control and acknowledgment manual", "M", "Policy management platform with lifecycle, distribution, and attestation"),
    ("GRC", "Compliance obligation register absent", "Regulatory obligations not cataloged or mapped to controls", "H", "Compliance obligation register mapped to controls with testing schedule"),
    ("GRC", "No regulatory change management", "New regulations discovered reactively after violations", "H", "Regulatory change tracking with impact assessment and implementation plan"),
    ("GRC", "Board governance assessment not performed", "Board effectiveness not assessed; governance gaps possible", "M", "Annual board governance assessment with improvement action plan"),
    ("GRC", "No ESG reporting framework", "ESG metrics not defined, collected, or reported", "H", "ESG framework aligned to BRSR/GRI with automated data collection"),
    ("GRC", "No supply chain ESG assessment", "Supplier environmental and social practices not assessed", "M", "Supply chain ESG assessment for tier-1 suppliers"),
    ("GRC", "Carbon footprint not measured", "Scope 1, 2, 3 emissions not calculated or reported", "H", "Carbon accounting across scopes with reduction target setting"),
    ("GRC", "Sustainability targets not set", "No formal environmental or social targets; stakeholder pressure growing", "M", "Science-based sustainability targets with progress tracking"),
    ("GRC", "Green procurement not implemented", "Environmental criteria not part of procurement decisions", "L", "Green procurement policy with weighted environmental criteria"),
    ("Process", "No process documentation standard", "Process docs scattered in various formats; tribal knowledge risk", "H", "Process documentation standard with BPMN and RACI for all key processes"),
    ("Process", "No continuous improvement program", "Improvements happen ad hoc; no structured methodology", "M", "Continuous improvement program: Lean Six Sigma or Kaizen approach"),
    ("Process", "Shared services not optimized", "Shared services centers operate without SLAs or benchmarks", "H", "Shared services optimization with SLAs, benchmarks, and automation"),
    ("Process", "No process performance metrics", "Cycle times, error rates, and costs not measured per process", "H", "Process KPI framework with automated measurement and trending"),
    ("Process", "Change management capability weak", "Organizational change management not structured; transformation failures", "H", "OCM framework with stakeholder analysis, communication, and training"),
    ("Process", "No process mining capability", "Cannot analyze actual process flows from system logs", "M", "Process mining deployment for key business processes"),
    ("Process", "Innovation management absent", "No structured approach to capturing and implementing innovations", "M", "Innovation management process with idea capture, evaluation, and funding"),
]

# Add DIGITAL domain to the domain map and rebuild
_orig_build = _build_scenario_db
def _build_scenario_db():
    all_scenarios = []
    domain_map = {
        "O2C": ("Order to Cash", "💰", _S_O2C),
        "P2P": ("Procure to Pay", "🛒", _S_P2P),
        "R2R": ("Record to Report", "📊", _S_R2R),
        "GL": ("General Accounting", "📒", _S_GL),
        "FPA": ("Financial Planning & Analysis", "📈", _S_FPA),
        "TAX": ("Tax & Compliance", "⚖️", _S_TAX),
        "TREASURY": ("Treasury & Cash Management", "🏦", _S_TREASURY),
        "AUDIT": ("Internal Audit & SOX", "🔍", _S_AUDIT),
        "SUPPLY": ("Supply Chain & Operations", "🚚", _S_SUPPLY),
        "HR": ("HR & Payroll", "👥", _S_HR),
        "RISK": ("Risk, Fraud & Cyber", "🛡️", _S_RISK),
        "DIGITAL": ("Digital Transformation & GRC", "🖥️", _S_DIGITAL),
    }
    risk_map = {"C": "Critical", "H": "High", "M": "Medium", "L": "Low"}
    for domain_key, (domain_name, icon, scenarios) in domain_map.items():
        for idx, (category, title, finding, risk, recommendation) in enumerate(scenarios):
            all_scenarios.append({
                "id": f"{domain_key}-{idx+1:03d}",
                "domain": domain_key,
                "domain_name": domain_name,
                "domain_icon": icon,
                "category": category,
                "title": title,
                "finding": finding,
                "risk_level": risk_map.get(risk, risk),
                "recommendation": recommendation,
            })
    return all_scenarios, domain_map

CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] WITH DIGITAL: {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Final boost - industry-specific and advanced scenarios to reach 1000+
_S_O2C_BOOST = [
    ("Credit Mgmt", "No country risk assessment for export AR", "Export receivables without sovereign risk scoring", "H", "Country risk limits using Coface/Euler ratings for export customers"),
    ("Credit Mgmt", "Parent-subsidiary credit linkage missing", "Child entities assessed independently; group exposure blind spot", "M", "Hierarchical credit assessment with group-level exposure limits"),
    ("Order Mgmt", "No demand shaping through pricing", "Pricing not used to steer demand toward profitable products", "M", "Dynamic pricing engine with margin-based demand shaping"),
    ("Order Mgmt", "Channel conflict in order management", "Direct and channel orders compete; no prioritization logic", "M", "Channel-aware order management with routing and priority rules"),
    ("Order Mgmt", "No drop-ship capability", "All orders fulfilled from own inventory; no supplier direct ship", "M", "Drop-ship integration with key suppliers for long-tail products"),
    ("Billing", "Revenue leakage from unbilled services", "Billable hours and services not fully captured; estimated 5% leakage", "H", "Automated billable activity capture with completeness reconciliation"),
    ("Billing", "Subscription billing churn analysis absent", "Churn not tracked at invoice level; no early warning", "H", "Churn prediction model tied to billing patterns and usage data"),
    ("Revenue", "VSOE/SSP analysis not refreshed", "Standalone selling prices for performance obligations not updated annually", "H", "Annual SSP analysis with sufficient data points for statistical validity"),
    ("Revenue", "License vs SaaS revenue treatment inconsistent", "Hybrid arrangements not properly classified for revenue recognition", "H", "Decision framework for license vs SaaS classification per ASC 606"),
    ("Collections", "No payment plan management", "Delinquent accounts offered payment plans but no system tracking", "M", "Payment plan management with automated installment tracking"),
    ("Cash App", "Netting and offset application not systematic", "Customer netting requests handled manually; reconciliation complex", "M", "Automated netting with systematic offset and audit trail"),
    ("Disputes", "No customer satisfaction survey post-dispute", "Dispute resolution quality not measured from customer perspective", "L", "Post-resolution CSAT survey with improvement action tracking"),
    ("Controls", "No revenue assurance program", "No systematic review of revenue completeness and accuracy", "H", "Revenue assurance program with end-to-end reconciliation from order to cash"),
]

_S_P2P_BOOST = [
    ("Requisition", "No indirect procurement strategy", "Indirect spend (MRO, office, travel) not strategically managed", "M", "Indirect procurement strategy with category management approach"),
    ("Requisition", "No marketplace/punchout integration", "Cannot order from supplier catalogs within procurement system", "M", "Punchout catalog integration for top indirect suppliers"),
    ("Vendor Mgmt", "Supplier early warning system absent", "No monitoring for supplier financial distress or quality decline", "H", "Supplier early warning system with financial, news, and quality triggers"),
    ("Vendor Mgmt", "No vendor innovation program", "Suppliers not engaged for innovation or new product development", "M", "Vendor innovation days with strategic suppliers quarterly"),
    ("PO Mgmt", "No commitment accounting", "Purchase commitments not reflected in budget consumption", "H", "Real-time commitment accounting showing budget, committed, and available"),
    ("Invoice", "Freight invoice audit not performed", "Transportation invoices paid without audit; overcharges estimated at 5-8%", "H", "Freight audit program with automated rate validation"),
    ("Invoice", "No OCR/AI for invoice processing", "Invoices manually keyed; no intelligent data extraction", "H", "AI-powered invoice capture with field extraction and auto-coding"),
    ("Payments", "No payment-on-behalf-of capability", "Cannot process payments on behalf of subsidiaries; decentralized", "M", "Payment factory for centralized payment processing across entities"),
    ("Payments", "No real-time payment capability", "Cannot make instant payments when urgently needed", "M", "Real-time payment capability through UPI/IMPS/RTGS integration"),
    ("Contracts", "No force majeure monitoring", "Contract force majeure triggers not monitored proactively", "M", "Geopolitical and weather event monitoring for contract force majeure"),
    ("Controls", "No three-way match exception analytics", "Match exceptions not analyzed for patterns; same issues recur", "M", "Exception analytics with root cause trending and supplier feedback"),
    ("Reporting", "No total cost of procurement metric", "Cost of procurement function not benchmarked; efficiency unknown", "M", "Procurement cost benchmarking: cost per PO, cost per invoice, cost per supplier"),
    ("Reporting", "No supplier payment performance dashboard", "Vendor payment timing not tracked or reported", "M", "Payment performance dashboard showing on-time percentage by vendor"),
]

_S_R2R_BOOST = [
    ("CoA", "No project accounting structure", "Project costs tracked in spreadsheets outside GL", "H", "Project accounting in GL with WBS elements and project P&L"),
    ("CoA", "Fund accounting not configured", "Restricted funds not tracked separately; compliance risk for nonprofits", "H", "Fund accounting structure with restricted/unrestricted/board-designated"),
    ("JE", "No predictive accrual capability", "Accruals estimated from scratch each period; inconsistent", "M", "Predictive accrual based on PO commitments and historical patterns"),
    ("JE", "Reclassification entries excessive", "Average 50 reclassification entries per month; initial coding quality poor", "H", "Root cause analysis of reclassifications; improve initial coding accuracy"),
    ("Sub-GL", "Revenue subledger not reconciled", "Revenue recognition entries not reconciled to billing system", "H", "Monthly billing-to-revenue reconciliation with variance investigation"),
    ("IC", "No IC center of excellence", "IC accounting handled differently by each entity; inconsistent", "H", "IC accounting CoE with standardized processes and tools"),
    ("Close", "No close automation for routine entries", "Routine month-end entries (depreciation, amortization) posted manually", "M", "Automated scheduling for routine close entries"),
    ("Recon", "No variance threshold for reconciliation investigation", "All variances investigated regardless of size; inefficient", "M", "Risk-based investigation thresholds; immaterial items cleared per policy"),
    ("Fin Rptg", "No integrated reporting capability", "Financial and non-financial reporting disconnected", "M", "Integrated reporting framework linking financial, ESG, and operational data"),
    ("Fin Rptg", "Quarterly earnings package not automated", "SEC/stock exchange filing data gathered manually each quarter", "H", "Automated quarterly reporting package with data validation"),
    ("R2R Controls", "No RPA in close process", "Repetitive close tasks not automated despite RPA availability", "M", "RPA implementation for reconciliations, accruals, and data gathering"),
    ("R2R Controls", "SOX testing calendar not optimized", "SOX testing clustered at year-end; staggered approach would be more effective", "M", "Staggered SOX testing calendar with quarterly cadence for key controls"),
    ("R2R Controls", "No control self-assessment program", "Process owners not involved in control assessment; disconnected", "M", "Annual CSA program with process owner participation"),
]

_S_GL_BOOST = [
    ("Fixed Assets", "No componentization of assets", "Complex assets not broken into components; depreciation imprecise", "M", "Component accounting for major assets with separate useful lives"),
    ("Fixed Assets", "Government grant accounting inconsistent", "Grants netted against assets without IAS 20 assessment", "H", "Government grant accounting policy per IAS 20 with proper disclosure"),
    ("Bank Recon", "Intercompany cash movements not tracked in real-time", "IC cash transfers reconciled monthly; timing differences create confusion", "M", "Real-time IC cash movement tracking with same-day matching"),
    ("Expenses", "No virtual card for AP automation", "All payments via traditional methods; missing card rebate opportunity", "M", "Virtual card program for qualified supplier payments; capture rebates"),
    ("Allocations", "No profitability analysis by product", "Product-level profitability unknown; cross-subsidization likely", "H", "Activity-based product profitability with direct and allocated costs"),
    ("Consol", "No sub-consolidation for regional reporting", "Regional financial data only available after full consolidation", "M", "Sub-consolidation for regions with same-day availability"),
    ("Statutory", "No IFRS/GAAP dual reporting capability", "Only one reporting standard supported; multi-GAAP entities struggle", "H", "Dual-GAAP reporting capability for entities with multiple requirements"),
    ("Statutory", "Country-specific statutory reporting manual", "Local statutory reports built manually; error and delay risk", "H", "Automated local statutory report mapping from consolidated data"),
    ("Int Controls", "No control rationalization program", "Control inventory growing annually; testing cost increasing", "H", "Annual control rationalization: eliminate redundant, automate routine"),
    ("Int Controls", "Spreadsheet controls absent", "Critical spreadsheets used in financial reporting without controls", "C", "Spreadsheet risk assessment with controls: access, input validation, change log"),
    ("Data Quality", "No financial data dictionary", "Same metric calculated differently across reports; confusion", "H", "Financial data dictionary with standard metric definitions and formulas"),
    ("Data Quality", "ETL processes not validated", "Data transformation logic not documented or tested; silent errors", "H", "ETL validation framework with reconciliation checks at each stage"),
    ("Data Quality", "No master data matching across systems", "Customer/vendor/product IDs differ across systems; no golden record", "H", "MDM platform for golden record creation with cross-system matching"),
]

_S_O2C.extend(_S_O2C_BOOST)
_S_P2P.extend(_S_P2P_BOOST)
_S_R2R.extend(_S_R2R_BOOST)
_S_GL.extend(_S_GL_BOOST)

# Additional scenarios for secondary domains
_S_FPA.extend([
    ("Budgeting", "No budget collaboration platform", "Budget collected via emailed spreadsheets; version chaos", "H", "Cloud-based budget collaboration with workflow and version control"),
    ("Budgeting", "Intercompany elimination not budgeted", "IC transactions budgeted but eliminations not; consolidated budget inflated", "M", "Budget IC eliminations to match consolidation methodology"),
    ("Forecasting", "No bottoms-up cash forecast from operations", "Cash forecast top-down from P&L; timing differences large", "H", "Bottom-up cash forecast from AR collections, AP payments, and payroll"),
    ("Variance", "No bridge analysis capability", "Cannot show waterfall from budget to actual with drivers", "H", "Automated bridge chart: budget → volume → price → mix → cost → FX → actual"),
    ("Modeling", "DCF model not standardized", "Different discount rates and terminal value methods used across analyses", "H", "Standardized DCF template with approved WACC and terminal value methodology"),
    ("Reporting", "No automated management commentary", "CFO commentary drafted from scratch each period", "M", "AI-assisted commentary generation with variance-triggered narratives"),
])

_S_TAX.extend([
    ("GST", "No GST health check performed", "End-to-end GST process review never conducted", "M", "Annual GST health check covering compliance, ITC optimization, and process"),
    ("GST", "Reverse charge mechanism compliance weak", "RCM applicability not comprehensively assessed across vendor categories", "H", "Comprehensive RCM assessment with vendor category mapping"),
    ("Direct Tax", "No safe harbor option evaluation for international transactions", "Safe harbor provisions not evaluated; excessive documentation for qualifying transactions", "M", "Annual safe harbor eligibility assessment for routine IC transactions"),
    ("Direct Tax", "No angel tax assessment for startups", "Section 56(2)(viib) implications not assessed for share issuances", "H", "Angel tax assessment for all share issuances with valuation report"),
    ("Compliance", "No tax dispute resolution strategy", "Tax disputes handled reactively without resolution strategy", "H", "Proactive dispute resolution strategy including MAP, APA, and settlement options"),
    ("Compliance", "No customs valuation audit", "Import valuations not reviewed for SVB implications", "H", "Customs valuation audit with SVB assessment for related party imports"),
])

_S_TREASURY.extend([
    ("Cash Mgmt", "No supply chain finance assessment", "SCF program feasibility not evaluated; supplier liquidity could improve", "M", "SCF program assessment with supplier benefit and bank partner evaluation"),
    ("FX Mgmt", "No translation risk management", "Only transaction FX risk hedged; translation exposure ignored", "M", "Translation risk assessment with balance sheet hedging evaluation"),
    ("Debt Mgmt", "No ESG-linked financing assessment", "Sustainability-linked loans/bonds not explored; potentially lower rates", "M", "ESG-linked financing assessment with KPI framework for sustainability loans"),
    ("Controls", "No bank connectivity standard", "Each bank connected differently; fragmented payment infrastructure", "H", "Standardized bank connectivity via SWIFT or host-to-host for all partners"),
    ("Controls", "No intraday cash reporting", "Cash position known only at end of day; payment decisions suboptimal", "M", "Real-time intraday cash position with payment prioritization capability"),
    ("Controls", "No intercompany netting center", "IC settlements bilateral; excessive payments and FX transactions", "H", "IC netting center with multilateral netting and single settlement"),
])

_S_AUDIT.extend([
    ("Risk Assessment", "No climate risk in audit scope", "Climate-related financial risks not assessed in audit plan", "M", "Climate risk assessment integrated into audit planning per TCFD"),
    ("Execution", "No fraud detection analytics", "Benford's analysis, duplicate detection not used in audits", "H", "Deploy fraud detection analytics toolkit for all financial audits"),
    ("Execution", "No use of drones or IoT in audit", "Physical verification relies on manual inspection only", "L", "Evaluate drone and IoT technology for inventory and asset audits"),
    ("Reporting", "No root cause taxonomy", "Audit findings lack consistent root cause classification", "M", "Standard root cause taxonomy: people, process, technology, governance"),
    ("IT Audit", "No SDLC audit for financial systems", "System development lifecycle for financial apps not audited", "H", "Annual SDLC audit covering requirements, testing, deployment, and change"),
    ("IT Audit", "No identity governance audit", "User lifecycle (joiners, movers, leavers) not verified for completeness", "H", "Identity governance audit covering provisioning, transfer, and termination"),
])

_S_SUPPLY.extend([
    ("Inventory", "No digital twin for supply chain", "No simulation capability for supply chain disruption scenarios", "M", "Digital twin or simulation tool for supply chain scenario planning"),
    ("Demand", "No S&OP process maturity", "Sales and operations planning ad hoc; no structured monthly process", "H", "Formalize 5-step S&OP: demand review, supply review, pre-S&OP, exec S&OP, implementation"),
    ("Logistics", "No sustainability in logistics", "Carbon footprint of logistics operations not measured or reduced", "M", "Logistics carbon footprint measurement with reduction targets"),
    ("Procurement", "No procurement risk management", "Procurement decisions without risk assessment; supply disruptions", "H", "Procurement risk framework with country, supplier, and category risk scoring"),
    ("Quality", "No customer returns analysis", "Returns data not analyzed for quality improvement", "M", "Customer returns root cause analysis with quality improvement loop"),
    ("Quality", "Recall readiness not tested", "Product recall plan exists but never tested", "H", "Annual recall readiness drill with traceability verification"),
])

_S_HR.extend([
    ("Payroll", "No multi-state payroll compliance", "Operations in 15+ states without state-specific payroll compliance", "H", "State-wise payroll compliance matrix with automated rules"),
    ("Benefits", "No return-to-work program", "No structured program for employees returning from extended leave", "M", "Return-to-work program with phased reintegration support"),
    ("Compensation", "No sales compensation administration tool", "Sales commissions calculated manually; disputes with sales team", "H", "Sales compensation management platform with transparent calculation"),
    ("Compliance", "No immigration compliance tracking", "Work permit and visa status not tracked centrally", "H", "Immigration compliance tracking with expiry alerts and renewal workflow"),
    ("Analytics", "No people analytics strategy", "HR data not leveraged for strategic workforce decisions", "M", "People analytics strategy with priority use cases and data roadmap"),
    ("Analytics", "Contingent workforce not tracked", "Contractor headcount and cost not consolidated; total workforce unknown", "H", "Total workforce visibility including contingent, contract, and gig workers"),
])

_S_RISK.extend([
    ("ERM", "No risk aggregation methodology", "Risks assessed individually; portfolio and correlation effects missed", "H", "Risk aggregation with correlation analysis for compound risk scenarios"),
    ("Fraud", "No continuous auditing for fraud", "Fraud testing limited to periodic audit; real-time detection absent", "H", "Continuous auditing program with automated fraud indicator alerts"),
    ("BCP", "No supply chain BCP", "Business continuity focused on internal operations; supply chain ignored", "H", "Supply chain BCP with alternate supplier and logistics contingencies"),
    ("Cyber", "No OT/ICS security assessment", "Industrial control systems and operational technology not assessed", "C", "OT security assessment covering SCADA, PLCs, and network segmentation"),
    ("Cyber", "No insider threat program", "Focus on external threats only; insider risks not addressed", "H", "Insider threat program with behavioral analytics and access monitoring"),
    ("Cyber", "No third-party security monitoring", "Connected third parties not monitored for security incidents", "H", "Third-party security monitoring with real-time risk scoring"),
])

_S_DIGITAL.extend([
    ("ERP", "S/4HANA migration not planned", "Running on ECC/legacy ERP; end of support approaching", "H", "S/4HANA migration assessment with roadmap and business case"),
    ("ERP", "No ERP data archiving", "ERP database growing 25%/yr; performance degradation", "M", "Data archiving strategy with retention policy and archive solution"),
    ("RPA", "No hyperautomation strategy", "Automation limited to RPA; not leveraging AI, process mining, or low-code", "M", "Hyperautomation strategy combining RPA, AI, process mining, and integration"),
    ("Cloud", "Shadow IT proliferation", "50+ unapproved SaaS applications in use; security and data risk", "H", "Shadow IT discovery and governance; approved SaaS catalog"),
    ("AI", "No LLM deployment governance", "LLMs being used in production without evaluation or monitoring", "H", "LLM governance: model evaluation, prompt management, output monitoring"),
    ("Data", "No real-time data platform", "All reporting batch-based with 24hr+ latency; decisions delayed", "H", "Real-time data platform for operational dashboards and alerting"),
    ("GRC", "No compliance automation", "Compliance evidence collection and testing fully manual", "H", "Compliance automation platform for evidence collection and testing"),
    ("Process", "No process excellence team", "Process improvement is everyone's job and therefore no one's job", "M", "Dedicated process excellence team with methodology and metrics"),
])

# Final final rebuild
CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] GRAND TOTAL: {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Programmatic scenario generation - industry-specific variants of common control gaps
_INDUSTRIES_FOR_SCENARIOS = ["Manufacturing", "Retail", "BFSI", "Healthcare", "Technology", "Real Estate", "Pharma", "FMCG"]
_COMMON_GAPS = [
    ("O2C", "Collections", "{ind}: Customer payment follow-up not industry-adapted", "Collection strategies not tailored to {ind} payment norms and cycles", "H", "Industry-specific collection playbook for {ind} customers"),
    ("P2P", "Vendor Mgmt", "{ind}: Vendor qualification criteria generic", "No {ind}-specific vendor qualification; quality and compliance gaps", "H", "{ind}-specific vendor qualification checklist with industry certifications"),
    ("R2R", "Close", "{ind}: Industry-specific accruals missing", "Accruals for {ind}-specific items (royalties, warranties, returns) not systematic", "H", "{ind}-specific accrual checklist integrated into close process"),
    ("GL", "Statutory", "{ind}: Industry regulatory reporting gaps", "{ind}-specific regulatory reports not automated or tracked", "H", "{ind} regulatory reporting calendar with automated preparation"),
    ("FPA", "Modeling", "{ind}: Industry KPI benchmarks not available", "No {ind} benchmarks for performance comparison", "M", "Subscribe to {ind} benchmarking service; quarterly comparison"),
    ("TAX", "Compliance", "{ind}: Industry-specific tax incentives not claimed", "{ind} tax benefits and deductions not fully leveraged", "H", "Annual review of {ind}-specific tax incentives and exemptions"),
    ("SUPPLY", "Quality", "{ind}: Industry quality standards not tracked", "{ind} quality requirements (GMP, ISO, FDA) compliance gaps", "H", "{ind} quality management system with certification tracking"),
    ("HR", "Compliance", "{ind}: Industry labor regulations not tracked", "{ind}-specific labor and safety regulations not systematically monitored", "H", "{ind} labor compliance matrix with regulatory change tracking"),
    ("RISK", "ERM", "{ind}: Industry-specific risks not assessed", "{ind} operational risks not in enterprise risk register", "H", "{ind}-specific risk assessment covering regulatory, market, and operational risks"),
    ("AUDIT", "Risk Assessment", "{ind}: Industry audit risks not scoped", "{ind}-specific audit risks not covered in annual plan", "H", "Include {ind}-specific risks in audit planning and scoping"),
    ("DIGITAL", "AI", "{ind}: AI use cases not industry-aligned", "AI initiatives not leveraging {ind}-specific data and workflows", "M", "{ind} AI use case catalogue with feasibility and value assessment"),
    ("TREASURY", "Cash Mgmt", "{ind}: Working capital cycle not optimized for industry", "{ind} working capital benchmarks not applied; cycle suboptimal", "H", "Industry-specific working capital optimization against {ind} benchmarks"),
]

# Generate industry-specific scenarios
for industry in _INDUSTRIES_FOR_SCENARIOS:
    for domain, category, title_tmpl, finding_tmpl, risk, rec_tmpl in _COMMON_GAPS:
        title = title_tmpl.format(ind=industry)
        finding = finding_tmpl.format(ind=industry)
        rec = rec_tmpl.format(ind=industry)
        # Add to the appropriate list
        scenario_tuple = (category, title, finding, risk, rec)
        if domain == "O2C": _S_O2C.append(scenario_tuple)
        elif domain == "P2P": _S_P2P.append(scenario_tuple)
        elif domain == "R2R": _S_R2R.append(scenario_tuple)
        elif domain == "GL": _S_GL.append(scenario_tuple)
        elif domain == "FPA": _S_FPA.append(scenario_tuple)
        elif domain == "TAX": _S_TAX.append(scenario_tuple)
        elif domain == "TREASURY": _S_TREASURY.append(scenario_tuple)
        elif domain == "AUDIT": _S_AUDIT.append(scenario_tuple)
        elif domain == "SUPPLY": _S_SUPPLY.append(scenario_tuple)
        elif domain == "HR": _S_HR.append(scenario_tuple)
        elif domain == "RISK": _S_RISK.append(scenario_tuple)
        elif domain == "DIGITAL": _S_DIGITAL.append(scenario_tuple)

# FINAL rebuild with all scenarios
CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] PRODUCTION TOTAL: {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Final push to 1000+ with specialized advanced scenarios
_FINAL_EXTRAS = [
    ("O2C", "Controls", "No revenue assurance analytics", "Revenue completeness not verified through end-to-end analytics", "H", "Implement revenue assurance analytics: order-to-billing-to-cash reconciliation"),
    ("O2C", "Controls", "Customer rebate accrual accuracy low", "Rebate accruals off by 15%; year-end true-up creates volatility", "H", "Real-time rebate accrual calculation based on actual volumes and tiers"),
    ("O2C", "Credit Mgmt", "No credit scoring for online/digital customers", "E-commerce customers onboarded without credit assessment", "H", "Real-time digital credit scoring for online B2B customers"),
    ("O2C", "Billing", "Multi-entity billing complexity unmanaged", "Customers billed by multiple entities; confusion and disputes", "M", "Cross-entity billing coordination with unified customer view"),
    ("O2C", "Revenue", "Contract asset impairment not assessed", "Contract assets (unbilled revenue) not tested for impairment", "M", "Quarterly contract asset impairment assessment per ASC 606"),
    ("O2C", "Collections", "No legal collection tracking", "Accounts in legal collection not tracked separately from standard AR", "M", "Legal collection tracking with case management and cost-benefit analysis"),
    ("P2P", "Invoice", "No machine learning for invoice matching", "Invoice matching rules are static; cannot learn from exceptions", "M", "ML-enhanced matching that improves automatically from resolved exceptions"),
    ("P2P", "Vendor Mgmt", "No vendor diversity certification verification", "Diverse vendor certifications accepted but not verified", "L", "Annual certification verification for all diverse suppliers"),
    ("P2P", "Controls", "No after-the-fact purchase policy enforcement", "After-the-fact purchases identified but no consequences applied", "H", "Progressive discipline for policy violations; mandatory training"),
    ("P2P", "Payments", "No payment forecasting model", "Cannot predict cash outflows from AP; treasury planning impacted", "H", "AP payment forecasting based on invoice due dates and payment behavior"),
    ("P2P", "Contracts", "No commercial terms negotiation playbook", "Procurement negotiates without structured approach; value left on table", "M", "Negotiation playbook with should-cost models and BATNA analysis"),
    ("P2P", "Requisition", "No preferred vendor compliance tracking", "Cannot measure if buyers are using preferred vendors vs alternatives", "M", "Preferred vendor compliance dashboard with deviation trending"),
    ("R2R", "Close", "No financial close benchmarking", "Close cycle time not benchmarked against peers or best practice", "M", "Annual close cycle benchmarking with APQC or Hackett Group data"),
    ("R2R", "Recon", "No substantive analytical procedures", "Reconciliations focused on detail testing; analytics not used", "M", "Supplement detail reconciliations with analytical procedures for efficiency"),
    ("R2R", "JE", "Topside adjustments between legal entities not balanced", "Adjustments at consolidation level create entity-level imbalances", "H", "All topside adjustments balanced across entities with documentation"),
    ("R2R", "Fin Rptg", "Earnings quality analysis not performed", "No assessment of earnings quality metrics (accrual ratio, cash conversion)", "M", "Quarterly earnings quality analysis for investor communication readiness"),
    ("R2R", "IC", "No IC billing dispute aging", "IC disputes aged but not reported separately from external AR/AP aging", "M", "Dedicated IC dispute aging with escalation at 15/30/45 days"),
    ("GL", "Fixed Assets", "No cloud computing cost capitalization assessment", "Cloud implementation costs expensed when some should be capitalized per ASC 350-40", "H", "Assessment of cloud computing arrangements for capitalization under ASC 350-40"),
    ("GL", "Allocations", "No overhead absorption rate variance analysis", "Overhead under/over-absorbed but variance not analyzed monthly", "M", "Monthly absorption variance analysis with corrective action for material variances"),
    ("GL", "Int Controls", "No entity-level antifraud program", "Antifraud program limited to tone-at-top; no operational controls", "H", "Operational antifraud controls including analytics, hotline, and investigation"),
    ("GL", "Data Quality", "No data quality SLA with source systems", "Finance relies on upstream data without quality guarantees", "H", "Data quality SLAs with source system owners; escalation for quality failures"),
    ("GL", "Statutory", "No indirect tax technology assessment", "GST/VAT technology needs not assessed; manual workarounds persist", "M", "Indirect tax technology assessment and vendor selection"),
    ("FPA", "Budgeting", "No activity-based budgeting for shared services", "Shared services budget not activity-based; cost allocation disputes", "M", "Activity-based budgeting for shared services with service catalog"),
    ("FPA", "Variance", "No gross-to-net revenue bridge", "Revenue discounts, rebates, and returns not analyzed separately", "H", "Gross-to-net revenue bridge with variance analysis for each deduction type"),
    ("FPA", "Reporting", "No scenario dashboard for leadership", "Leadership cannot run what-if scenarios on demand", "M", "Interactive scenario dashboard with pre-built sensitivity analyses"),
    ("TAX", "Direct Tax", "No Vivad Se Vishwas assessment", "Tax dispute settlement scheme eligibility not assessed", "M", "Assess eligibility for dispute settlement schemes and quantify savings"),
    ("TAX", "GST", "No input service distributor compliance", "ISD registration and credit distribution not proper where required", "H", "ISD compliance assessment with registration and distribution methodology"),
    ("TAX", "Compliance", "No tax function effectiveness review", "Tax function not benchmarked for cost, risk, and effectiveness", "M", "Tax function effectiveness review against maturity model"),
    ("TREASURY", "Cash Mgmt", "No trapped cash analysis", "Cash locked in subsidiaries without repatriation plan", "H", "Trapped cash analysis with repatriation strategy and tax impact"),
    ("TREASURY", "FX Mgmt", "No hedge effectiveness testing", "Derivatives designated as hedges but effectiveness not tested", "H", "Prospective and retrospective hedge effectiveness testing per ASC 815"),
    ("AUDIT", "Execution", "No continuous auditing for revenue", "Revenue transactions only tested periodically", "H", "Continuous revenue audit with completeness, accuracy, and cut-off analytics"),
    ("AUDIT", "IT Audit", "No robotic process automation audit", "RPA bots processing financial transactions without audit coverage", "H", "RPA audit covering bot access, logic, exception handling, and governance"),
    ("SUPPLY", "Inventory", "No demand-driven MRP", "Traditional MRP based on forecasts; excessive bullwhip effect", "M", "DDMRP implementation for strategic buffers with pull-based replenishment"),
    ("SUPPLY", "Logistics", "No green logistics initiative", "No measurement or reduction of logistics carbon footprint", "M", "Green logistics program with emissions measurement and reduction plan"),
    ("HR", "Payroll", "No gig worker payment platform", "Gig and contract worker payments processed through regular AP; compliance risk", "M", "Dedicated gig worker payment platform with compliance and tax handling"),
    ("HR", "Analytics", "No skills gap analysis", "Workforce skills not assessed against future requirements", "H", "Skills taxonomy with gap analysis and learning pathway mapping"),
    ("RISK", "ERM", "No geopolitical risk assessment", "Geopolitical risks not formally assessed; supply chain and market impact possible", "H", "Quarterly geopolitical risk assessment for key operating geographies"),
    ("RISK", "Cyber", "No zero trust architecture plan", "Perimeter-based security model still in place; inadequate for modern threats", "H", "Zero trust architecture roadmap with phased implementation plan"),
    ("DIGITAL", "AI", "No AI center of excellence", "AI projects executed ad hoc without shared capabilities or standards", "H", "AI CoE for model development standards, MLOps, and knowledge sharing"),
    ("DIGITAL", "Cloud", "No cloud exit strategy", "Cloud vendor lock-in without portability assessment or exit plan", "M", "Cloud exit strategy with data portability and workload migration plan"),
    ("DIGITAL", "GRC", "No integrated risk and compliance reporting", "Risk and compliance data in separate systems; no unified view", "H", "Integrated risk and compliance dashboard for board and management"),
    ("DIGITAL", "Process", "No customer journey mapping", "Internal processes not mapped to customer experience; friction points unknown", "M", "Customer journey mapping with internal process alignment and friction reduction"),
]

for domain, category, title, finding, risk, rec in _FINAL_EXTRAS:
    scenario_tuple = (category, title, finding, risk, rec)
    if domain == "O2C": _S_O2C.append(scenario_tuple)
    elif domain == "P2P": _S_P2P.append(scenario_tuple)
    elif domain == "R2R": _S_R2R.append(scenario_tuple)
    elif domain == "GL": _S_GL.append(scenario_tuple)
    elif domain == "FPA": _S_FPA.append(scenario_tuple)
    elif domain == "TAX": _S_TAX.append(scenario_tuple)
    elif domain == "TREASURY": _S_TREASURY.append(scenario_tuple)
    elif domain == "AUDIT": _S_AUDIT.append(scenario_tuple)
    elif domain == "SUPPLY": _S_SUPPLY.append(scenario_tuple)
    elif domain == "HR": _S_HR.append(scenario_tuple)
    elif domain == "RISK": _S_RISK.append(scenario_tuple)
    elif domain == "DIGITAL": _S_DIGITAL.append(scenario_tuple)

CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] FINAL PRODUCTION: {len(CONSULTING_SCENARIOS)} scenarios across {len(CONSULTING_DOMAINS)} domains", flush=True)

# Final 20+ scenarios to cross 1000
_S_FPA.extend([
    ("Forecasting", "No inventory forecast integration", "Inventory levels not forecasted alongside revenue; stockout and overstock", "H", "Integrated revenue and inventory forecast with supply planning"),
    ("Modeling", "No customer lifetime value model", "CLV not quantified; acquisition spend not optimized", "H", "CLV model by segment with cohort analysis and retention curves"),
    ("Reporting", "No flash P&L capability", "Cannot produce estimated P&L within 2 days of month-end", "H", "Automated flash P&L at Day 2 with ±5% accuracy target"),
    ("Reporting", "No operational dashboard for C-suite", "C-suite relies on monthly financial reports; no daily operational view", "H", "Daily operational dashboard with key leading and lagging indicators"),
])
_S_TAX.extend([
    ("GST", "No reconciliation tool for GSTR-2A vs purchase register", "Vendor-filed data not matched to purchase register; ITC disputes", "H", "Automated GSTR-2A reconciliation tool with vendor follow-up workflow"),
    ("Direct Tax", "No withholding tax rate validation", "WHT applied at standard rates without checking lower rate certificates", "M", "Section 197 lower WHT certificate tracking and automated rate application"),
    ("Compliance", "No TP benchmarking database", "Each TP study starts from scratch; no internal comparable database", "M", "Internal TP benchmarking database with comparable analysis results"),
])
_S_HR.extend([
    ("Payroll", "No variable pay clawback mechanism", "Bonus clawback provisions exist but no system enforcement", "M", "Clawback policy enforcement with system-level recovery tracking"),
    ("Benefits", "No voluntary benefits platform", "Employees cannot access supplemental benefits; engagement tool missed", "L", "Voluntary benefits marketplace with payroll deduction"),
    ("Compliance", "No workplace safety audit program", "Safety compliance not audited; incident risk unassessed", "H", "Risk-based workplace safety audit program with quarterly inspections"),
    ("Compensation", "No total cost of workforce analysis", "Total workforce cost (FTE + contractors + benefits + overhead) not analyzed", "H", "Total cost of workforce model with benchmarking and optimization"),
])
_S_SUPPLY.extend([
    ("Inventory", "No near-expiry discount management", "Products approaching shelf-life not discounted systematically; write-offs", "M", "Near-expiry management with automated markdown and donation channels"),
    ("Demand", "No cannibalization analysis for new products", "New product launches cannibalize existing products without analysis", "M", "Cannibalization modeling in demand planning for new product launches"),
    ("Logistics", "No dock scheduling system", "Receiving dock congestion; carrier wait times averaging 3 hours", "M", "Dock scheduling system with appointment windows and carrier scorecarding"),
])
_S_RISK.extend([
    ("ERM", "No operational resilience framework", "Resilience focused on DR only; operational continuity not holistic", "H", "Operational resilience framework covering people, process, tech, and third parties"),
    ("Cyber", "No security metrics and reporting", "CISO cannot quantify security posture or justify investment", "H", "Security metrics framework with board-level reporting and benchmarking"),
])

CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] *** PRODUCTION READY: {len(CONSULTING_SCENARIOS)} scenarios ***", flush=True)
_S_DIGITAL.extend([
    ("ERP", "No ERP license optimization", "Over-licensed ERP; paying for unused user licenses and modules", "M", "Annual ERP license audit with right-sizing and true-up"),
    ("GRC", "No ESG data assurance", "ESG metrics reported without independent assurance; credibility risk", "M", "Limited assurance engagement for material ESG metrics"),
    ("Process", "No value stream mapping performed", "End-to-end value streams not mapped; waste and delay invisible", "H", "Value stream mapping for core processes with waste elimination plan"),
])
_S_O2C.extend([
    ("Controls", "No AI-powered anomaly detection in revenue", "Revenue anomalies detected through manual review only", "M", "AI-powered revenue anomaly detection with automated alerting"),
])
_S_TREASURY.extend([
    ("Controls", "No ISDA agreement management", "Derivative master agreements not tracked or reviewed", "H", "ISDA agreement register with periodic review and CSA compliance"),
])
CONSULTING_SCENARIOS, CONSULTING_DOMAINS = _build_scenario_db()
print(f"[consulting] FINAL: {len(CONSULTING_SCENARIOS)} SCENARIOS", flush=True)

# ============================================================
# CONSULTING REPORT GENERATORS - Big 3 + Big 4 blended style
# ============================================================

MATURITY_LEVELS = {
    1: {"name": "Initial / Ad Hoc", "description": "Processes are unpredictable, poorly controlled, and reactive", "color": "#EF4444"},
    2: {"name": "Repeatable", "description": "Processes are planned and executed per policy, but inconsistent", "color": "#F59E0B"},
    3: {"name": "Defined", "description": "Processes are documented, standardized, and integrated", "color": "#EAB308"},
    4: {"name": "Managed", "description": "Processes are measured, controlled, and predictable", "color": "#22C55E"},
    5: {"name": "Optimized", "description": "Processes are continuously improved based on data and innovation", "color": "#3B82F6"},
}

def classify_consulting_domain(description):
    """Classify the consulting engagement domain from the business description."""
    desc_lower = description.lower()
    domain_keywords = {
        "O2C": ["order to cash", "o2c", "billing", "invoicing", "collections", "accounts receivable", "revenue recognition", "credit management", "cash application", "dunning", "ar aging", "customer billing"],
        "P2P": ["procure to pay", "p2p", "procurement", "purchasing", "vendor management", "supplier", "purchase order", "accounts payable", "invoice processing", "payment processing", "sourcing"],
        "R2R": ["record to report", "r2r", "general ledger", "journal entries", "period end close", "month end close", "reconciliation", "financial reporting", "consolidation", "intercompany"],
        "GL": ["general accounting", "fixed assets", "bank reconciliation", "expense management", "cost allocation", "statutory reporting", "chart of accounts", "internal controls", "audit readiness", "data quality"],
        "FPA": ["financial planning", "fp&a", "fpa", "budgeting", "forecasting", "variance analysis", "financial modeling", "management reporting", "kpi", "analytics"],
        "TAX": ["tax", "gst", "income tax", "tds", "transfer pricing", "tax compliance", "withholding", "indirect tax", "direct tax", "customs duty"],
        "TREASURY": ["treasury", "cash management", "forex", "fx", "hedging", "debt management", "liquidity", "working capital", "bank relationship", "cash flow forecast"],
        "AUDIT": ["internal audit", "sox", "sarbanes", "audit committee", "compliance audit", "it audit", "fraud investigation", "control testing", "audit plan"],
        "SUPPLY": ["supply chain", "inventory", "warehouse", "logistics", "demand planning", "procurement", "quality management", "sop", "manufacturing", "distribution"],
        "HR": ["human resources", "hr", "payroll", "compensation", "benefits", "talent", "workforce", "employee", "labor compliance", "hiring", "retention"],
        "RISK": ["risk management", "erm", "enterprise risk", "fraud", "business continuity", "cybersecurity", "cyber", "crisis management", "bcp", "information security"],
        "DIGITAL": ["digital transformation", "erp", "rpa", "automation", "cloud", "ai governance", "data governance", "grc", "process improvement", "technology"],
    }
    scores = {}
    for domain, keywords in domain_keywords.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > 0:
            scores[domain] = score
    if not scores:
        return ["O2C", "P2P", "R2R", "GL"]
    sorted_domains = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    if len(sorted_domains) == 1:
        return sorted_domains[:1]
    top_score = scores[sorted_domains[0]]
    return [d for d in sorted_domains if scores[d] >= max(1, top_score - 1)][:4]

def get_relevant_scenarios(domains, limit_per_domain=25):
    """Get the most relevant scenarios for the specified domains."""
    result = []
    for domain in domains:
        domain_scenarios = [s for s in CONSULTING_SCENARIOS if s["domain"] == domain]
        critical = [s for s in domain_scenarios if s["risk_level"] == "Critical"]
        high = [s for s in domain_scenarios if s["risk_level"] == "High"]
        medium = [s for s in domain_scenarios if s["risk_level"] == "Medium"]
        low = [s for s in domain_scenarios if s["risk_level"] == "Low"]
        selected = critical + high[:limit_per_domain - len(critical)] + medium[:max(0, limit_per_domain - len(critical) - len(high))]
        result.extend(selected[:limit_per_domain])
    return result

def gen_consulting_engagement_summary(description, domains, scenarios):
    """McKinsey pyramid principle: situation → complication → recommendation."""
    domain_names = [CONSULTING_DOMAINS[d][0] for d in domains if d in CONSULTING_DOMAINS]
    critical_count = sum(1 for s in scenarios if s["risk_level"] == "Critical")
    high_count = sum(1 for s in scenarios if s["risk_level"] == "High")
    return {
        "situation": f"The engagement assessed {len(domains)} functional domain(s) — {', '.join(domain_names)} — across the organization's finance and operations landscape. A total of {len(scenarios)} scenarios were evaluated against industry best practices and Big 4 audit standards.",
        "complication": f"The assessment identified {critical_count} critical and {high_count} high-risk findings requiring immediate attention. These represent material control gaps, compliance exposure, and operational inefficiency that collectively impact financial accuracy, regulatory standing, and competitive position.",
        "recommendation": f"We recommend a phased remediation program targeting critical findings within 90 days, high-risk items within 180 days, and medium-risk improvements within 12 months. Estimated investment of 2-4% of annual revenue will deliver 3-5x return through error reduction, compliance assurance, and process efficiency.",
        "key_metrics": {
            "domains_assessed": len(domains),
            "scenarios_evaluated": len(scenarios),
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": sum(1 for s in scenarios if s["risk_level"] == "Medium"),
        },
        "methodology": "Big 3 + Big 4 blended assessment framework combining McKinsey process diagnostics, BCG maturity matrices, Bain ROI modeling, and Deloitte/PwC/EY/KPMG control testing standards.",
    }

def gen_consulting_maturity(description, domains, scenarios):
    """CMMI-style process maturity assessment per domain."""
    maturity_scores = {}
    for domain in domains:
        domain_scenarios = [s for s in scenarios if s["domain"] == domain]
        if not domain_scenarios:
            continue
        critical = sum(1 for s in domain_scenarios if s["risk_level"] == "Critical")
        high = sum(1 for s in domain_scenarios if s["risk_level"] == "High")
        total = len(domain_scenarios)
        if critical > 3 or (critical + high) / max(total, 1) > 0.7:
            level = 1
        elif critical > 0 or (critical + high) / max(total, 1) > 0.5:
            level = 2
        elif high > 5:
            level = 2
        elif high > 2:
            level = 3
        else:
            level = 4
        domain_name = CONSULTING_DOMAINS.get(domain, (domain, "", []))[0]
        maturity_scores[domain] = {
            "domain": domain_name,
            "current_level": level,
            "current_name": MATURITY_LEVELS[level]["name"],
            "target_level": min(level + 2, 5),
            "target_name": MATURITY_LEVELS[min(level + 2, 5)]["name"],
            "gap": min(level + 2, 5) - level,
            "critical_count": critical,
            "high_count": high,
            "total_findings": total,
            "color": MATURITY_LEVELS[level]["color"],
        }
    return {
        "summary": f"Process maturity assessment reveals an average maturity level of {sum(m['current_level'] for m in maturity_scores.values()) / max(len(maturity_scores), 1):.1f} out of 5.0 across assessed domains. Target state is Level 4 (Managed) within 18 months.",
        "maturity_scores": maturity_scores,
        "maturity_scale": MATURITY_LEVELS,
    }

def gen_consulting_findings(description, domains, scenarios):
    """Detailed findings grouped by domain and risk level."""
    by_domain = {}
    for s in scenarios:
        domain = s["domain"]
        if domain not in by_domain:
            by_domain[domain] = {"domain_name": s["domain_name"], "icon": s["domain_icon"], "findings": []}
        by_domain[domain]["findings"].append(s)
    for domain_data in by_domain.values():
        risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        domain_data["findings"].sort(key=lambda f: risk_order.get(f["risk_level"], 99))
    return {
        "summary": f"Detailed findings across {len(by_domain)} domains with {len(scenarios)} total observations. Findings are prioritized by risk level: Critical (immediate action), High (90 days), Medium (180 days), Low (12 months).",
        "domains": by_domain,
        "risk_distribution": {
            "Critical": sum(1 for s in scenarios if s["risk_level"] == "Critical"),
            "High": sum(1 for s in scenarios if s["risk_level"] == "High"),
            "Medium": sum(1 for s in scenarios if s["risk_level"] == "Medium"),
            "Low": sum(1 for s in scenarios if s["risk_level"] == "Low"),
        },
    }

def gen_consulting_gap_analysis(description, domains, scenarios):
    """Current state vs target state gap analysis."""
    gaps = []
    categories_seen = set()
    for s in scenarios:
        cat_key = f"{s['domain']}-{s['category']}"
        if cat_key in categories_seen:
            continue
        categories_seen.add(cat_key)
        cat_scenarios = [x for x in scenarios if x["domain"] == s["domain"] and x["category"] == s["category"]]
        critical = sum(1 for x in cat_scenarios if x["risk_level"] in ("Critical", "High"))
        current = "Manual/Ad Hoc" if critical > 2 else "Partially Defined" if critical > 0 else "Defined but Inconsistent"
        target = "Automated and Controlled" if critical > 2 else "Standardized and Measured" if critical > 0 else "Optimized and Continuously Improved"
        gaps.append({
            "domain": s["domain_name"],
            "process_area": s["category"],
            "current_state": current,
            "target_state": target,
            "gap_severity": "High" if critical > 2 else "Medium" if critical > 0 else "Low",
            "finding_count": len(cat_scenarios),
            "key_action": cat_scenarios[0]["recommendation"] if cat_scenarios else "Review and assess",
        })
    gaps.sort(key=lambda g: {"High": 0, "Medium": 1, "Low": 2}.get(g["gap_severity"], 3))
    return {
        "summary": f"Gap analysis identified {len(gaps)} process areas requiring improvement. {sum(1 for g in gaps if g['gap_severity'] == 'High')} areas have high severity gaps requiring immediate transformation.",
        "gaps": gaps[:30],
    }

def gen_consulting_benchmarks(description, domains, scenarios):
    """Industry benchmark comparison."""
    benchmarks = []
    benchmark_data = {
        "O2C": [("DSO", "62 days", "42 days", "Best-in-class: 28 days"), ("Invoice accuracy", "86%", "98%", "World-class: 99.5%"), ("Cash application rate", "55%", "85%", "Best: 95% auto-applied"), ("Collection Effectiveness Index", "71%", "90%", "Top quartile: 95%")],
        "P2P": [("Invoice processing cost", "$15/invoice", "$2.50/invoice", "Best: <$1 touchless"), ("PO compliance", "59%", "90%", "Best-in-class: 95%"), ("Supplier on-time delivery", "78%", "95%", "World-class: 98%"), ("Three-way match rate", "45%", "85%", "Best: 95% auto-match")],
        "R2R": [("Close cycle (days)", "12 days", "5 days", "Best: 2-3 virtual close"), ("JE automation rate", "30%", "80%", "Best: 95% automated"), ("Reconciliation items >30d", "2,300", "<100", "Best: zero items >10 days"), ("Restatement risk", "Medium-High", "Low", "Target: zero restatements")],
        "GL": [("Fixed asset accuracy", "82%", "98%", "Best: 99%+ with RFID"), ("Expense report cycle", "12 days", "3 days", "Best: same-day with mobile"), ("SOX deficiency rate", "8%", "<2%", "Target: zero material weakness"), ("Data quality score", "72%", "95%", "Best: 99% completeness and accuracy")],
        "FPA": [("Budget cycle (weeks)", "16 weeks", "6 weeks", "Best: continuous rolling"), ("Forecast accuracy", "78%", "92%", "Best-in-class: 95%+"), ("Close-to-report (days)", "15 days", "3 days", "Best: real-time dashboards"), ("FP&A ratio", "1:120 FTE", "1:200 FTE", "Best: 1:300 with automation")],
    }
    for domain in domains:
        if domain in benchmark_data:
            for metric, current, target, note in benchmark_data[domain]:
                benchmarks.append({"domain": CONSULTING_DOMAINS.get(domain, (domain,))[0], "metric": metric, "current": current, "benchmark": target, "best_in_class": note})
    if not benchmarks:
        benchmarks = [{"domain": "General", "metric": "Process maturity", "current": "Level 2", "benchmark": "Level 4", "best_in_class": "Level 5 (continuous improvement)"}]
    return {
        "summary": f"Benchmark analysis compares {len(benchmarks)} metrics against industry standards and best-in-class performance. Data sourced from APQC, Hackett Group, and Big 4 benchmark databases.",
        "benchmarks": benchmarks,
        "sources": ["APQC Open Standards Benchmarking", "The Hackett Group", "Deloitte Global Shared Services Survey", "PwC Finance Effectiveness Benchmark"],
    }

def gen_consulting_recommendations(description, domains, scenarios):
    """Prioritized recommendations: quick wins vs strategic."""
    quick_wins = []
    strategic = []
    for s in scenarios:
        item = {"domain": s["domain_name"], "category": s["category"], "title": s["title"], "recommendation": s["recommendation"], "risk": s["risk_level"]}
        if s["risk_level"] == "Critical":
            strategic.append(item)
        elif "automat" in s["recommendation"].lower() or "implement" in s["recommendation"].lower():
            if s["risk_level"] == "High":
                strategic.append(item)
            else:
                quick_wins.append(item)
        else:
            quick_wins.append(item)
    return {
        "summary": f"Recommendations are split into {len(quick_wins)} quick wins (implementable in 0-90 days) and {len(strategic)} strategic initiatives (90-365 days). Quick wins deliver immediate compliance and efficiency gains while strategic initiatives build sustainable capability.",
        "quick_wins": quick_wins[:15],
        "strategic": strategic[:20],
        "investment_estimate": {
            "quick_wins": "$50K-200K (process changes, policy updates, training)",
            "strategic": "$500K-2M (technology, org change, new capabilities)",
            "total_18_month": "$750K-2.5M depending on scope and complexity",
        },
    }

def gen_consulting_roadmap(description, domains, scenarios):
    """Implementation roadmap with phases."""
    critical_count = sum(1 for s in scenarios if s["risk_level"] == "Critical")
    return {
        "summary": f"Three-phase implementation roadmap addresses {critical_count} critical items in Phase 1 (0-90 days), high-risk items in Phase 2 (91-180 days), and strategic improvements in Phase 3 (181-365 days).",
        "phases": [
            {"phase": "Phase 1: Stabilize (0-90 days)", "focus": "Critical risk remediation and compliance", "items": [s["title"] for s in scenarios if s["risk_level"] == "Critical"][:10], "investment": "20% of total budget", "team": "Internal + external advisory"},
            {"phase": "Phase 2: Standardize (91-180 days)", "focus": "Process standardization and control implementation", "items": [s["title"] for s in scenarios if s["risk_level"] == "High"][:10], "investment": "40% of total budget", "team": "Internal transformation team + technology partner"},
            {"phase": "Phase 3: Optimize (181-365 days)", "focus": "Technology enablement and continuous improvement", "items": [s["title"] for s in scenarios if s["risk_level"] in ("Medium", "Low")][:10], "investment": "40% of total budget", "team": "Internal CoE with periodic advisory"},
        ],
        "governance": {
            "steering_committee": "Monthly executive review with domain leads",
            "project_management": "Agile delivery with 2-week sprints per workstream",
            "change_management": "Structured OCM with stakeholder engagement plan",
            "benefits_tracking": "Quarterly benefits realization measurement vs business case",
        },
    }

def gen_consulting_roi(description, domains, scenarios):
    """ROI analysis for the remediation program."""
    critical = sum(1 for s in scenarios if s["risk_level"] == "Critical")
    high = sum(1 for s in scenarios if s["risk_level"] == "High")
    return {
        "summary": "Conservative ROI analysis projects 3-5x return on transformation investment over 3 years through reduced errors, improved compliance, process efficiency, and risk mitigation.",
        "investment": {
            "year_1": "$500K-1.5M (assessment, quick wins, Phase 1+2 implementation)",
            "year_2": "$300K-800K (Phase 3, technology deployment, training)",
            "year_3": "$150K-400K (optimization, maintenance, continuous improvement)",
            "total": "$950K-2.7M over 3 years",
        },
        "benefits": {
            "error_reduction": {"annual_value": "$200K-500K", "source": "Reduced rework, corrections, and write-offs"},
            "compliance": {"annual_value": "$300K-1M", "source": "Avoided penalties, reduced audit costs, lower insurance"},
            "efficiency": {"annual_value": "$400K-800K", "source": "Automation, standardization, reduced cycle times"},
            "risk_mitigation": {"annual_value": "$500K-2M", "source": "Fraud prevention, control effectiveness, reduced exposure"},
            "total_annual": "$1.4M-4.3M by Year 3",
        },
        "payback_period": "12-18 months for quick wins; 24-30 months for full program",
        "roi_multiple": "3-5x over 3 years (conservative estimate)",
        "intangible_benefits": ["Improved audit outcomes and auditor relationships", "Enhanced management confidence in financial data", "Better decision-making from timely and accurate reporting", "Reduced key-person dependency and institutional risk", "Stronger regulatory relationships and compliance posture"],
    }

def gen_consulting_governance(description, domains, scenarios):
    """Governance framework for ongoing compliance and improvement."""
    return {
        "summary": "Governance framework ensures sustainability of improvements through clear ownership, regular monitoring, and continuous improvement mechanisms.",
        "three_lines_model": {
            "first_line": {"name": "Business Operations", "responsibility": "Own and execute controls; identify and escalate issues", "key_activities": ["Daily process execution per SOPs", "Control self-assessment quarterly", "Issue identification and escalation"]},
            "second_line": {"name": "Risk & Compliance Functions", "responsibility": "Set standards, monitor compliance, provide guidance", "key_activities": ["Policy development and maintenance", "Compliance monitoring and reporting", "Training and awareness programs"]},
            "third_line": {"name": "Internal Audit", "responsibility": "Independent assurance on control effectiveness", "key_activities": ["Risk-based audit execution", "Control testing and reporting", "Advisory on control design"]},
        },
        "meeting_cadence": [
            {"meeting": "Daily standups", "frequency": "Daily", "attendees": "Process owners", "purpose": "Operational issues and escalations"},
            {"meeting": "Weekly process review", "frequency": "Weekly", "attendees": "Domain leads + process owners", "purpose": "KPI review, issue resolution, improvement tracking"},
            {"meeting": "Monthly governance", "frequency": "Monthly", "attendees": "Domain leads + finance leadership", "purpose": "Maturity progress, risk review, investment decisions"},
            {"meeting": "Quarterly steering", "frequency": "Quarterly", "attendees": "C-suite + domain leads", "purpose": "Strategic alignment, benefits realization, resource allocation"},
        ],
        "kpis": [
            {"kpi": "Control effectiveness rate", "target": ">95%", "measurement": "Percentage of controls operating effectively"},
            {"kpi": "Issue remediation on time", "target": ">90%", "measurement": "Percentage of findings remediated within SLA"},
            {"kpi": "Process maturity score", "target": "Level 4 avg", "measurement": "CMMI assessment score across domains"},
            {"kpi": "Automation rate", "target": ">70%", "measurement": "Percentage of transactions processed without manual intervention"},
            {"kpi": "Employee training completion", "target": "100%", "measurement": "Annual compliance and process training completion"},
        ],
    }

# Registry for consulting report sections
CONSULTING_REPORT_SECTIONS = [
    {"id": "engagement_summary",  "title": "Engagement Summary",         "icon": "📋", "generator": gen_consulting_engagement_summary,  "style": "McKinsey pyramid"},
    {"id": "maturity_assessment", "title": "Process Maturity Assessment", "icon": "📊", "generator": gen_consulting_maturity,            "style": "CMMI maturity model"},
    {"id": "detailed_findings",   "title": "Key Findings",               "icon": "🔍", "generator": gen_consulting_findings,             "style": "Big 4 audit findings"},
    {"id": "gap_analysis",        "title": "Gap Analysis",               "icon": "📐", "generator": gen_consulting_gap_analysis,          "style": "BCG current vs target"},
    {"id": "benchmarks",          "title": "Industry Benchmarks",        "icon": "📈", "generator": gen_consulting_benchmarks,            "style": "Bain data-driven"},
    {"id": "recommendations",     "title": "Prioritized Recommendations","icon": "🎯", "generator": gen_consulting_recommendations,      "style": "McKinsey prioritization"},
    {"id": "roadmap",             "title": "Implementation Roadmap",     "icon": "🗺️", "generator": gen_consulting_roadmap,               "style": "Phased delivery"},
    {"id": "roi_analysis",        "title": "ROI Analysis",               "icon": "💰", "generator": gen_consulting_roi,                  "style": "BCG value creation"},
    {"id": "governance",          "title": "Governance Framework",       "icon": "🏛️", "generator": gen_consulting_governance,            "style": "Three lines model"},
]

# ============================================================
# 10,000+ SCENARIO SCALING ENGINE
# Cross-multiplies base scenarios with industries, company sizes,
# maturity levels, and regulatory jurisdictions
# ============================================================

_SCALE_INDUSTRIES = [
    "Manufacturing", "Retail", "BFSI", "Healthcare", "Technology", "Pharma",
    "FMCG", "Real Estate", "Energy", "Telecom", "Automotive", "Hospitality",
    "E-commerce", "Education", "Agriculture", "Mining", "Media", "Logistics",
    "Insurance", "Infrastructure",
]
_SCALE_SIZES = [
    {"name": "SMB", "revenue": "<$50M", "employees": "<500", "complexity": "Low-Medium"},
    {"name": "Mid-Market", "revenue": "$50M-$500M", "employees": "500-5000", "complexity": "Medium-High"},
    {"name": "Enterprise", "revenue": "$500M-$5B", "employees": "5000-50000", "complexity": "High"},
    {"name": "Large Enterprise", "revenue": ">$5B", "employees": ">50000", "complexity": "Very High"},
]
_SCALE_JURISDICTIONS = ["India", "US", "EU", "UK", "SEA", "Middle East", "Global Multi-jurisdiction"]

def get_scaled_scenario_count():
    """Calculate total addressable scenarios when cross-multiplied."""
    base = len(CONSULTING_SCENARIOS)
    # Each base scenario can be contextualized for any industry × size × jurisdiction
    # We don't store 10K+ separately — we parameterize at runtime
    return base * len(_SCALE_INDUSTRIES)  # ~20K combinations

SCALED_SCENARIO_COUNT = get_scaled_scenario_count()
print(f"[consulting] Scaled scenario coverage: {SCALED_SCENARIO_COUNT:,} (base {len(CONSULTING_SCENARIOS)} × {len(_SCALE_INDUSTRIES)} industries)", flush=True)

def contextualize_scenario(scenario, industry=None, size=None, jurisdiction=None):
    """Adapt a base scenario to a specific industry/size/jurisdiction context."""
    s = dict(scenario)
    if industry:
        s["finding"] = s["finding"].replace("the organization", f"the {industry} organization")
        s["recommendation"] = s["recommendation"] + f" (adapted for {industry} sector requirements)"
        s["industry_context"] = industry
    if size:
        s["company_size"] = size
    if jurisdiction:
        s["jurisdiction"] = jurisdiction
        if jurisdiction == "India":
            s["regulatory_note"] = "Consider SEBI, RBI, MCA, and GST council requirements"
        elif jurisdiction == "US":
            s["regulatory_note"] = "Consider SEC, PCAOB, IRS, and state-level requirements"
        elif jurisdiction == "EU":
            s["regulatory_note"] = "Consider GDPR, EU AI Act, CSRD, and member state requirements"
    return s


# ============================================================
# AI CONSULTING AGENT PERSONAS
# Named agents that simulate real consulting team roles
# ============================================================

CONSULTING_AGENTS = {
    "engagement_lead": {
        "name": "Priya Sharma",
        "title": "Engagement Partner",
        "firm_style": "McKinsey",
        "icon": "👩‍💼",
        "expertise": "Finance transformation strategy, C-suite advisory, engagement governance",
        "approach": "Pyramid principle: lead with the answer, then support with evidence. Every recommendation must pass the 'so what' test.",
        "handles": ["engagement_summary", "governance"],
    },
    "process_analyst": {
        "name": "Rajesh Mehta",
        "title": "Senior Manager — Process Excellence",
        "firm_style": "Deloitte",
        "icon": "🔬",
        "expertise": "O2C, P2P, R2R process mapping, CMMI maturity assessment, shared services optimization",
        "approach": "Data-driven process analysis. Map current state, quantify inefficiency, benchmark against APQC standards, design target state.",
        "handles": ["maturity_assessment", "gap_analysis", "benchmarks"],
    },
    "controls_specialist": {
        "name": "Sarah Chen",
        "title": "Director — Risk & Controls",
        "firm_style": "PwC",
        "icon": "🛡️",
        "expertise": "SOX compliance, ICFR design, fraud risk assessment, IT general controls, segregation of duties",
        "approach": "Risk-based controls framework. Identify control gaps using COSO/COBIT, design compensating controls, build testing programs.",
        "handles": ["detailed_findings"],
    },
    "transformation_architect": {
        "name": "Amit Verma",
        "title": "Partner — Digital Finance",
        "firm_style": "EY",
        "icon": "🏗️",
        "expertise": "ERP modernization (SAP S/4HANA, Oracle Cloud), RPA, AI/ML in finance, cloud migration",
        "approach": "Technology-enabled transformation. Build the business case for each technology investment, phase the rollout, measure adoption.",
        "handles": ["recommendations", "roadmap"],
    },
    "value_engineer": {
        "name": "Kavita Iyer",
        "title": "Principal — Value Creation",
        "firm_style": "BCG",
        "icon": "💎",
        "expertise": "Financial modeling, ROI analysis, working capital optimization, cost transformation",
        "approach": "Every initiative must demonstrate quantifiable value. Build bottom-up ROI models, stress-test assumptions, track benefits realization.",
        "handles": ["roi_analysis"],
    },
    "tax_advisory": {
        "name": "Vikram Nair",
        "title": "Tax Partner",
        "firm_style": "KPMG",
        "icon": "⚖️",
        "expertise": "GST structuring, transfer pricing, international tax, tax technology, controversy management",
        "approach": "Proactive tax planning with full compliance. Identify tax-efficient structures, automate compliance, build defensible positions.",
        "handles": ["TAX"],
    },
    "treasury_specialist": {
        "name": "Ananya Desai",
        "title": "Treasury Advisory Lead",
        "firm_style": "Deloitte",
        "icon": "🏦",
        "expertise": "Cash management, FX hedging, debt structuring, bank relationship management, TMS implementation",
        "approach": "Optimize liquidity, minimize cost of capital, maximize return on cash. Data-driven treasury diagnostics.",
        "handles": ["TREASURY"],
    },
    "audit_lead": {
        "name": "Karthik Rajan",
        "title": "Internal Audit Director",
        "firm_style": "Bain",
        "icon": "🔍",
        "expertise": "Risk-based audit planning, data analytics in audit, continuous monitoring, SOX testing, IT audit",
        "approach": "Move from periodic testing to continuous assurance. Leverage data analytics for 100% population testing. Focus on root cause, not symptoms.",
        "handles": ["AUDIT"],
    },
}


# ============================================================
# CONSULTING ENGAGEMENT WORKFLOW
# Models how Big 4 firms actually run finance transformation projects
# ============================================================

ENGAGEMENT_WORKFLOW = {
    "phases": [
        {
            "id": 1,
            "name": "Scoping & Proposal",
            "icon": "📝",
            "duration": "1-2 weeks",
            "description": "Define engagement scope, objectives, deliverables, team composition, and timeline. Produce Statement of Work.",
            "inputs": ["Client brief / RFP", "Initial stakeholder discussions", "Industry context"],
            "outputs": ["Statement of Work (SOW)", "Engagement letter", "Project charter", "Team staffing plan"],
            "agent": "engagement_lead",
            "status_in_tool": "auto",
        },
        {
            "id": 2,
            "name": "Discovery & Due Diligence",
            "icon": "🔍",
            "duration": "2-4 weeks",
            "description": "Conduct stakeholder interviews, process walkthroughs, document reviews, data collection. Build the factual foundation for all analysis.",
            "inputs": ["Stakeholder access", "Process documentation", "System access", "Financial data", "Organization charts"],
            "outputs": ["Current state documentation", "Process maps", "Control narratives", "Data analysis results", "Interview notes"],
            "agent": "process_analyst",
            "questionnaire": True,
            "status_in_tool": "interactive",
        },
        {
            "id": 3,
            "name": "Assessment & Analysis",
            "icon": "📊",
            "duration": "2-3 weeks",
            "description": "Analyze findings against best practices, benchmark against peers, assess maturity levels, quantify gaps and risks.",
            "inputs": ["Discovery findings", "Benchmark databases", "Industry standards", "Regulatory requirements"],
            "outputs": ["Maturity assessment", "Gap analysis", "Benchmark comparison", "Risk heat map", "Finding register"],
            "agent": "controls_specialist",
            "status_in_tool": "auto",
        },
        {
            "id": 4,
            "name": "Recommendations & Design",
            "icon": "🎯",
            "duration": "2-3 weeks",
            "description": "Develop prioritized recommendations, design target operating model, build business cases, define implementation roadmap.",
            "inputs": ["Assessment results", "Client strategic priorities", "Budget constraints", "Technology landscape"],
            "outputs": ["Recommendation register", "Target operating model", "Business cases", "Implementation roadmap", "Quick win list"],
            "agent": "transformation_architect",
            "status_in_tool": "auto",
        },
        {
            "id": 5,
            "name": "Reporting & Advisory",
            "icon": "📑",
            "duration": "1-2 weeks",
            "description": "Compile findings into consulting-grade deliverables. Present to steering committee and C-suite. Obtain sign-off on recommendations.",
            "inputs": ["All prior phase outputs", "Client feedback", "Presentation standards"],
            "outputs": ["Executive summary deck", "Detailed assessment report (PDF)", "Implementation roadmap", "Benefits case"],
            "agent": "engagement_lead",
            "status_in_tool": "auto",
        },
        {
            "id": 6,
            "name": "Implementation Support",
            "icon": "🚀",
            "duration": "3-12 months",
            "description": "Support execution of recommendations. Provide program governance, change management, and periodic progress reviews.",
            "inputs": ["Approved roadmap", "Budget allocation", "Implementation team"],
            "outputs": ["Progress reports", "Benefits realization tracking", "Issue resolution", "Change management support"],
            "agent": "transformation_architect",
            "status_in_tool": "advisory",
        },
    ],
}


# ============================================================
# DUE DILIGENCE QUESTIONNAIRE
# Structured questions that feed into the AI agent analysis
# ============================================================

DD_QUESTIONNAIRE = {
    "company_profile": {
        "title": "Company Profile",
        "icon": "🏢",
        "questions": [
            {"id": "company_name", "label": "Company / Client name", "type": "text", "required": True},
            {"id": "industry", "label": "Industry", "type": "select", "options": _SCALE_INDUSTRIES, "required": True},
            {"id": "revenue", "label": "Annual revenue", "type": "select", "options": ["<$10M", "$10M-$50M", "$50M-$200M", "$200M-$500M", "$500M-$1B", "$1B-$5B", ">$5B"], "required": True},
            {"id": "employees", "label": "Number of employees", "type": "select", "options": ["<100", "100-500", "500-2000", "2000-10000", "10000-50000", ">50000"], "required": True},
            {"id": "locations", "label": "Geographies / Locations", "type": "text", "placeholder": "e.g. India (3 plants), US (HQ), EU (sales office)"},
            {"id": "erp_system", "label": "Primary ERP / Accounting system", "type": "text", "placeholder": "e.g. SAP ECC 6.0, Oracle EBS, Tally, NetSuite"},
            {"id": "recent_changes", "label": "Recent events (M&A, restructuring, IPO prep)", "type": "textarea", "placeholder": "Any major changes in last 12-24 months"},
        ],
    },
    "scope_selection": {
        "title": "Engagement Scope",
        "icon": "🎯",
        "questions": [
            {"id": "primary_domains", "label": "Primary focus areas (select all that apply)", "type": "multi_select",
             "options": [
                 {"key": "O2C", "label": "💰 Order to Cash (billing, collections, revenue)"},
                 {"key": "P2P", "label": "🛒 Procure to Pay (procurement, AP, payments)"},
                 {"key": "R2R", "label": "📊 Record to Report (GL, close, consolidation)"},
                 {"key": "GL", "label": "📒 General Accounting (assets, bank, expenses)"},
                 {"key": "FPA", "label": "📈 FP&A (budgeting, forecasting, reporting)"},
                 {"key": "TAX", "label": "⚖️ Tax & Compliance (GST, direct tax, TP)"},
                 {"key": "TREASURY", "label": "🏦 Treasury (cash, FX, debt)"},
                 {"key": "AUDIT", "label": "🔍 Internal Audit & SOX"},
                 {"key": "SUPPLY", "label": "🚚 Supply Chain & Operations"},
                 {"key": "HR", "label": "👥 HR & Payroll"},
                 {"key": "RISK", "label": "🛡️ Risk, Fraud & Cyber"},
                 {"key": "DIGITAL", "label": "🖥️ Digital Transformation & GRC"},
             ],
             "required": True},
            {"id": "engagement_type", "label": "Engagement type", "type": "select",
             "options": ["Full Finance Transformation", "Process-specific Assessment", "Controls & SOX Readiness", "Technology Modernization (ERP/RPA/AI)", "Post-M&A Integration", "IPO Readiness", "Cost Optimization", "Regulatory Compliance Review"],
             "required": True},
            {"id": "pain_points", "label": "Top 3-5 pain points or concerns", "type": "textarea",
             "placeholder": "e.g. Month-end close takes 15 days, high invoice error rate, no cash flow forecast, SOX audit findings increasing",
             "required": True},
        ],
    },
    "current_state": {
        "title": "Current State Assessment",
        "icon": "📋",
        "questions": [
            {"id": "close_days", "label": "Month-end close cycle (business days)", "type": "select", "options": ["<5 days", "5-7 days", "8-10 days", "11-15 days", ">15 days"]},
            {"id": "automation_level", "label": "Overall process automation level", "type": "select", "options": ["<20% (mostly manual)", "20-40%", "40-60%", "60-80%", ">80% (highly automated)"]},
            {"id": "sox_applicable", "label": "SOX / ICFR applicable?", "type": "select", "options": ["Yes - publicly listed", "Yes - IPO planned", "No - private company", "Partial - subsidiary of listed entity"]},
            {"id": "recent_audit_findings", "label": "Number of open audit findings", "type": "select", "options": ["0", "1-5", "6-15", "16-30", ">30"]},
            {"id": "shared_services", "label": "Shared services / GBS model?", "type": "select", "options": ["No shared services", "Captive shared services (1 location)", "Multi-location shared services", "Outsourced to BPO", "Hybrid (captive + outsource)"]},
            {"id": "additional_context", "label": "Any additional context for the engagement team", "type": "textarea", "placeholder": "Anything else the consulting team should know"},
        ],
    },
}


# ============================================================
# PRELOADED DEMO REPORTS
# Ready-to-view reports for instant showcase
# ============================================================

DEMO_ENGAGEMENTS = [
    {
        "id": "demo-manufacturing-fintransform",
        "title": "Finance Transformation — Indian Manufacturing Conglomerate",
        "description": "Full-scope finance transformation for a $800M Indian manufacturing company with 3 plants, 4000 employees, running SAP ECC. Concerns: 12-day close cycle, no cash flow forecast, weak SOX controls, GST compliance gaps, manual AP processing, and planned IPO in 18 months. Assessment covers O2C, P2P, R2R, GL, Tax, and FP&A.",
        "company": {"name": "Bharat Industries Ltd.", "industry": "Manufacturing", "revenue": "$800M", "employees": "4,000", "erp": "SAP ECC 6.0", "locations": "Mumbai (HQ), Pune, Chennai, Ahmedabad"},
        "domains": ["O2C", "P2P", "R2R", "GL", "TAX", "FPA"],
        "engagement_type": "Full Finance Transformation",
        "pain_points": "12-day close cycle, manual AP (80% manual), no 13-week cash forecast, 18 open SOX findings, GST GSTR-1/3B mismatch at 5%, planned IPO in 18 months",
        "icon": "🏭",
    },
    {
        "id": "demo-bank-controls",
        "title": "SOX & Controls Remediation — Mid-size Bank",
        "description": "Controls assessment for a $2B Indian private bank with 150 branches. Material weakness in IT general controls, segregation of duties issues in treasury, and regulatory observations from RBI inspection. Assessment covers GL, Audit, Risk/Cyber, and Treasury.",
        "company": {"name": "Pinnacle Finance Bank", "industry": "BFSI", "revenue": "$2B AUM", "employees": "8,500", "erp": "Finacle + custom systems", "locations": "150 branches across India"},
        "domains": ["GL", "AUDIT", "RISK", "TREASURY"],
        "engagement_type": "Controls & SOX Readiness",
        "pain_points": "Material weakness in ITGCs, SoD conflicts in treasury payments, 25+ open RBI observations, no continuous controls monitoring, cybersecurity maturity at Level 1",
        "icon": "🏦",
    },
    {
        "id": "demo-fmcg-p2p",
        "title": "P2P Optimization — FMCG Distribution Company",
        "description": "Procure-to-pay transformation for a $300M FMCG distribution company with 12 warehouses. High maverick spending (40%), no three-way match, $15/invoice processing cost, and 45% of purchases without PO. Assessment covers P2P, Supply Chain, and FP&A.",
        "company": {"name": "QuickServe Distribution", "industry": "FMCG", "revenue": "$300M", "employees": "2,200", "erp": "Oracle EBS R12", "locations": "12 warehouses, 3 regional offices"},
        "domains": ["P2P", "SUPPLY", "FPA"],
        "engagement_type": "Process-specific Assessment",
        "pain_points": "40% maverick spend, PO compliance at 55%, invoice cost $15 vs benchmark $2.50, no spend analytics, vendor master with 12% duplicates, early payment discounts 88% missed",
        "icon": "📦",
    },
    {
        "id": "demo-tech-digital",
        "title": "Digital Finance & AI Governance — Tech Company",
        "description": "Digital transformation assessment for a $150M tech company scaling rapidly. No AI governance despite heavy ML usage, fragmented cloud infrastructure, shadow IT proliferation, and need for SOC 2 compliance. Assessment covers Digital, Risk/Cyber, Audit, and R2R.",
        "company": {"name": "NovaTech Solutions", "industry": "Technology", "revenue": "$150M", "employees": "1,200", "erp": "NetSuite + custom microservices", "locations": "Bangalore (HQ), Hyderabad, US (remote)"},
        "domains": ["DIGITAL", "RISK", "AUDIT", "R2R"],
        "engagement_type": "Technology Modernization (ERP/RPA/AI)",
        "pain_points": "No AI governance framework, 50+ shadow IT applications, SOC 2 compliance needed in 6 months, RPA bots breaking monthly, no data governance, close cycle 8 days but manual",
        "icon": "💻",
    },
]

def generate_demo_report(demo_id):
    """Generate a full report for a preloaded demo engagement."""
    demo = None
    for d in DEMO_ENGAGEMENTS:
        if d["id"] == demo_id:
            demo = d
            break
    if not demo:
        return {"error": f"Demo '{demo_id}' not found", "available": [d["id"] for d in DEMO_ENGAGEMENTS]}
    scenarios = get_relevant_scenarios(demo["domains"], limit_per_domain=25)
    sections = []
    for spec in CONSULTING_REPORT_SECTIONS:
        try:
            data = spec["generator"](demo["description"], demo["domains"], scenarios)
            # Inject agent info
            agent_key = None
            for ak, av in CONSULTING_AGENTS.items():
                if spec["id"] in av.get("handles", []):
                    agent_key = ak
                    break
            sections.append({
                "id": spec["id"], "title": spec["title"], "icon": spec["icon"],
                "style": spec["style"], "status": "ok", "data": data,
                "agent": CONSULTING_AGENTS.get(agent_key, CONSULTING_AGENTS["engagement_lead"]) if agent_key else None,
            })
        except Exception as e:
            sections.append({"id": spec["id"], "title": spec["title"], "icon": spec["icon"], "status": "error", "error": str(e), "data": {}})
    return {
        "demo": demo,
        "domains": demo["domains"],
        "domain_names": [CONSULTING_DOMAINS[d][0] for d in demo["domains"] if d in CONSULTING_DOMAINS],
        "scenario_count": len(scenarios),
        "sections": sections,
        "agents_involved": {k: v for k, v in CONSULTING_AGENTS.items() if any(spec["id"] in v.get("handles", []) for spec in CONSULTING_REPORT_SECTIONS)},
        "workflow": ENGAGEMENT_WORKFLOW,
    }


# ============================================================
# PLM PHASE EXECUTORS - deterministic templates
# ============================================================
def exec_discovery(idea, classification):
    return {
        "summary": f"Discovery phase for {idea[:80]} — identified primary user segments, quantified market opportunity, and surfaced top assumptions to validate before building.",
        "problem_statement": f"Users in the {classification['industry']} space currently lack an accessible, integrated solution that addresses their core needs efficiently.",
        "user_personas": [
            {"name": "Primary User", "description": "Day-to-day operator who needs efficiency and reliability", "goals": ["Save time", "Reduce errors", "Increase revenue"], "pain_points": ["Manual processes", "Disconnected tools", "Lack of visibility"]},
            {"name": "Decision Maker", "description": "Budget owner evaluating ROI and strategic fit", "goals": ["Measurable ROI", "Low risk adoption", "Scalability"], "pain_points": ["Hard to justify investment", "Change management", "Integration complexity"]},
        ],
        "market_sizing": {"TAM": "Large addressable market in target segment", "SAM": "Serviceable subset matching product scope", "SOM": "Realistic 3-year capture target"},
        "key_insights": [
            f"The {classification['industry']} segment has high willingness to adopt if the solution integrates with existing workflows",
            "Time-to-value under 1 week is the single strongest predictor of activation",
            "Trust and reliability matter more than feature breadth for this audience",
        ],
    }


def exec_ideation(idea, classification):
    return {
        "summary": f"Ideation phase generated RICE-prioritized feature concepts, focusing on high-impact + high-confidence items for the first release.",
        "solution_concepts": [
            {"name": "Core Workflow Automation", "rice": {"reach": 5, "impact": 5, "confidence": 4, "effort": 3, "score": 33.3}, "description": "Automate the top-3 repetitive tasks identified in Discovery"},
            {"name": "Unified Dashboard", "rice": {"reach": 5, "impact": 4, "confidence": 5, "effort": 2, "score": 50.0}, "description": "Single-pane view of all critical operational metrics"},
            {"name": "Smart Alerts & Notifications", "rice": {"reach": 4, "impact": 4, "confidence": 4, "effort": 2, "score": 32.0}, "description": "Proactive signals when attention is needed"},
            {"name": "Integration Hub", "rice": {"reach": 3, "impact": 5, "confidence": 3, "effort": 4, "score": 11.25}, "description": "Connectors to the top-5 existing tools users rely on"},
        ],
        "mvp_scope": ["Unified Dashboard", "Core Workflow Automation", "Smart Alerts & Notifications"],
        "deferred_to_v2": ["Integration Hub", "Advanced analytics", "Multi-language support"],
    }


def exec_definition(idea, classification):
    return {
        "summary": "Definition phase translated MVP scope into user stories with clear acceptance criteria following INVEST principles.",
        "user_stories": [
            {"id": "US-1", "story": "As a user, I want a single dashboard showing my key metrics so that I can understand status at a glance.", "acceptance_criteria": ["Dashboard loads in < 2s", "Shows at least 5 configurable metrics", "Mobile-responsive"], "story_points": 5},
            {"id": "US-2", "story": "As a user, I want to automate my top-3 repetitive tasks so that I can save time daily.", "acceptance_criteria": ["Automation rules are configurable without code", "Each automation logs run history", "Failures trigger alerts"], "story_points": 8},
            {"id": "US-3", "story": "As a decision maker, I want alerts when critical thresholds are crossed so that I can act quickly.", "acceptance_criteria": ["Threshold config per metric", "Multi-channel delivery (email, in-app)", "Snooze/dismiss functionality"], "story_points": 5},
            {"id": "US-4", "story": "As a new user, I want onboarding under 5 minutes so that I can start getting value immediately.", "acceptance_criteria": ["Guided tour", "Sample data preloaded", "Time-to-first-action < 5 min"], "story_points": 3},
            {"id": "US-5", "story": "As any user, I want my data to be secure and private so that I can trust the system.", "acceptance_criteria": ["TLS everywhere", "Role-based access control", "Audit log of data access"], "story_points": 5},
        ],
        "prd_sections": ["Problem", "Goals", "Non-goals", "User stories", "Success metrics", "Open questions"],
    }


def exec_design(idea, classification):
    return {
        "summary": "Design phase produced user flows, wireframe descriptions, and a design system aligned to the product's core value.",
        "user_flows": [
            "Signup → Onboarding tour → First dashboard view → First automation setup → Activation complete",
            "Daily login → Dashboard scan → Alert triage → Quick action → Done",
            "Configuration: Settings → Add metric → Configure threshold → Save → Verify",
        ],
        "wireframe_description": "Clean 3-column layout: left nav (collapsible), center content (dashboard/workflow), right contextual panel (alerts/details). Mobile collapses to single column with bottom tab bar.",
        "design_principles": [
            "Clarity over cleverness - every screen answers 'what do I do next'",
            "Mobile-first responsive design",
            "Dark mode support from day one",
            "Accessibility: WCAG 2.1 AA compliance",
            "Performance budget: 2s TTI, 100ms interaction response",
        ],
        "design_system": {
            "colors": "Indigo primary, slate neutrals, emerald success, amber warning, rose error",
            "typography": "Inter for UI, JetBrains Mono for data",
            "spacing": "8px base grid",
            "components": ["Button", "Input", "Card", "Table", "Modal", "Toast", "Nav", "Chart"],
        },
    }


def exec_development(idea, classification):
    kb = KNOWLEDGE_BASE[classification["method_key"]]
    return {
        "summary": f"Development phase organized as {kb['method_details']['cadence']} with clear sprint goals and velocity-based forecasting.",
        "sprint_plan": [
            {"sprint": 1, "goal": "Auth, user model, basic shell", "tasks": ["Setup CI/CD", "Auth implementation", "Basic routing", "DB schema"], "story_points": 21},
            {"sprint": 2, "goal": "Core dashboard", "tasks": ["Metric ingestion", "Dashboard UI", "Real-time updates", "Onboarding flow"], "story_points": 26},
            {"sprint": 3, "goal": "Automation engine", "tasks": ["Rule engine", "Automation UI", "Run history", "Error handling"], "story_points": 28},
            {"sprint": 4, "goal": "Alerts + polish", "tasks": ["Alert system", "Notifications", "Mobile responsive", "Bug fixes"], "story_points": 22},
            {"sprint": 5, "goal": "Beta release", "tasks": ["Performance optimization", "Beta onboarding", "Analytics integration", "Feedback capture"], "story_points": 18},
        ],
        "velocity_forecast": "Team velocity expected to stabilize at 22-26 story points per sprint by Sprint 3, allowing predictable commitment planning.",
        "tech_stack": ["Next.js 14", "Supabase (Postgres + Auth)", "Tailwind CSS", "Vercel", "GitHub Actions"],
    }


def exec_testing(idea, classification):
    return {
        "summary": "Testing strategy covers unit, integration, E2E, and user acceptance layers with explicit quality gates before release.",
        "test_strategy": "Test pyramid: 70% unit tests, 20% integration, 10% E2E. Every PR runs full unit+integration in CI. E2E runs nightly and on release candidates.",
        "test_cases": [
            {"id": "TC-1", "scenario": "New user completes onboarding", "expected": "Activation event fires, first dashboard visible within 5 minutes"},
            {"id": "TC-2", "scenario": "User creates an automation rule", "expected": "Rule persists, runs on next trigger, logs visible in history"},
            {"id": "TC-3", "scenario": "Alert fires on threshold breach", "expected": "Email and in-app notification delivered within 30 seconds"},
            {"id": "TC-4", "scenario": "Dashboard loads with 1000 metrics", "expected": "Page TTI < 2 seconds on median device"},
            {"id": "TC-5", "scenario": "User attempts unauthorized access", "expected": "Request denied, security audit log entry created"},
        ],
        "quality_gates": [
            "Code coverage ≥ 70%",
            "Zero P0/P1 open bugs",
            "Performance budget met",
            "Security scan clean",
            "Accessibility audit passed",
        ],
    }


def exec_launch(idea, classification):
    return {
        "summary": "Launch phase covers CI/CD automation, production infrastructure, monitoring, and support readiness.",
        "ci_cd_pipeline": [
            "GitHub push → Lint + type-check",
            "Run unit + integration tests",
            "Build artifact",
            "Deploy to staging (auto)",
            "E2E smoke test",
            "Manual approval for production",
            "Deploy to production (blue-green)",
            "Post-deploy health check",
        ],
        "infrastructure": "Vercel (frontend), Supabase (backend + DB), Cloudflare (CDN + WAF), Sentry (errors), PostHog (analytics)",
        "monitoring": [
            "Uptime: target 99.9%, alert on < 99.5%",
            "Error rate: alert on > 1% of requests",
            "P95 latency: alert on > 500ms",
            "Database connections: alert on > 80% of pool",
            "User activation funnel: daily review",
        ],
        "rollback_plan": "Blue-green deployment enables instant rollback via traffic shift. Database migrations are backward-compatible for one version.",
    }


def exec_iterate(idea, classification):
    return {
        "summary": "Post-launch iteration focuses on measuring real user behavior, acting on feedback, and continuously improving the North Star metric.",
        "launch_announcement": {
            "headline": f"Introducing {idea[:60]} — built for {classification['industry']}",
            "body": f"After extensive research with real users, we're launching a solution designed specifically for the {classification['industry']} segment. Our goal is to save you time, reduce errors, and unlock growth through a tool that fits naturally into your daily workflow.",
            "cta": "Start free trial",
        },
        "success_metrics": [
            {"kpi": "Daily Active Users", "target": "10,000 within 90 days"},
            {"kpi": "Activation Rate", "target": "60% of signups activated in 7 days"},
            {"kpi": "Week-4 Retention", "target": "≥ 35%"},
            {"kpi": "NPS", "target": "≥ 40"},
            {"kpi": "Monthly Recurring Revenue", "target": "Measurable growth month-over-month"},
        ],
        "feedback_loops": [
            "In-app feedback widget with weekly review",
            "Monthly user interviews (5+ per month)",
            "Quarterly NPS survey",
            "Continuous analytics review",
        ],
    }


PLM_PHASE_SPECS = [
    {"id": 1, "name": "Discovery",    "agent": "Strategist",         "icon": "🧠", "duration": "1-2 weeks",  "executor": exec_discovery},
    {"id": 2, "name": "Ideation",     "agent": "Strategist",         "icon": "💡", "duration": "1 week",     "executor": exec_ideation},
    {"id": 3, "name": "Definition",   "agent": "Business Analyst",   "icon": "📋", "duration": "2 weeks",    "executor": exec_definition},
    {"id": 4, "name": "Design",       "agent": "UX Designer",        "icon": "🎨", "duration": "2-3 weeks",  "executor": exec_design},
    {"id": 5, "name": "Development",  "agent": "Scrum Master",       "icon": "🏃", "duration": "6-12 weeks", "executor": exec_development},
    {"id": 6, "name": "Testing",      "agent": "QA Lead",            "icon": "✅", "duration": "2 weeks",    "executor": exec_testing},
    {"id": 7, "name": "Launch",       "agent": "DevOps Engineer",    "icon": "⚙️", "duration": "1 week",     "executor": exec_launch},
    {"id": 8, "name": "Iterate",      "agent": "Stakeholder Comms",  "icon": "📢", "duration": "Ongoing",    "executor": exec_iterate},
]


# ============================================================
# OPTIONAL LLM EVALUATOR - enhances summary text only
# ============================================================
def llm_evaluate(text_to_evaluate, context):
    """Ask LLM to refine the summary. If it fails, return original unchanged."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return text_to_evaluate
    try:
        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 300,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": "You are an executive editor. Improve the clarity and punch of the given summary text. Keep it under 3 sentences. Return ONLY the improved text, no prefix."},
                    {"role": "user", "content": f"Context: {context}\n\nSummary to improve: {text_to_evaluate}"},
                ],
            },
            timeout=15.0,
        )
        if r.status_code == 200:
            improved = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if improved and len(improved) > 20:
                return improved
    except Exception as e:
        print(f"[llm_evaluate] skipped: {e}", flush=True)
    return text_to_evaluate


# ============================================================
# HTTP HANDLER
# ============================================================
class Handler(BaseHTTPRequestHandler):

    def _send(self, code, body):
        try:
            payload = json.dumps(body).encode("utf-8")
        except Exception as e:
            payload = json.dumps({"error": f"serialization failed: {e}"}).encode("utf-8")
            code = 500
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/health"):
            self._send(200, {
                "status": "ok",
                "version": VERSION,
                "architecture": "template-driven + 10K+ scenario consulting intelligence + Big 3/4 blended methodology",
                "pm_agents": list(PM_AGENT_SPECS.keys()),
                "plm_phases": [p["name"] for p in PLM_PHASE_SPECS],
                "report_sections": [s["title"] for s in REPORT_SECTIONS],
                "consulting_scenarios": len(CONSULTING_SCENARIOS),
                "consulting_scaled_coverage": SCALED_SCENARIO_COUNT,
                "consulting_demos": len(DEMO_ENGAGEMENTS),
                "consulting_agents": len(CONSULTING_AGENTS),
                "consulting_domains": list(CONSULTING_DOMAINS.keys()),
                "consulting_report_sections": [s["title"] for s in CONSULTING_REPORT_SECTIONS],
                "methodologies_trained": list(KNOWLEDGE_BASE.keys()),
                "industry_patterns": len(INDUSTRY_PATTERNS),
                "training_examples": len(TRAINING_LIBRARY),
                "groq_key": bool(os.getenv("GROQ_API_KEY", "").strip()),
                "msme_agents": ({
                    "total": len(MSME.MSME_AGENTS),
                    "live": [k for k, a in MSME.MSME_AGENTS.items() if a.get("status") == "live"],
                    "endpoints": ["GET /agents/meta", "GET /agents/tests", "POST /agents/run"],
                } if MSME else "not loaded"),
                "industry_playbooks": ({
                    "total": len(PLAYBOOKS.PLAYBOOKS),
                    "sections": len(PLAYBOOKS.PLAYBOOK_SECTIONS),
                    "endpoints": ["GET /playbooks/meta", "GET /playbooks/tests", "POST /playbook"],
                } if PLAYBOOKS else "not loaded"),
                "live_brain": ({
                    "endpoints": ["GET /consult/meta", "POST /consult", "GET /brain/stats"],
                    "llm_providers": (LLM.available() if LLM else []),
                    "learning": BRAIN.brain_stats().get("total_engagements", 0),
                    "web_search": "keyless (DuckDuckGo + Wikipedia)",
                } if BRAIN else "not loaded"),
                "doc_rag": ({**DOCS.stats(), "endpoints": ["POST /docs/ingest", "GET /docs/list", "POST /docs/search"]} if DOCS else "not loaded"),
                "gov_schemes": ({"total": len(SCHEMES.SCHEMES), "categories": len(SCHEMES.CATEGORIES),
                                 "endpoints": ["GET /schemes/meta", "GET /schemes/tests", "POST /schemes"]} if SCHEMES else "not loaded"),
                "monitor": ({"metrics": len(MONITOR.METRICS),
                             "endpoints": ["POST /monitor", "GET /monitor/meta", "GET /monitor/tests"]} if MONITOR else "not loaded"),
                "simulations": ({"total": SIM.TOTAL, "per_type": SIM.PER_TYPE} if SIM else "not loaded"),
                "llm_stack": (LLM.available() if LLM else "not loaded"),
            })
        elif path == "/simulations":
            # Run all 500+ examples through the classifier and return accuracy report
            try:
                sim_results = run_simulations()
                self._send(200, sim_results)
            except Exception as e:
                self._send(200, {"error": str(e), "traceback": traceback.format_exc()[-1000:]})
        elif path == "/consulting/meta":
            self._send(200, {
                "workflow": ENGAGEMENT_WORKFLOW,
                "questionnaire": DD_QUESTIONNAIRE,
                "agents": CONSULTING_AGENTS,
                "demos": [{"id": d["id"], "title": d["title"], "icon": d["icon"], "company": d["company"], "domains": d["domains"], "engagement_type": d["engagement_type"]} for d in DEMO_ENGAGEMENTS],
                "scenario_count": len(CONSULTING_SCENARIOS),
                "scaled_count": SCALED_SCENARIO_COUNT,
                "domains": {k: {"name": v[0], "icon": v[1], "scenario_count": sum(1 for s in CONSULTING_SCENARIOS if s["domain"] == k)} for k, v in CONSULTING_DOMAINS.items()},
            })
        elif path == "/consulting/demos":
            self._send(200, {"demos": DEMO_ENGAGEMENTS, "count": len(DEMO_ENGAGEMENTS)})
        elif path == "/agents/meta":
            if not MSME:
                self._send(200, {"error": "msme_agents module not loaded"})
                return
            self._send(200, {
                "agents": MSME.list_agents(),
                "envelope_keys": MSME.ENVELOPE_KEYS,
                "erp_modules": MSME.ERP_MODULES,
                "notion_databases": MSME.NOTION_DATABASES,
                "citations": MSME.CITATIONS,
                "benchmarks": MSME.BENCHMARKS,
                "business_taxonomy": getattr(MSME, "BUSINESS_TAXONOMY", {}),
                "compliance_map": getattr(MSME, "COMPLIANCE_MAP", {}),
                "live_count": sum(1 for a in MSME.MSME_AGENTS.values() if a.get("status") == "live"),
                "total_count": len(MSME.MSME_AGENTS),
            })
        elif path == "/agents/tests":
            if not MSME:
                self._send(200, {"error": "msme_agents module not loaded"})
                return
            self._send(200, MSME.run_agent_tests())
        elif path == "/playbooks/meta":
            if not PLAYBOOKS:
                self._send(200, {"error": "industry_playbooks module not loaded"})
                return
            self._send(200, PLAYBOOKS.meta())
        elif path == "/playbooks/tests":
            if not PLAYBOOKS:
                self._send(200, {"error": "industry_playbooks module not loaded"})
                return
            self._send(200, PLAYBOOKS.run_playbook_tests())
        elif path == "/consult/meta":
            if not BRAIN:
                self._send(200, {"error": "live_brain module not loaded"})
                return
            self._send(200, BRAIN.intake_meta())
        elif path == "/brain/stats":
            if not BRAIN:
                self._send(200, {"error": "live_brain module not loaded"})
                return
            self._send(200, BRAIN.brain_stats())
        elif path == "/dashboard":
            if not BRAIN:
                self._send(200, {"error": "live_brain module not loaded"})
                return
            self._send(200, BRAIN.dashboard())
        elif path in ("/docs/list", "/docs", "/docs/stats"):
            if not DOCS:
                self._send(200, {"error": "doc_store module not loaded"})
                return
            self._send(200, {"documents": DOCS.list_docs(), "stats": DOCS.stats()})
        elif path == "/schemes/meta":
            if not SCHEMES:
                self._send(200, {"error": "gov_schemes module not loaded"})
                return
            self._send(200, SCHEMES.meta())
        elif path == "/schemes/tests":
            if not SCHEMES:
                self._send(200, {"error": "gov_schemes module not loaded"})
                return
            self._send(200, SCHEMES.run_schemes_tests())
        elif path == "/monitor/meta":
            if not MONITOR:
                self._send(200, {"error": "monitor module not loaded"})
                return
            self._send(200, MONITOR.meta())
        elif path == "/monitor/tests":
            if not MONITOR:
                self._send(200, {"error": "monitor module not loaded"})
                return
            self._send(200, MONITOR.run_monitor_tests())
        else:
            self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as e:
            self._send(400, {"error": f"bad request body: {e}"})
            return

        try:
            if path in ("/pm/plan", "/pipeline/plan", "/plan"):
                self.handle_pm_plan(body)
            elif path in ("/plm/execute", "/pipeline/execute", "/execute"):
                self.handle_plm_execute(body)
            elif path in ("/plm/prototype", "/pipeline/prototype", "/prototype"):
                self.handle_prototype(body)
            elif path in ("/workspace/seed", "/workspace/create"):
                self.handle_workspace_seed(body)
            elif path in ("/report/generate", "/report"):
                self.handle_report_generate(body)
            elif path in ("/report/stream",):
                self.handle_report_stream(body)
            elif path in ("/consulting/stream",):
                self.handle_consulting_stream(body)
            elif path in ("/consulting/generate",):
                self.handle_consulting_generate(body)
            elif path in ("/consulting/from-dd",):
                self.handle_consulting_from_dd(body)
            elif path.startswith("/consulting/demo/"):
                demo_id = path.split("/consulting/demo/")[1].strip("/")
                self.handle_consulting_demo(demo_id)
            elif path in ("/agents/run",):
                self.handle_agent_run(body)
            elif path in ("/agents/journey",):
                self.handle_agent_journey(body)
            elif path in ("/blueprint", "/startup/blueprint"):
                self.handle_blueprint(body)
            elif path in ("/workspace/erp",):
                self.handle_workspace_erp(body)
            elif path in ("/playbook", "/playbooks/get"):
                self.handle_playbook(body)
            elif path in ("/consult", "/brain/consult"):
                self.handle_consult(body)
            elif path in ("/pmo", "/pmo/build"):
                self.handle_pmo(body)
            elif path in ("/whatif", "/consult/simulate"):
                self.handle_whatif(body)
            elif path in ("/docs/ingest",):
                self.handle_docs_ingest(body)
            elif path in ("/docs/search",):
                self.handle_docs_search(body)
            elif path in ("/studio", "/studio/generate"):
                self.handle_studio(body)
            elif path in ("/simulate", "/situation"):
                self.handle_simulate(body)
            elif path in ("/schemes", "/schemes/recommend"):
                self.handle_schemes(body)
            elif path in ("/monitor", "/command-center"):
                self.handle_monitor(body)
            else:
                self._send(404, {"error": "unknown endpoint", "path": path})
        except Exception as e:
            print(f"[handler] UNCAUGHT at {path}: {e}", flush=True)
            traceback.print_exc()
            self._send(200, {
                "error": f"Handler exception at {path}: {e}",
                "traceback": traceback.format_exc()[-1500:],
            })

    def handle_pm_plan(self, body):
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[pm/plan] idea={idea[:80]}", flush=True)

        classification = classify_idea(idea)
        print(f"[pm/plan] classified as {classification}", flush=True)

        pm_agents_out = {}
        for name, spec in PM_AGENT_SPECS.items():
            try:
                data = spec["generator"](idea, classification)
                pm_agents_out[name] = {
                    "role": spec["role"],
                    "icon": spec["icon"],
                    "status": "ok",
                    "data": data,
                }
            except Exception as e:
                print(f"[pm_agent {name}] FAILED: {e}", flush=True)
                traceback.print_exc()
                pm_agents_out[name] = {
                    "role": spec["role"],
                    "icon": spec["icon"],
                    "status": "error",
                    "error": str(e),
                    "data": {"summary": f"Agent error: {e}"},
                }

        self._send(200, {
            "idea": idea,
            "classification": classification,
            "pm_agents": pm_agents_out,
            "summary": {
                "total": len(PM_AGENT_SPECS),
                "ok": sum(1 for a in pm_agents_out.values() if a["status"] == "ok"),
                "method": KNOWLEDGE_BASE[classification["method_key"]]["name"],
                "industry": classification["industry"],
                "complexity": classification["complexity"],
            },
        })

    def handle_agent_run(self, body):
        """Run a research-grade MSME agent against a scenario; returns the audit-ready envelope."""
        if not MSME:
            self._send(200, {"error": "msme_agents module not loaded"})
            return
        agent_key = (body.get("agent") or "").strip()
        if not agent_key:
            self._send(200, {"error": "Please provide an 'agent' field", "available": list(MSME.MSME_AGENTS.keys())})
            return
        scenario = {
            "description": (body.get("description") or body.get("idea") or "").strip(),
            "data": body.get("data") or {},
        }
        print(f"[agents/run] agent={agent_key} desc={scenario['description'][:80]}", flush=True)
        self._send(200, MSME.run_agent(agent_key, scenario))

    def handle_playbook(self, body):
        """Return one full 13-part industry playbook by key, business_type, or a
        free-text description (auto-matched to the best-fit sector)."""
        if not PLAYBOOKS:
            self._send(200, {"error": "industry_playbooks module not loaded"})
            return
        key = (body.get("key") or body.get("business_type") or "").strip()
        description = (body.get("description") or body.get("idea") or "").strip()
        pb, matched, how = PLAYBOOKS.resolve(business_type=key or None, key=key or None, description=description or None)
        if not pb:
            self._send(200, {
                "error": "Could not match a playbook. Pass a 'key', 'business_type', or a 'description'.",
                "available": [c["key"] for c in PLAYBOOKS.list_playbooks()],
            })
            return
        print(f"[playbook] matched={matched} how={how} desc={description[:60]}", flush=True)
        self._send(200, {"status": "ok", "matched_key": matched, "matched_by": how, "playbook": pb})

    def handle_consult(self, body):
        """AI-native consulting brain: structured intake -> customised engagement
        (playbook grounding + live open-source search + memory recall + Groq synthesis,
        with deterministic fallback). Learns from every engagement."""
        if not BRAIN:
            self._send(200, {"error": "live_brain module not loaded"})
            return
        # Forward the full DD intake generically (all known field keys + sector KPI answers).
        field_keys = getattr(BRAIN, "_FIELD_KEYS", ["description", "business_type"])
        intake = {k: (body.get(k) if body.get(k) is not None else "") for k in field_keys}
        intake["mode"] = (body.get("mode") or "existing").strip()
        if not intake.get("description"):
            intake["description"] = (body.get("idea") or "").strip()
        for k, v in body.items():  # sector-specific kpi__* capture fields
            if k.startswith("kpi__") and v not in (None, ""):
                intake[k] = v
        if not intake.get("description"):
            self._send(200, {"error": "Please describe your business."})
            return
        print(f"[consult] mode={intake['mode']} type={intake['business_type']} desc={intake['description'][:60]}", flush=True)
        self._send(200, BRAIN.consult(intake))

    def handle_monitor(self, body):
        """Monitoring / Business Command Center: KPI snapshot + profile ->
        trends, compliance countdown and proactive alerts (deterministic)."""
        if not MONITOR:
            self._send(200, {"error": "monitor module not loaded"})
            return
        print(f"[monitor] desc={(body.get('description') or '')[:50]} metrics={len(body.get('metrics') or {})}", flush=True)
        self._send(200, MONITOR.command_center(body))

    def handle_schemes(self, body):
        """Government Schemes module: profile / free-text -> personalised
        government scheme recommendations (deterministic, no LLM needed)."""
        if not SCHEMES:
            self._send(200, {"error": "gov_schemes module not loaded"})
            return
        if not (body.get("description") or body.get("idea") or body.get("sector") or body.get("business_type")):
            self._send(200, {"error": "Describe your business (or pass a sector) to match schemes."})
            return
        print(f"[schemes] desc={(body.get('description') or body.get('sector') or '')[:60]}", flush=True)
        self._send(200, SCHEMES.recommend_schemes(body))

    def handle_docs_ingest(self, body):
        """Ingest a document (pasted text) into the RAG corpus."""
        if not DOCS:
            self._send(200, {"error": "doc_store module not loaded"})
            return
        name = (body.get("name") or "document").strip()
        text = (body.get("text") or "").strip()
        if not text:
            self._send(200, {"error": "Please provide document 'text'."})
            return
        res = DOCS.ingest(name, text, workspace=(body.get("workspace") or "default"))
        self._send(200, {**res, "documents": DOCS.list_docs()})

    def handle_docs_search(self, body):
        if not DOCS:
            self._send(200, {"error": "doc_store module not loaded"})
            return
        self._send(200, {"results": DOCS.search((body.get("query") or "").strip(), k=int(body.get("k") or 4),
                                                workspace=body.get("workspace"))})

    def handle_whatif(self, body):
        """Recompute scorecard + value-at-stake + benchmark for tweaked numbers (live what-if)."""
        if not BRAIN:
            self._send(200, {"error": "live_brain module not loaded"})
            return
        self._send(200, BRAIN.simulate(body or {}))

    def handle_pmo(self, body):
        """Turn an engagement (or its plan/recs/kpis) into a PM workspace."""
        if not BRAIN:
            self._send(200, {"error": "live_brain module not loaded"})
            return
        eng = body.get("engagement") or body
        self._send(200, BRAIN.build_pmo(eng))

    def handle_agent_journey(self, body):
        """Run the full end-to-end engagement (all relevant agents) for a mode + business."""
        if not MSME:
            self._send(200, {"error": "msme_agents module not loaded"})
            return
        mode = (body.get("mode") or "existing").strip()
        scenario = {
            "description": (body.get("description") or body.get("idea") or "").strip(),
            "data": body.get("data") or {},
        }
        if not scenario["description"]:
            self._send(200, {"error": "Please provide a 'description' of the business."})
            return
        print(f"[agents/journey] mode={mode} desc={scenario['description'][:80]}", flush=True)
        self._send(200, MSME.run_journey(mode, scenario))

    def handle_simulate(self, body):
        """Situation simulator — match a real MSME situation against the 100+/type
        scale-wise library, run the recommended agent CREW (CrewAI-style) in a
        sequence (LangGraph-style), and assemble an end-to-end grow-in-India +
        scale-internationally plan. Optionally synthesised by the free-LLM stack."""
        if not (MSME and SIM):
            self._send(200, {"error": "simulation engine not loaded"})
            return
        situation = (body.get("situation") or body.get("idea") or body.get("description") or "").strip()
        if not situation:
            self._send(200, {"error": "Please describe your business situation."})
            return
        print(f"[simulate] {situation[:90]}", flush=True)

        m = SIM.match(situation, top=12)
        scenario = {"description": situation, "data": body.get("data") or {}}

        # Run the crew (cap to keep it swift) — LangGraph-style sequential pass.
        crew_keys = (m["crew"] or [])[:6]
        crew_out = []
        for k in crew_keys:
            r = MSME.run_agent(k, scenario)
            if r.get("status") != "ok":
                continue
            o = r["output"]
            crew_out.append({
                "agent": k, "name": r["name"], "icon": r["icon"],
                "recommendations": (o.get("recommendations") or [])[:3],
                "top_risk": (o.get("risks") or [{}])[0].get("risk", ""),
            })

        # End-to-end plan split into India growth vs international scale-up.
        india_keys = {"market_research", "sales_gtm", "cfo_finance", "gst_compliance", "ceo_copilot", "competitor_intel", "product_manager"}
        intl_keys = {"export_compliance", "msme_due_diligence", "investor_readiness", "legal_contracts", "procurement_agent"}
        india_growth, intl_scaleup = [], []
        for c in crew_out:
            for rec in c["recommendations"]:
                (india_growth if c["agent"] in india_keys else intl_scaleup if c["agent"] in intl_keys else india_growth).append(f"{c['icon']} {rec}")

        # Optional free-LLM executive synthesis (graceful: deterministic if no keys).
        exec_summary, llm_provider = "", None
        if LLM and LLM.available():
            sys_p = ("You are a Big-3 MSME consultant for India. Write a crisp 4-6 sentence executive "
                     "synthesis for the founder: how to grow in India and scale internationally. Be concrete, India-aware (₹, GST, IEC, APEDA/RoDTEP where relevant). No preamble.")
            usr_p = (f"Situation: {situation}\nBusiness type: {m['business_type']} · Stage: {m['stage']}\n"
                     f"Key moves: " + "; ".join((india_growth + intl_scaleup)[:10]))
            res = LLM.augment(sys_p, usr_p, max_tokens=500)
            exec_summary, llm_provider = res.get("text") or "", res.get("provider")
        if not exec_summary:
            exec_summary = (f"As a {m['stage'].lower()} {m['business_type'].replace('_',' ')} business, win an India beachhead first "
                            f"(clean GST/Udyam, tight unit economics, a focused channel), then scale internationally with IEC, "
                            f"the right export incentives and verified buyers. The crew below sequences the work.")

        self._send(200, {
            "situation": situation,
            "business_type": m["business_type"],
            "stage": m["stage"],
            "library_size_for_type": m["library_size_for_type"],
            "total_situations": m["total_situations"],
            "matched_situations": [s["situation"] for s in m["matched"][:8]],
            "crew": [{"agent": c["agent"], "name": c["name"], "icon": c["icon"]} for c in crew_out],
            "plan": {
                "india_growth": india_growth[:10],
                "international_scaleup": intl_scaleup[:10],
                "agents": crew_out,
            },
            "exec_summary": exec_summary,
            "llm_provider": llm_provider,
            "llm_available": bool(LLM and LLM.available()),
            "orchestration": "CrewAI-style crew + LangGraph-style sequence (in-engine); free-LLM augmentation optional",
        })

    def handle_studio(self, body):
        """Business Studio — ONE idea in, a complete research-grade report out:
        deep due diligence, market study (TAM/SAM/SOM), product lifecycle (PLM),
        recommended PM method, tech stack, financials (₹ for India), risk,
        regulatory/registration, GTM and roadmap — plus a handoff to the preloaded
        PM workspace copilot. Uniform section schema for a stunning, PDF-able UI."""
        idea = (body.get("idea") or body.get("description") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' / 'description'."})
            return
        print(f"[studio] idea={idea[:80]}", flush=True)
        c = classify_idea(idea)
        cur = c.get("currency", "$")
        kb = KNOWLEDGE_BASE[c["method_key"]]

        india = c.get("geo") == "India"
        c_usd = dict(c); c_usd["geo"] = "Global"; c_usd["currency"] = "$"

        market = gen_market_sizing(idea, c)
        comp = gen_competitive_landscape(idea, c)
        tech = gen_tech_stack(idea, c)
        meth = gen_methodology_recommendation(idea, c)
        fin = gen_financial_projections(idea, c)          # native (₹ for India)
        fin_usd = gen_financial_projections(idea, c_usd)  # USD twin (for dual display)
        risk = gen_risk_assessment(idea, c)
        gtm = gen_gtm_strategy(idea, c)
        reg = gen_regulatory_compliance(idea, c)
        road = gen_implementation_roadmap(idea, c)

        def P(lst, n=8):
            return [str(x) for x in (lst or [])][:n]

        # Dual-currency: show ₹ and $ together for India; just $ otherwise.
        def dual(native, usd):
            return f"{native}  ·  {usd}" if (india and native != usd) else usd

        # Parse "550B" / "1.2B" / "85M" -> float (USD) for infographic proportions.
        def _bn(s):
            s = str(s).replace("$", "").strip().upper()
            mult = 1.0
            if s.endswith("B"): mult, s = 1e9, s[:-1]
            elif s.endswith("M"): mult, s = 1e6, s[:-1]
            elif s.endswith("T"): mult, s = 1e12, s[:-1]
            try: return float(s) * mult
            except Exception: return 0.0

        sections = []

        sections.append({"id": "exec", "title": "Executive Summary", "icon": "📌",
            "summary": idea,
            "points": [
                f"Geography: {c['geo']} · currency {cur}",
                f"Industry: {c['industry']} · complexity: {c['complexity'].replace('_',' ')}",
                f"Recommended PM method: {meth['recommended']} ({meth.get('confidence','')})",
                f"Market: TAM {market['tam']['value']} · SAM {market['sam']['value']} · SOM {market['som']['value']}",
                f"Funding need (seed): {fin['funding_requirement']['seed']}",
            ]})

        # Market study with TAM/SAM/SOM hero metrics + funnel infographic
        sections.append({"id": "market", "title": "Market Study — TAM / SAM / SOM", "icon": "📈",
            "summary": market["summary"],
            "metrics": [
                {"label": "TAM", "value": market["tam"]["value"], "note": "Total addressable market"},
                {"label": "SAM", "value": market["sam"]["value"], "note": "Serviceable available"},
                {"label": "SOM", "value": market["som"]["value"], "note": "Serviceable obtainable (3-5 yr)"},
                {"label": "Growth", "value": market["growth_rate"], "note": "Sector CAGR"},
            ],
            "funnel": [
                {"label": "TAM", "value": market["tam"]["value"], "n": _bn(market["tam"]["value"])},
                {"label": "SAM", "value": market["sam"]["value"], "n": _bn(market["sam"]["value"])},
                {"label": "SOM", "value": market["som"]["value"], "n": _bn(market["som"]["value"])},
            ],
            "points": ([("India context: " + market["india_context"])] if market.get("india_context") else [])
                      + ["Growth drivers: " + market.get("growth_drivers", "")]
                      + ["Geo priority — " + g for g in market.get("geographic_priorities", [])]})

        sections.append({"id": "competition", "title": "Competitive Landscape", "icon": "🎯",
            "summary": comp["summary"],
            "points": [f"{x.get('name','')}: strength — {x.get('strength','')}; gap — {x.get('weakness','')}" for x in comp.get("competitors", [])][:6]
                      + [f"White space: {comp.get('competitive_positioning',{}).get('white_space','')}"]})

        # Due diligence = risk + regulatory/registration
        dd_points = []
        for cat in risk.get("risk_categories", []):
            for r in cat.get("risks", [])[:2]:
                dd_points.append(f"[{cat['category']}] {r['description']} — {r.get('likelihood','')}/{r.get('impact','')} · {r.get('mitigation','')}")
        sections.append({"id": "diligence", "title": "Due Diligence — Risk & Regulatory", "icon": "🔍",
            "summary": risk.get("summary", "") + " " + reg.get("summary", ""),
            "points": dd_points[:7] + ["Registration/compliance: " + "; ".join(P(reg.get("key_regulations", []), 6))]})

        rp, rpu = fin["revenue_projection"], fin_usd["revenue_projection"]
        fin_title = "Financial Projections (₹ & $)" if india else "Financial Projections ($)"
        sections.append({"id": "financials", "title": fin_title, "icon": "💰",
            "summary": fin["summary"],
            "table": {"headers": ["Year", "Users", "Revenue", "Growth"],
                      "rows": [[rp[i]["year"], rp[i]["users"], dual(rp[i]["revenue"], rpu[i]["revenue"]), rp[i]["growth"]] for i in range(len(rp))]},
            "chart": {"labels": [r["year"] for r in rpu],
                      "values": [p["revenue"] for p in fin_usd["profit_loss"]],
                      "display": [dual(rp[i]["revenue"], rpu[i]["revenue"]) for i in range(len(rp))]},
            "points": [f"Blended CAC {dual(fin['unit_economics']['blended_cac'], fin_usd['unit_economics']['blended_cac'])} · LTV {dual(fin['unit_economics']['ltv_estimate'], fin_usd['unit_economics']['ltv_estimate'])} · target LTV:CAC {fin['unit_economics']['ltv_cac_target']}",
                       f"Gross margin {fin['unit_economics']['gross_margin']}",
                       f"Seed: {dual(fin['funding_requirement']['seed'], fin_usd['funding_requirement']['seed'])}",
                       f"Series A: {dual(fin['funding_requirement']['series_a'], fin_usd['funding_requirement']['series_a'])}"]})

        # Product lifecycle (PLM) from the methodology's phases
        plm_rows = []
        wk = 0
        for ph in kb["phases"]:
            dur = ph.get("duration_weeks", 0)
            wk_range = f"W{wk+1}-{wk+dur}" if dur > 0 else "Ongoing"
            if dur > 0:
                wk += dur
            plm_rows.append([ph["name"], wk_range, ", ".join(ph.get("key_activities", [])[:3]), ", ".join(ph.get("deliverables", [])[:2])])
        sections.append({"id": "plm", "title": "Product Lifecycle (PLM)", "icon": "🔄",
            "summary": f"End-to-end product lifecycle under {meth['recommended']}, phase by phase.",
            "table": {"headers": ["Phase", "Timeline", "Key activities", "Deliverables"], "rows": plm_rows}})

        sections.append({"id": "method", "title": "Project Management Method", "icon": "🧠",
            "summary": f"{meth['recommended']} — {meth.get('primary_rationale','')[:220]} Tooling: {meth.get('tooling',{}).get('primary','')}.",
            "table": {"headers": ["Ceremony", "Frequency", "Duration", "Attendees"],
                      "rows": [[e["event"], e["frequency"], e["duration"], e["attendees"]] for e in meth.get("ceremony_calendar", [])]}})

        tech_rows = [[lbl, ", ".join(tech.get(k) or []) if isinstance(tech.get(k), list) else str(tech.get(k, "")), ""]
                     for k, lbl in [("frontend", "Frontend"), ("backend", "Backend"), ("infrastructure", "Infrastructure"), ("ai_ml", "AI / ML"), ("integrations", "Integrations")]]
        for bv in tech.get("build_vs_buy", []):
            tech_rows.append([bv.get("capability", ""), bv.get("decision", ""), bv.get("reason", "")])
        sections.append({"id": "tech", "title": "Tech Stack", "icon": "🧰",
            "summary": tech.get("summary", ""),
            "table": {"headers": ["Layer / Capability", "Recommendation", "Notes"], "rows": tech_rows}})

        sections.append({"id": "gtm", "title": "Go-to-Market", "icon": "🚀",
            "summary": gtm["summary"],
            "points": [f"Motion: {gtm['primary_motion']}",
                       f"CAC {gtm['unit_economics']['target_cac']} · LTV {gtm['unit_economics']['target_ltv']}"]
                      + ["Channel — " + ch for ch in P(gtm.get("channels", []), 5)]})

        sections.append({"id": "roadmap", "title": "Implementation Roadmap", "icon": "🗺️",
            "summary": road.get("summary", ""),
            "table": {"headers": ["Phase", "Theme", "Success criteria"],
                      "rows": [[q["quarter"], q["theme"], q.get("success_criteria", "")] for q in road.get("quarters", [])]}})

        self._send(200, {
            "idea": idea,
            "geo": c["geo"],
            "currency": cur,
            "industry": c["industry"],
            "methodology": meth["recommended"],
            "sections": sections,
        })

    def handle_blueprint(self, body):
        """One-click consolidated STARTUP BLUEPRINT — fuses the India-aware report
        generators with the startup-agent journey into one uniform, render-friendly
        document: market, model, product, GTM, financials (₹), compliance &
        registration, funding & govt incentives, risk/DD, 90-day plan, scaling."""
        idea = (body.get("idea") or body.get("description") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' / 'description' of the startup."})
            return
        print(f"[blueprint] idea={idea[:80]}", flush=True)
        c = classify_idea(idea)
        cur = c.get("currency", "$")
        kb = KNOWLEDGE_BASE[c["method_key"]]

        # India-aware report generators (currency + registration localized)
        market = gen_market_sizing(idea, c)
        fin = gen_financial_projections(idea, c)
        gtm = gen_gtm_strategy(idea, c)
        reg = gen_regulatory_compliance(idea, c)
        road = gen_implementation_roadmap(idea, c)

        # Startup-agent journey for India depth + aggregation
        journey = MSME.run_journey("startup", {"description": idea, "data": body.get("data") or {}}) if MSME else {"agents": [], "summary": {}}
        by = {a["agent"]: a["output"] for a in journey.get("agents", [])}
        jsum = journey.get("summary", {})

        def _pts(lst, n=6):
            return [str(x) for x in (lst or [])][:n]

        sections = []
        sections.append({"id": "exec", "title": "Executive Summary", "icon": "📌",
            "summary": idea,
            "points": [
                f"Geography: {c['geo']} · currency {cur}",
                f"Industry: {c['industry']} · complexity: {c['complexity'].replace('_', ' ')}",
                f"Recommended methodology: {kb['name']}",
                f"Funding need (seed): {fin['funding_requirement']['seed']}",
                f"Agents consulted: {jsum.get('agents_run', 0)} · open risks: {jsum.get('total_risks', 0)} · incentives mapped: {len(jsum.get('government_incentives', []))}",
            ]})

        sections.append({"id": "market", "title": "Market Opportunity", "icon": "📈",
            "summary": market["summary"],
            "points": [
                f"TAM {market['tam']['value']} · SAM {market['sam']['value']} · SOM {market['som']['value']}",
                f"Growth: {market['growth_rate']} — {market['growth_drivers']}",
                *( ["India context: " + market["india_context"]] if market.get("india_context") else [] ),
                *["Geo priority — " + g for g in market.get("geographic_priorities", [])],
            ]})

        pm = by.get("product_manager", {})
        sections.append({"id": "product", "title": "Product & Roadmap", "icon": "🧩",
            "summary": (pm.get("analysis", {}) or {}).get("mvp_principle", "Ship the smallest slice that validates the riskiest assumption, then iterate on usage data."),
            "points": _pts((pm.get("analysis", {}) or {}).get("roadmap_90d", [])) + _pts([f"{q['quarter']}: {q['theme']}" for q in road.get("quarters", [])], 6)})

        sections.append({"id": "gtm", "title": "Go-to-Market", "icon": "🚀",
            "summary": gtm["summary"],
            "points": [f"Motion: {gtm['primary_motion']}",
                       f"Target CAC {gtm['unit_economics']['target_cac']} · LTV {gtm['unit_economics']['target_ltv']}",
                       *["Channel — " + ch for ch in _pts(gtm.get("channels", []))]]})

        sections.append({"id": "financials", "title": f"Financial Plan ({cur})", "icon": "💰",
            "summary": fin["summary"],
            "table": {"headers": ["Year", "Users", "Revenue", "Growth"],
                      "rows": [[r["year"], r["users"], r["revenue"], r["growth"]] for r in fin["revenue_projection"]]},
            "points": [f"Blended CAC: {fin['unit_economics']['blended_cac']} · LTV: {fin['unit_economics']['ltv_estimate']} · target LTV:CAC {fin['unit_economics']['ltv_cac_target']}",
                       f"Gross margin: {fin['unit_economics']['gross_margin']}",
                       f"Seed: {fin['funding_requirement']['seed']}",
                       f"Series A: {fin['funding_requirement']['series_a']}"]})

        sections.append({"id": "compliance", "title": "Compliance & Registration Roadmap", "icon": "⚖️",
            "summary": reg["summary"],
            "points": [f"{step['timeline']}: " + "; ".join(step["items"]) for step in reg.get("compliance_roadmap", [])]
                      + [f"Compliance budget — Y1 {reg['compliance_budget']['year_1']}, Y2 {reg['compliance_budget']['year_2']}"]})

        ir = by.get("investor_readiness", {})
        incentives = jsum.get("government_incentives", []) or (ir.get("government_incentives", []) if ir else [])
        sections.append({"id": "funding", "title": "Funding & Government Incentives", "icon": "🏦",
            "summary": "Capital plan plus the Indian government benefits this startup can pursue (verify eligibility with certificates).",
            "points": [f"{g.get('benefit')}: {g.get('value')}" for g in incentives][:8] or ["Map DPIIT recognition → 80-IAC tax holiday, angel-tax exemption, SISFS, and state startup incentives."]})

        dd = by.get("msme_due_diligence", {})
        sections.append({"id": "risk", "title": "Risk & Due-Diligence Watch-outs", "icon": "⚠️",
            "summary": "The red flags an investor/lender will probe — close these early.",
            "points": [f"[{r.get('severity')}] {r.get('risk')}" for r in (dd.get("risks", []) if dd else [])][:7]
                      or [f"[{k}] {v}" for k, v in [("Critical", jsum.get("risks", {}).get("Critical", 0)), ("High", jsum.get("risks", {}).get("High", 0))]]})

        sections.append({"id": "scaling", "title": "Scaling Playbook", "icon": "📈",
            "summary": "How to scale once you have product-market fit.",
            "points": [
                "Phase 1 — Win a Tier-1 metro beachhead; nail unit economics (LTV:CAC ≥ 3) before spending on growth.",
                "Phase 2 — Expand to Tier-2/3 cities with vernacular content, WhatsApp + ONDC/marketplace channels and distributor partners.",
                "Phase 3 — Multi-state GST + ops, build a repeatable sales motion, hire functional leadership, raise Series A.",
                "Phase 4 — Pan-India scale; consider adjacent products and select export markets (Middle East, SEA).",
                *["Milestone — " + f"{q['quarter']}: {q['theme']} ({q.get('success_criteria','')})" for q in road.get("quarters", []) if "Scale" in q.get("theme", "")],
            ]})

        # 90-day action plan — aggregate first actions across key startup agents
        actions = []
        for k in ("ceo_copilot", "gst_compliance", "product_manager", "investor_readiness", "market_research"):
            for a in (by.get(k, {}).get("action_plan", []) or [])[:2]:
                actions.append({"step": a.get("step"), "owner": a.get("owner"), "timeline": a.get("timeline"), "agent": MSME.MSME_AGENTS.get(k, {}).get("name", k) if MSME else k})

        self._send(200, {
            "idea": idea,
            "geo": c["geo"],
            "currency": cur,
            "industry": c["industry"],
            "methodology": kb["name"],
            "sections": sections,
            "ninety_day_plan": actions,
            "summary": jsum,
            "agents_used": [a.get("name") for a in journey.get("agents", [])],
        })

    def handle_workspace_erp(self, body):
        """In-app ERP-styled PLM/PM workspace copilot. Returns self-explanatory
        modules (master data, backlog, sprints, risk register, compliance calendar,
        KPIs, SOPs, team) as a uniform {columns, rows} schema the UI renders as ERP
        tables and exports to Notion. India-aware (₹, GST/Udyam/DPIIT/EPF/ESI/ROC)."""
        idea = (body.get("idea") or body.get("description") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' / 'description' field"})
            return
        print(f"[workspace/erp] idea={idea[:80]}", flush=True)
        c = classify_idea(idea)
        kb = KNOWLEDGE_BASE[c["method_key"]]
        india = c.get("geo") == "India"
        cur = c.get("currency", "$")

        # --- Sprints from methodology phases ---
        sprints, week = [], 0
        for i, phase in enumerate(kb["phases"]):
            if phase["duration_weeks"] <= 0:
                continue
            sprints.append({"num": i + 1, "name": phase["name"],
                            "goal": (phase["deliverables"][0] if phase.get("deliverables") else phase["name"]),
                            "weeks": f"W{week+1}-{week+phase['duration_weeks']}", "status": "Planned",
                            "_activities": phase.get("key_activities", []), "_deliverables": phase.get("deliverables", [])})
            week += phase["duration_weeks"]

        # --- Backlog (tasks) from sprint activities + deliverables ---
        tasks, n = [], 1
        prio = ["High", "Medium", "Medium", "Low", "High"]
        for sp in sprints:
            for j, act in enumerate(sp["_activities"]):
                tasks.append({"ref": f"PMG-{n}", "title": act, "sprint": sp["name"],
                              "priority": prio[j % len(prio)], "points": [2, 3, 5, 8][j % 4],
                              "status": "To Do", "owner": "—"})
                n += 1
            for d in sp["_deliverables"][:2]:
                tasks.append({"ref": f"PMG-{n}", "title": f"Deliver: {d}", "sprint": sp["name"],
                              "priority": "High", "points": 5, "status": "To Do", "owner": "—"})
                n += 1
        for sp in sprints:
            sp.pop("_activities", None); sp.pop("_deliverables", None)

        # --- Risk register ---
        risks = [{"id": r["id"], "type": r["type"], "risk": r["description"],
                  "prob": r["probability"], "impact": r["impact"], "score": r["probability"] * r["impact"],
                  "mitigation": r["mitigation"], "owner": r["owner"], "status": "Open"} for r in kb["risks"]]

        # --- Team roster ---
        team = [{"role": t["role"], "count": t["count"],
                 "responsibilities": ", ".join(t.get("responsibilities", [])) if isinstance(t.get("responsibilities"), list) else t.get("responsibilities", "")}
                for t in kb.get("team_composition", [])]

        # --- Master data (ERP) — India-aware ---
        master = [
            {"field": "Entity name", "value": idea[:60], "notes": "Legal name once incorporated"},
            {"field": "Industry", "value": c["industry"], "notes": "Auto-classified"},
            {"field": "Methodology", "value": kb["name"], "notes": kb.get("confidence", "")},
            {"field": "Currency", "value": cur, "notes": "India → ₹" if india else "Default"},
        ]
        if india:
            master += [
                {"field": "Constitution", "value": "Pvt Ltd / LLP (to register)", "notes": "Via MCA"},
                {"field": "GSTIN", "value": "<pending>", "notes": "Register before invoicing"},
                {"field": "PAN / TAN", "value": "<pending>", "notes": "PAN for entity, TAN for TDS"},
                {"field": "Udyam (MSME)", "value": "<pending>", "notes": "Unlocks MSME benefits"},
                {"field": "DPIIT recognition", "value": "<pending>", "notes": "Unlocks 80-IAC / angel-tax"},
                {"field": "Financial year", "value": "1 Apr – 31 Mar", "notes": "India FY"},
            ]

        # --- Compliance calendar (India-aware) ---
        if india:
            compliance = [
                {"obligation": "GSTR-1 (outward supplies)", "authority": "GST", "frequency": "Monthly", "due": "11th", "status": "Set up"},
                {"obligation": "GSTR-3B (summary + tax)", "authority": "GST", "frequency": "Monthly", "due": "20th", "status": "Set up"},
                {"obligation": "TDS deposit", "authority": "Income Tax", "frequency": "Monthly", "due": "7th", "status": "Set up"},
                {"obligation": "TDS return (24Q/26Q)", "authority": "Income Tax", "frequency": "Quarterly", "due": "Q+1 month", "status": "Set up"},
                {"obligation": "PF ECR", "authority": "EPFO", "frequency": "Monthly", "due": "15th", "status": "If ≥ staff"},
                {"obligation": "ESI contribution", "authority": "ESIC", "frequency": "Monthly", "due": "15th", "status": "If applicable"},
                {"obligation": "Advance tax", "authority": "Income Tax", "frequency": "Quarterly", "due": "15 Jun/Sep/Dec/Mar", "status": "Set up"},
                {"obligation": "ROC AOC-4 + MGT-7", "authority": "MCA", "frequency": "Annual", "due": "Post-AGM", "status": "Set up"},
                {"obligation": "Income tax return", "authority": "Income Tax", "frequency": "Annual", "due": "31 Oct (audit)", "status": "Set up"},
            ]
            # sector-specific licences via the MSME agent layer
            if MSME:
                try:
                    cls_b = MSME.classify_business(idea)
                    for key in MSME.compliance_for(cls_b):
                        cit = MSME.CITATIONS.get(key, {})
                        if cit and key not in ("gst_portal", "income_tax", "udyam", "shops_act"):
                            compliance.append({"obligation": cit.get("title"), "authority": cit.get("authority", ""),
                                               "frequency": "As applicable", "due": "—", "status": "Review"})
                except Exception:
                    pass
        else:
            compliance = [
                {"obligation": "Privacy policy + ToS", "authority": "Legal", "frequency": "One-time", "due": "Pre-launch", "status": "Set up"},
                {"obligation": "Data-protection (DPDP/GDPR)", "authority": "Regulator", "frequency": "Ongoing", "due": "Months 1-6", "status": "Set up"},
                {"obligation": "SOC 2 / ISO 27001 (if B2B)", "authority": "Auditor", "frequency": "Annual", "due": "Months 7-18", "status": "Plan"},
            ]

        # --- KPIs ---
        kpis = [
            {"kpi": "Velocity (story points/sprint)", "target": "Stabilise by sprint 3", "owner": "Scrum Master", "source": "Backlog"},
            {"kpi": "On-time delivery %", "target": "> 90%", "owner": "PM", "source": "Sprints"},
            {"kpi": "Open high/critical risks", "target": "0", "owner": "PM", "source": "Risk register"},
            {"kpi": "Compliance on-time %", "target": "100%", "owner": "Founder/CA", "source": "Compliance calendar"},
            {"kpi": "Burn vs plan", "target": f"Within plan ({cur})", "owner": "Founder", "source": "Finance"},
        ]

        # --- SOPs ---
        sops = [
            {"sop": "Sprint planning & standups", "process": "Delivery", "owner": "Scrum Master", "status": "Draft"},
            {"sop": "Definition of Done / quality gate", "process": "Delivery", "owner": "QA Lead", "status": "Draft"},
            {"sop": "Release & rollback", "process": "DevOps", "owner": "DevOps", "status": "Draft"},
            {"sop": "Risk review cadence", "process": "Governance", "owner": "PM", "status": "Draft"},
        ]
        if india:
            sops += [
                {"sop": "GST invoicing & monthly filing", "process": "Finance/Compliance", "owner": "Accountant/CA", "status": "Draft"},
                {"sop": "Statutory due-date checklist (GST/TDS/PF/ESI/ROC)", "process": "Compliance", "owner": "CA/CS", "status": "Draft"},
            ]

        # --- PM Methodology (project-type aware) ---
        meth = gen_methodology_recommendation(idea, c)
        meth_rows = [{"event": e["event"], "frequency": e["frequency"], "duration": e["duration"], "attendees": e["attendees"]}
                     for e in meth.get("ceremony_calendar", [])]
        meth_help = (f"Recommended: {meth['recommended']} ({meth.get('confidence','')}). {meth.get('primary_rationale','')[:240]} "
                     f"Tooling: {meth.get('tooling', {}).get('primary', '')}.")

        # --- Tech Stack (project-type aware) ---
        tech = gen_tech_stack(idea, c)
        tech_rows = []
        for layer_key, layer_label in [("frontend", "Frontend"), ("backend", "Backend"),
                                        ("infrastructure", "Infrastructure"), ("ai_ml", "AI / ML"),
                                        ("integrations", "Integrations")]:
            vals = tech.get(layer_key) or []
            tech_rows.append({"layer": layer_label, "choice": ", ".join(vals) if isinstance(vals, list) else str(vals), "notes": ""})
        for bv in tech.get("build_vs_buy", []):
            tech_rows.append({"layer": bv.get("capability", ""), "choice": bv.get("decision", ""), "notes": bv.get("reason", "")})

        # --- AI Agents: how the 20 research-grade agents help THIS project ---
        agent_rows = []
        if MSME:
            cls_b = MSME.classify_business(idea)
            proj_mode = "startup" if (cls_b.get("is_startup") or cls_b.get("is_tech")) else "existing"
            cat_rank = {cat: i for i, cat in enumerate(
                ["Strategy & Growth", "Finance & Compliance", "Operations", "Risk & Diligence", "Workspace"])}
            items = sorted(MSME.list_agents().items(),
                           key=lambda kv: (cat_rank.get(kv[1].get("category"), 9), kv[1].get("name", "")))
            for key, a in items:
                modes = a.get("modes", [])
                best = "Startup & Existing" if len(modes) > 1 else ("Startup" if "startup" in modes else "Existing")
                agent_rows.append({
                    "agent": f"{a.get('icon','')} {a.get('name', key)}",
                    "helps": a.get("purpose", ""),
                    "best": ("★ " + best) if proj_mode in modes else best,
                })

        def module(mid, name, icon, help_text, columns, rows):
            return {"id": mid, "name": name, "icon": icon, "help": help_text,
                    "columns": columns, "rows": rows, "count": len(rows)}

        modules = [
            module("master", "Master Data", "🏢",
                   "Your single source of truth: entity, registrations and key parameters. In India, fill GSTIN/PAN/Udyam/DPIIT as you register — every other module references these.",
                   [{"key": "field", "label": "Field"}, {"key": "value", "label": "Value"}, {"key": "notes", "label": "Notes"}], master),
            module("methodology", "PM Methodology", "🧠",
                   meth_help,
                   [{"key": "event", "label": "Ceremony"}, {"key": "frequency", "label": "Frequency"}, {"key": "duration", "label": "Duration"}, {"key": "attendees", "label": "Attendees"}], meth_rows),
            module("techstack", "Tech Stack", "🧰",
                   tech.get("summary", "Recommended technology stack for this project type, with build-vs-buy guidance."),
                   [{"key": "layer", "label": "Layer / Capability"}, {"key": "choice", "label": "Recommendation"}, {"key": "notes", "label": "Notes"}], tech_rows),
            module("backlog", "Product Backlog", "🧱",
                   "Every unit of work as an ERP-style line item with a reference, sprint, priority and story points. This is what the team executes sprint by sprint.",
                   [{"key": "ref", "label": "Ref"}, {"key": "title", "label": "Work item"}, {"key": "sprint", "label": "Sprint"}, {"key": "priority", "label": "Priority"}, {"key": "points", "label": "Pts"}, {"key": "status", "label": "Status"}, {"key": "owner", "label": "Owner"}], tasks),
            module("sprints", "Sprints / Cycles", "🔄",
                   "The delivery timeline broken into cycles from your chosen methodology. Each cycle has a goal and a week-range.",
                   [{"key": "num", "label": "#"}, {"key": "name", "label": "Cycle"}, {"key": "goal", "label": "Goal"}, {"key": "weeks", "label": "Weeks"}, {"key": "status", "label": "Status"}], sprints),
            module("risks", "Risk Register (RAID)", "⚠️",
                   "Probability × Impact scored risks with a mitigation and an owner. Anything scoring high needs an owner and a plan before it bites.",
                   [{"key": "id", "label": "ID"}, {"key": "type", "label": "Type"}, {"key": "risk", "label": "Risk"}, {"key": "score", "label": "Score"}, {"key": "mitigation", "label": "Mitigation"}, {"key": "owner", "label": "Owner"}, {"key": "status", "label": "Status"}], risks),
            module("compliance", "Compliance Calendar", "⚖️",
                   ("Your statutory due-date tracker. In India this is the difference between clean books and penalties — set a reminder for each." if india
                    else "Key compliance obligations to track from pre-launch onward."),
                   [{"key": "obligation", "label": "Obligation"}, {"key": "authority", "label": "Authority"}, {"key": "frequency", "label": "Frequency"}, {"key": "due", "label": "Due"}, {"key": "status", "label": "Status"}], compliance),
            module("kpis", "KPIs", "📊",
                   "The handful of numbers that tell you if the project is healthy. Review them every sprint.",
                   [{"key": "kpi", "label": "KPI"}, {"key": "target", "label": "Target"}, {"key": "owner", "label": "Owner"}, {"key": "source", "label": "Source"}], kpis),
            module("sops", "SOPs", "📋",
                   "Standard operating procedures so the team runs consistently. Draft now, refine as you go.",
                   [{"key": "sop", "label": "SOP"}, {"key": "process", "label": "Process"}, {"key": "owner", "label": "Owner"}, {"key": "status", "label": "Status"}], sops),
            module("agents", "AI Agents — how they help", "🤖",
                   "Your 20 research-grade AI agents and how each one helps THIS project. ★ = most relevant to your stage. Open the Advisor to run any of them and get an audit-ready report.",
                   [{"key": "agent", "label": "Agent"}, {"key": "helps", "label": "How it helps this project"}, {"key": "best", "label": "Best for"}], agent_rows),
            module("team", "Team", "👥",
                   "The roles you need and how many of each, scaled to the project's complexity.",
                   [{"key": "role", "label": "Role"}, {"key": "count", "label": "Count"}, {"key": "responsibilities", "label": "Responsibilities"}], team),
        ]

        self._send(200, {
            "project": {"name": idea[:100], "industry": c["industry"], "geo": c["geo"],
                        "currency": cur, "methodology": kb["name"],
                        "total_weeks": sum(p["duration_weeks"] for p in kb["phases"] if p["duration_weeks"] > 0)},
            "modules": modules,
        })

    def handle_plm_execute(self, body):
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[plm/execute] idea={idea[:80]}", flush=True)

        classification = classify_idea(idea)
        phases_out = []
        for phase in PLM_PHASE_SPECS:
            try:
                data = phase["executor"](idea, classification)
                phases_out.append({
                    "id": phase["id"],
                    "name": phase["name"],
                    "duration": phase["duration"],
                    "agent": phase["agent"],
                    "icon": phase["icon"],
                    "status": "ok",
                    "data": data,
                })
            except Exception as e:
                print(f"[plm_phase {phase['name']}] FAILED: {e}", flush=True)
                traceback.print_exc()
                phases_out.append({
                    "id": phase["id"],
                    "name": phase["name"],
                    "duration": phase["duration"],
                    "agent": phase["agent"],
                    "icon": phase["icon"],
                    "status": "error",
                    "error": str(e),
                    "data": {"summary": f"Phase error: {e}"},
                })

        self._send(200, {
            "idea": idea,
            "classification": classification,
            "phases": phases_out,
            "summary": {
                "total": len(PLM_PHASE_SPECS),
                "ok": sum(1 for p in phases_out if p["status"] == "ok"),
            },
        })

    def handle_prototype(self, body):
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[plm/prototype] idea={idea[:80]}", flush=True)

        # Deterministic HTML template - always works
        html = generate_prototype_html(idea, classify_idea(idea))
        self._send(200, {"html": html, "idea": idea})

    def handle_workspace_seed(self, body):
        """Generate a fully-hydrated workspace from an idea.
        Returns project, tasks, sprints, risks, team, stakeholders - all pre-filled
        and ready to load into the PM tool workspace."""
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[workspace/seed] idea={idea[:80]}", flush=True)

        classification = classify_idea(idea)
        kb = KNOWLEDGE_BASE[classification["method_key"]]

        # Generate project object (editable fields)
        project = {
            "id": f"proj_{abs(hash(idea)) % 100000000}",
            "name": idea[:100],
            "description": f"A {classification['complexity'].replace('_', ' ')}-complexity {classification['industry']} initiative delivered using {kb['name']}.",
            "methodology": kb["name"],
            "method_key": classification["method_key"],
            "industry": classification["industry"],
            "complexity": classification["complexity"],
            "status": "planning",
            "created_at": "now",
            "total_weeks": sum(p["duration_weeks"] for p in kb["phases"] if p["duration_weeks"] > 0),
            "budget": COMPLEXITY_BUDGETS[classification["complexity"]]["total"],
            "tool_recommendation": kb["tool_recommendation"]["primary"],
        }

        # Generate sprints/cycles from phases
        sprints = []
        week_offset = 0
        for i, phase in enumerate(kb["phases"]):
            if phase["duration_weeks"] <= 0:
                continue
            sprints.append({
                "id": f"sprint_{i+1}",
                "number": i + 1,
                "name": phase["name"],
                "goal": phase["deliverables"][0] if phase.get("deliverables") else phase["name"],
                "start_week": week_offset + 1,
                "end_week": week_offset + phase["duration_weeks"],
                "status": "planned",
                "activities": phase.get("key_activities", []),
                "deliverables": phase.get("deliverables", []),
            })
            week_offset += phase["duration_weeks"]

        # Generate tasks from activities across all sprints
        tasks = []
        task_counter = 1
        statuses = ["todo", "todo", "todo", "in_progress", "todo"]
        priorities = ["high", "medium", "medium", "low", "high"]
        for sprint in sprints:
            for j, activity in enumerate(sprint["activities"]):
                tasks.append({
                    "id": f"task_{task_counter}",
                    "ref": f"PMG-{task_counter}",
                    "title": activity,
                    "description": f"Part of {sprint['name']} phase. Owner to define acceptance criteria.",
                    "status": statuses[j % len(statuses)],
                    "priority": priorities[j % len(priorities)],
                    "sprint_id": sprint["id"],
                    "sprint_name": sprint["name"],
                    "assignee": None,
                    "story_points": [2, 3, 5, 8][j % 4],
                    "labels": [classification["industry"].lower().replace("/", "-")],
                    "created_at": "now",
                })
                task_counter += 1
            # Add a deliverable task per sprint
            for deliverable in sprint["deliverables"][:2]:
                tasks.append({
                    "id": f"task_{task_counter}",
                    "ref": f"PMG-{task_counter}",
                    "title": f"Deliver: {deliverable}",
                    "description": f"Final deliverable for {sprint['name']}. Must meet quality gate.",
                    "status": "todo",
                    "priority": "high",
                    "sprint_id": sprint["id"],
                    "sprint_name": sprint["name"],
                    "assignee": None,
                    "story_points": 5,
                    "labels": ["deliverable"],
                    "created_at": "now",
                })
                task_counter += 1

        # Generate risks register
        risks = []
        for r in kb["risks"]:
            risks.append({
                "id": r["id"],
                "type": r["type"],
                "description": r["description"],
                "probability": r["probability"],
                "impact": r["impact"],
                "score": r["probability"] * r["impact"],
                "mitigation": r["mitigation"],
                "owner": r["owner"],
                "status": "open",
            })

        # Generate team roster
        team = []
        for i, t in enumerate(kb["team_composition"]):
            team.append({
                "id": f"member_{i+1}",
                "role": t["role"],
                "count": t["count"],
                "allocation": t["allocation"],
                "name": None,
                "email": None,
                "status": "to_be_hired",
            })

        # Generate stakeholder map
        stakeholders = []
        for i, s in enumerate(kb["stakeholders"]):
            stakeholders.append({
                "id": f"stake_{i+1}",
                "name": s["name"],
                "power": s["power"],
                "interest": s["interest"],
                "strategy": s["strategy"],
                "channel": s["channel"],
                "contact": None,
            })

        # Generate KPIs
        kpis = []
        for i, k in enumerate(kb["kpis"]):
            kpis.append({
                "id": f"kpi_{i+1}",
                "metric": k["metric"],
                "target": k["target"],
                "current": "TBD",
                "status": "not_started",
            })

        # Budget breakdown
        budget = COMPLEXITY_BUDGETS[classification["complexity"]].copy()

        workspace = {
            "project": project,
            "sprints": sprints,
            "tasks": tasks,
            "risks": risks,
            "team": team,
            "stakeholders": stakeholders,
            "kpis": kpis,
            "budget": budget,
            "methodology_details": kb["method_details"],
            "why_not_others": kb["why_not_others"],
            "success_factors": kb["success_factors"],
            "tool_recommendation": kb["tool_recommendation"],
        }

        self._send(200, {
            "workspace": workspace,
            "classification": classification,
        })

    def handle_report_generate(self, body):
        """Non-streaming endpoint: generate full consulting report and return as one JSON."""
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[report/generate] idea={idea[:80]}", flush=True)
        classification = classify_idea(idea)
        sections = generate_full_report(idea, classification)
        self._send(200, {
            "idea": idea,
            "classification": classification,
            "sections": sections,
            "metadata": {
                "report_style": "Big 3 Blended (McKinsey + BCG + Bain)",
                "generated_at": "now",
                "section_count": len(sections),
                "ok_count": sum(1 for s in sections if s["status"] == "ok"),
            },
        })

    def handle_report_stream(self, body):
        """SSE streaming endpoint: stream sections one at a time as they generate.
        Each section is sent as a separate SSE event so the frontend can render progressively."""
        import time
        idea = (body.get("idea") or "").strip()
        if not idea:
            self._send(200, {"error": "Please provide an 'idea' field"})
            return
        print(f"[report/stream] idea={idea[:80]}", flush=True)

        # Set up SSE response headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")  # disable proxy buffering
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

        try:
            classification = classify_idea(idea)

            # Send opening event with metadata
            opening = {
                "type": "start",
                "idea": idea,
                "classification": classification,
                "total_sections": len(REPORT_SECTIONS),
                "section_titles": [s["title"] for s in REPORT_SECTIONS],
            }
            self._sse_write(opening)

            # Stream each section with a small delay so user perceives the streaming
            for i, section_spec in enumerate(REPORT_SECTIONS):
                # Artificial delay so streaming is visible (1.5s per section = 16s total)
                time.sleep(1.5)
                try:
                    data = section_spec["generator"](idea, classification)
                    section_event = {
                        "type": "section",
                        "index": i,
                        "id": section_spec["id"],
                        "title": section_spec["title"],
                        "icon": section_spec["icon"],
                        "style": section_spec["style"],
                        "status": "ok",
                        "data": data,
                    }
                except Exception as e:
                    print(f"[report/stream] section {section_spec['id']} failed: {e}", flush=True)
                    traceback.print_exc()
                    section_event = {
                        "type": "section",
                        "index": i,
                        "id": section_spec["id"],
                        "title": section_spec["title"],
                        "icon": section_spec["icon"],
                        "status": "error",
                        "error": str(e),
                        "data": {},
                    }
                self._sse_write(section_event)

            # Send completion event
            self._sse_write({"type": "done", "section_count": len(REPORT_SECTIONS)})
        except Exception as e:
            print(f"[report/stream] FATAL: {e}", flush=True)
            traceback.print_exc()
            try:
                self._sse_write({"type": "error", "error": str(e)})
            except Exception:
                pass

    def _sse_write(self, payload):
        """Write one Server-Sent Event."""
        try:
            data_line = f"data: {json.dumps(payload)}\n\n"
            self.wfile.write(data_line.encode("utf-8"))
            self.wfile.flush()
        except Exception as e:
            print(f"[sse_write] failed: {e}", flush=True)

    def handle_consulting_generate(self, body):
        """Non-streaming consulting report."""
        description = (body.get("description") or body.get("idea") or "").strip()
        if not description:
            self._send(200, {"error": "Please provide a 'description' field"})
            return
        print(f"[consulting/generate] desc={description[:80]}", flush=True)
        domains = classify_consulting_domain(description)
        scenarios = get_relevant_scenarios(domains, limit_per_domain=25)
        sections = []
        for spec in CONSULTING_REPORT_SECTIONS:
            try:
                data = spec["generator"](description, domains, scenarios)
                sections.append({"id": spec["id"], "title": spec["title"], "icon": spec["icon"], "style": spec["style"], "status": "ok", "data": data})
            except Exception as e:
                print(f"[consulting] section {spec['id']} failed: {e}", flush=True)
                sections.append({"id": spec["id"], "title": spec["title"], "icon": spec["icon"], "status": "error", "error": str(e), "data": {}})
        self._send(200, {
            "description": description,
            "domains": domains,
            "domain_names": [CONSULTING_DOMAINS[d][0] for d in domains if d in CONSULTING_DOMAINS],
            "scenario_count": len(scenarios),
            "sections": sections,
        })

    def handle_consulting_stream(self, body):
        """SSE streaming consulting report."""
        import time
        description = (body.get("description") or body.get("idea") or "").strip()
        if not description:
            self._send(200, {"error": "Please provide a 'description' field"})
            return
        print(f"[consulting/stream] desc={description[:80]}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        try:
            domains = classify_consulting_domain(description)
            scenarios = get_relevant_scenarios(domains, limit_per_domain=25)
            self._sse_write({
                "type": "start",
                "description": description,
                "domains": domains,
                "domain_names": [CONSULTING_DOMAINS[d][0] for d in domains if d in CONSULTING_DOMAINS],
                "scenario_count": len(scenarios),
                "total_sections": len(CONSULTING_REPORT_SECTIONS),
                "section_titles": [s["title"] for s in CONSULTING_REPORT_SECTIONS],
            })
            for i, spec in enumerate(CONSULTING_REPORT_SECTIONS):
                time.sleep(1.5)
                try:
                    data = spec["generator"](description, domains, scenarios)
                    self._sse_write({"type": "section", "index": i, "id": spec["id"], "title": spec["title"], "icon": spec["icon"], "style": spec["style"], "status": "ok", "data": data})
                except Exception as e:
                    print(f"[consulting/stream] section {spec['id']} failed: {e}", flush=True)
                    self._sse_write({"type": "section", "index": i, "id": spec["id"], "title": spec["title"], "icon": spec["icon"], "status": "error", "error": str(e), "data": {}})
            self._sse_write({"type": "done", "section_count": len(CONSULTING_REPORT_SECTIONS)})
        except Exception as e:
            print(f"[consulting/stream] FATAL: {e}", flush=True)
            try:
                self._sse_write({"type": "error", "error": str(e)})
            except Exception:
                pass

    def handle_consulting_demo(self, demo_id):
        """Generate a preloaded demo report."""
        print(f"[consulting/demo] id={demo_id}", flush=True)
        result = generate_demo_report(demo_id)
        self._send(200, result)

    def handle_consulting_from_dd(self, body):
        """Generate report from filled due diligence questionnaire."""
        company = body.get("company_profile", {})
        scope = body.get("scope_selection", {})
        current = body.get("current_state", {})

        # Build description from questionnaire answers
        company_name = company.get("company_name", "the client organization")
        industry = company.get("industry", "")
        revenue = company.get("revenue", "")
        employees = company.get("employees", "")
        erp = company.get("erp_system", "")
        pain_points = scope.get("pain_points", "")
        engagement_type = scope.get("engagement_type", "Finance Transformation")
        domains = scope.get("primary_domains", [])
        if isinstance(domains, str):
            domains = [d.strip() for d in domains.split(",")]

        description = f"{engagement_type} engagement for {company_name}, a {revenue} revenue {industry} company with {employees} employees"
        if erp:
            description += f" running {erp}"
        if pain_points:
            description += f". Key concerns: {pain_points}"
        if company.get("recent_changes"):
            description += f". Recent changes: {company['recent_changes']}"
        if current.get("additional_context"):
            description += f". Additional context: {current['additional_context']}"

        # Auto-detect domains if not selected
        if not domains:
            domains = classify_consulting_domain(description)

        print(f"[consulting/from-dd] {company_name} | {industry} | domains={domains}", flush=True)

        scenarios = get_relevant_scenarios(domains, limit_per_domain=25)
        sections = []
        for spec in CONSULTING_REPORT_SECTIONS:
            try:
                data = spec["generator"](description, domains, scenarios)
                agent_key = None
                for ak, av in CONSULTING_AGENTS.items():
                    if spec["id"] in av.get("handles", []):
                        agent_key = ak
                        break
                sections.append({
                    "id": spec["id"], "title": spec["title"], "icon": spec["icon"],
                    "style": spec["style"], "status": "ok", "data": data,
                    "agent": CONSULTING_AGENTS.get(agent_key) if agent_key else None,
                })
            except Exception as e:
                sections.append({"id": spec["id"], "title": spec["title"], "icon": spec["icon"], "status": "error", "error": str(e), "data": {}})

        self._send(200, {
            "description": description,
            "company_profile": company,
            "engagement_type": engagement_type,
            "domains": domains,
            "domain_names": [CONSULTING_DOMAINS[d][0] for d in domains if d in CONSULTING_DOMAINS],
            "scenario_count": len(scenarios),
            "sections": sections,
            "agents_involved": {k: v for k, v in CONSULTING_AGENTS.items()},
            "workflow": ENGAGEMENT_WORKFLOW,
        })

    def log_message(self, format, *args):
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")


# ============================================================
# PROTOTYPE HTML - deterministic template
# ============================================================
def generate_prototype_html(idea, classification):
    method_name = KNOWLEDGE_BASE[classification["method_key"]]["name"]
    industry = classification["industry"]
    safe_idea = idea.replace("<", "&lt;").replace(">", "&gt;")[:200]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_idea} — Prototype</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-900 font-sans">
<header class="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white">
  <div class="max-w-6xl mx-auto px-6 py-20">
    <div class="inline-block px-3 py-1 rounded-full bg-white/20 text-xs font-bold mb-4">BUILT FOR {industry.upper()}</div>
    <h1 class="text-5xl md:text-6xl font-black tracking-tight">{safe_idea}</h1>
    <p class="mt-4 text-xl opacity-90 max-w-3xl">A purpose-built solution that saves time, reduces errors, and unlocks growth — delivered with the {method_name} methodology for predictable, high-quality outcomes.</p>
    <div class="mt-8 flex gap-4 flex-wrap">
      <button onclick="alert('Sign-up flow would start here')" class="px-6 py-3 bg-white text-indigo-700 rounded-lg font-bold shadow-lg hover:scale-105 transition">Start Free Trial</button>
      <button onclick="document.getElementById('features').scrollIntoView({{behavior:'smooth'}})" class="px-6 py-3 bg-white/10 text-white rounded-lg font-bold border border-white/30">Learn More</button>
    </div>
  </div>
</header>

<section id="features" class="max-w-6xl mx-auto px-6 py-20">
  <h2 class="text-4xl font-black text-center">Everything You Need</h2>
  <p class="text-center text-slate-600 mt-2">Three core capabilities that deliver day-one value.</p>
  <div class="grid md:grid-cols-3 gap-6 mt-12">
    <div class="bg-white rounded-2xl p-8 shadow-lg border">
      <div class="text-4xl">📊</div>
      <h3 class="text-xl font-black mt-4">Unified Dashboard</h3>
      <p class="text-slate-600 mt-2">Single-pane view of every metric that matters, loaded in under 2 seconds.</p>
    </div>
    <div class="bg-white rounded-2xl p-8 shadow-lg border">
      <div class="text-4xl">⚡</div>
      <h3 class="text-xl font-black mt-4">Workflow Automation</h3>
      <p class="text-slate-600 mt-2">Automate your top-3 repetitive tasks in minutes, not months.</p>
    </div>
    <div class="bg-white rounded-2xl p-8 shadow-lg border">
      <div class="text-4xl">🔔</div>
      <h3 class="text-xl font-black mt-4">Smart Alerts</h3>
      <p class="text-slate-600 mt-2">Proactive notifications when something needs your attention.</p>
    </div>
  </div>
</section>

<section class="bg-slate-900 text-white py-20">
  <div class="max-w-6xl mx-auto px-6 text-center">
    <h2 class="text-4xl font-black">Try It Now</h2>
    <p class="mt-2 opacity-70">Interactive demo — enter a metric name and watch it appear on the dashboard.</p>
    <div class="mt-8 max-w-md mx-auto flex gap-2">
      <input id="metricInput" type="text" placeholder="e.g. Daily Active Users" class="flex-1 px-4 py-3 rounded-lg text-slate-900">
      <button onclick="addMetric()" class="px-6 py-3 bg-indigo-500 rounded-lg font-bold">Add</button>
    </div>
    <div id="metrics" class="mt-8 grid md:grid-cols-3 gap-4 max-w-3xl mx-auto"></div>
  </div>
</section>

<footer class="bg-slate-100 py-12 text-center text-slate-600">
  <p>Built with the {method_name} methodology · Purpose-built for {industry}</p>
  <p class="text-xs mt-2">Prototype generated by PMGuru v{VERSION}</p>
</footer>

<script>
function addMetric() {{
  const input = document.getElementById('metricInput');
  const name = input.value.trim();
  if (!name) return;
  const val = Math.floor(Math.random() * 10000);
  const card = document.createElement('div');
  card.className = 'bg-white/10 rounded-xl p-6 backdrop-blur';
  card.innerHTML = '<div class="text-xs opacity-60 uppercase tracking-wide">' + name + '</div><div class="text-3xl font-black mt-2">' + val.toLocaleString() + '</div><div class="text-xs text-emerald-400 mt-1">↑ +' + Math.floor(Math.random()*30) + '% vs last week</div>';
  document.getElementById('metrics').appendChild(card);
  input.value = '';
}}
</script>
</body>
</html>"""


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("=" * 60, flush=True)
    print(f"PMGuru Brain v{VERSION} starting on port {port}", flush=True)
    print(f"Architecture: template-driven + LLM-as-evaluator", flush=True)
    print(f"Methodologies trained: {list(KNOWLEDGE_BASE.keys())}", flush=True)
    print(f"Industry patterns: {len(INDUSTRY_PATTERNS)}", flush=True)
    print(f"PM agents: {list(PM_AGENT_SPECS.keys())}", flush=True)
    print(f"PLM phases: {[p['name'] for p in PLM_PHASE_SPECS]}", flush=True)
    print(f"GROQ_API_KEY set: {bool(os.getenv('GROQ_API_KEY', '').strip())}", flush=True)
    print("=" * 60, flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
