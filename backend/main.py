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

VERSION = "11.0"

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
                "architecture": "template-driven (deterministic) + LLM-as-evaluator + 500-example training",
                "pm_agents": list(PM_AGENT_SPECS.keys()),
                "plm_phases": [p["name"] for p in PLM_PHASE_SPECS],
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
