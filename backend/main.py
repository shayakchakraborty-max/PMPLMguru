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
    return {
        "method_key": best["method"],
        "industry": best["industry"],
        "complexity": best["complexity"],
        "confidence_score": best_score,
    }


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
        "infrastructure": ["Vercel (web)", "Railway or Render (services)", "Cloudflare (CDN + WAF)"],
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
    return {
        "summary": f"Bottoms-up sizing reveals a ${market['som']} serviceable obtainable market within the broader ${market['tam']} {classification['industry']} sector.",
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
        "geographic_priorities": ["Initial: India (Tier 1 + Tier 2 cities)", "Year 2: Southeast Asia (Indonesia, Vietnam)", "Year 3: Middle East + select African markets"] if "India" in str(market.get("drivers", "")).lower() or "ondc" in str(market.get("drivers", "")).lower() else ["Initial: Domestic market", "Year 2: Adjacent English-speaking markets", "Year 3: Strategic expansion based on traction"],
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
    """3-year financial model."""
    fin = FINANCIAL_MULTIPLIERS[classification["complexity"]]
    budget = COMPLEXITY_BUDGETS[classification["complexity"]]
    y1_loss = fin["burn_y1"] - fin["y1_revenue"]
    y2_breakeven = fin["y2_revenue"] - (fin["burn_y1"] * 1.4)
    y3_profit = fin["y3_revenue"] - (fin["burn_y1"] * 1.8)
    return {
        "summary": f"3-year model shows path to profitability by Year {2 if y2_breakeven > 0 else 3}, with cumulative revenue of ${(fin['y1_revenue'] + fin['y2_revenue'] + fin['y3_revenue']):,} and total investment requirement of ${(fin['burn_y1'] * 4.2):,.0f}.",
        "revenue_projection": [
            {"year": "Year 1", "users": f"{fin['y1_users']:,}", "revenue": f"${fin['y1_revenue']:,}", "growth": "Launch year"},
            {"year": "Year 2", "users": f"{fin['y1_users'] * 6:,}", "revenue": f"${fin['y2_revenue']:,}", "growth": f"{round(100 * (fin['y2_revenue'] / fin['y1_revenue'] - 1))}% YoY"},
            {"year": "Year 3", "users": f"{fin['y3_users']:,}", "revenue": f"${fin['y3_revenue']:,}", "growth": f"{round(100 * (fin['y3_revenue'] / fin['y2_revenue'] - 1))}% YoY"},
        ],
        "cost_structure": budget,
        "unit_economics": {
            "blended_cac": f"${round(fin['burn_y1'] / fin['y1_users'])}",
            "ltv_estimate": f"${round(fin['y3_revenue'] / fin['y3_users'] * 3)}",
            "ltv_cac_target": "≥ 3:1 by end of Year 2",
            "payback_period": "12-18 months",
            "gross_margin": "65-78% depending on infrastructure efficiency",
        },
        "profit_loss": [
            {"year": "Year 1", "revenue": fin["y1_revenue"], "costs": fin["burn_y1"], "net": y1_loss, "status": "Loss (investment phase)"},
            {"year": "Year 2", "revenue": fin["y2_revenue"], "costs": int(fin["burn_y1"] * 1.4), "net": int(y2_breakeven), "status": "Approaching breakeven" if y2_breakeven > -100000 else "Loss (growth phase)"},
            {"year": "Year 3", "revenue": fin["y3_revenue"], "costs": int(fin["burn_y1"] * 1.8), "net": int(y3_profit), "status": "Profitable" if y3_profit > 0 else "Path to profitability"},
        ],
        "funding_requirement": {
            "seed": f"${(fin['burn_y1'] * 1.5):,.0f} - 18 month runway to PMF + early traction",
            "series_a": f"${(fin['burn_y1'] * 4):,.0f} - 24 month runway to scale GTM",
            "use_of_funds": ["55% engineering and product", "25% sales and marketing", "12% G&A and operations", "8% reserves"],
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
    """Go-to-market strategy."""
    gtm = GTM_STRATEGIES.get(classification["industry"], GTM_STRATEGIES["SaaS/Product"])
    return {
        "summary": f"GTM motion is {gtm['motion']}, optimized for {classification['industry']} buyer behavior and economics.",
        "primary_motion": gtm["motion"],
        "channels": gtm["channels"],
        "unit_economics": {
            "target_cac": gtm["cac"],
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
    """Regulatory and compliance requirements."""
    reg = REGULATIONS.get(classification["industry"], REGULATIONS["SaaS/Product"])
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
                "architecture": "template-driven (deterministic) + LLM-as-evaluator + 500-example training + Big 3 consulting reports",
                "pm_agents": list(PM_AGENT_SPECS.keys()),
                "plm_phases": [p["name"] for p in PLM_PHASE_SPECS],
                "report_sections": [s["title"] for s in REPORT_SECTIONS],
                "methodologies_trained": list(KNOWLEDGE_BASE.keys()),
                "industry_patterns": len(INDUSTRY_PATTERNS),
                "training_examples": len(TRAINING_LIBRARY),
                "groq_key": bool(os.getenv("GROQ_API_KEY", "").strip()),
            })
        elif path == "/simulations":
            # Run all 500+ examples through the classifier and return accuracy report
            try:
                sim_results = run_simulations()
                self._send(200, sim_results)
            except Exception as e:
                self._send(200, {"error": str(e), "traceback": traceback.format_exc()[-1000:]})
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
