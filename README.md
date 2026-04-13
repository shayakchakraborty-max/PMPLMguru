# PMGuru v12 — Three-Path Launcher

## What changed in this push

The `/auto` flow now gives users **three independent paths** after they enter an idea,
instead of jumping straight to the PM workspace.

```
  Enter idea
      │
      ▼
 Classify (< 1s)
      │
      ▼
  Three choices ─────────┬─────────────────┐
      │                  │                 │
      ▼                  ▼                 ▼
  🗂️ PM Tool         📘 PLM Report    🎨 Prototype
   /workspace            /plm             /prototype
```

All three paths share the same backend brain (`backend/main.py`, no changes).
Only the frontend routes were revised.

## Files in this push

| File | Status | Purpose |
|------|--------|---------|
| `frontend/app/auto/page.js` | **revised** | Two-step launcher: idea input → three-path chooser |
| `frontend/app/plm/page.js` | **new** | Renders the 8-phase PLM report (Discovery → Iterate) |
| `frontend/app/prototype/page.js` | **new** | Renders the generated HTML prototype in a device-framed iframe |
| `frontend/app/workspace/page.js` | unchanged | The existing 8-view PM tool |
| `frontend/app/api/pipeline/route.js` | unchanged | Already supports `stage: "pm" / "plm" / "workspace"` |
| `frontend/app/api/prototype/route.js` | unchanged | Already proxies `/plm/prototype` |
| `backend/main.py` | unchanged | Already exposes `/workspace/seed`, `/plm/execute`, `/plm/prototype` |
| `backend/requirements.txt` | unchanged | `httpx==0.27.2` |

## How to deploy

### 1. Commit the new/revised files

Push these three files to your GitHub repo:

```
frontend/app/auto/page.js        ← replace
frontend/app/plm/page.js         ← new folder + file
frontend/app/prototype/page.js   ← new folder + file
```

### 2. Deploy to Vercel

Vercel will auto-deploy on push. No environment variable changes needed — the existing
`BRAIN_URL` continues to work for all three paths.

### 3. Backend — nothing to do

Your existing Render deployment already serves `/workspace/seed`, `/plm/execute`, and
`/plm/prototype`. Just make sure it's warm:

```
curl https://your-render-url.onrender.com/health
```

## User flow

1. User lands on `/auto` and enters an idea.
2. Clicks **Analyze & choose path** → backend classifies in < 1s.
3. Sees their idea with classification pills (methodology · industry · complexity)
   plus a short "why this methodology" explanation.
4. Sees **three action cards**:
   - **🗂️ PM Tool Workspace** — generates full editable workspace, navigates to `/workspace`
   - **📘 PLM Plan & Report** — generates 8-phase lifecycle report, navigates to `/plm`
   - **🎨 Interactive Prototype** — generates working HTML, navigates to `/prototype`
5. Each path is cached in `localStorage`, so the user can run all three on the same
   idea and switch freely.
6. Each destination page has a "← Back to launcher" link that returns to `/auto`.

## PLM page features

- **Phase rail** at the top for quick jumping
- **Expand/collapse all** controls
- **Print view** — clean CSS print styles strip chrome
- **Export JSON** — download the full PLM data blob
- All 8 phases render their specific data types (personas, RICE scores, user stories,
  sprint plans, test cases, CI/CD pipelines, launch announcements, success metrics)

## Prototype page features

- **Device viewport toggle** — Desktop / Tablet / Mobile
- **Fake browser chrome** for a polished share-ready look
- **Regenerate** — re-runs the backend to get a fresh HTML variant
- **Open in new tab** — browse the prototype standalone
- **Download HTML** — save the file to share, deploy, or edit

## Version history

- **v11** — single path: idea → workspace only
- **v12** — this push — three-path launcher with PM / PLM / Prototype

## Zero LLM dependencies

All three paths use the deterministic template engine. Groq is still optional evaluator-only.
