# 🔧 V12 Frontend Sync Fix

## ⚠️ The Problem

Your **backend** is on v12 ✅ but your **frontend** is still on v10 ❌. They're talking past each other:

- Old frontend calls `/api/pipeline`, `/api/pmtool`, `/api/prototype` (v10 routes)
- New backend only has `/autopilot` (v12 endpoint)
- Result: 500 error because those old routes return nothing useful

## ✅ The Fix

Upload these **2 frontend files** to GitHub. The folder structure inside this zip matches your repo exactly, so just drag-and-drop the `frontend` folder onto GitHub.

```
v12-frontend-fix/
└── frontend/
    └── app/
        ├── auto/
        │   └── page.js              ← Replaces existing (v12 single-button UI)
        └── api/
            └── autopilot/
                └── route.js         ← NEW file (didn't exist before)
```

## 🚀 Upload Steps

### Step 1: Download & Unzip
1. Download `v12-frontend-fix.zip`
2. Unzip it on your computer
3. You'll see a `v12-frontend-fix` folder containing a `frontend` subfolder

### Step 2: Drag-and-Drop to GitHub
1. Open GitHub → your repo `PMPLMguru`
2. Click **"Add file"** → **"Upload files"**
3. **Drag the `frontend` folder** from the unzipped folder onto GitHub's upload area
4. GitHub should show TWO files in the "Add" preview:
   - `frontend/app/auto/page.js` — modified
   - `frontend/app/api/autopilot/route.js` — **NEW (in green)**
5. Commit message: `Sync frontend to v12 - add autopilot route`
6. Click **"Commit changes"**

### Step 3: Wait for Vercel
1. Vercel auto-deploys when it sees the commit (~90 seconds)
2. Watch your Vercel dashboard for the green checkmark on the new deployment

### Step 4: Hard Refresh the Frontend
1. Open your Vercel URL → click "Launch Autopilot" (or `/auto`)
2. **Hard refresh**: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. The page header should now say **"PMGuru v12 · Detailed Autopilot"**

If you still see "v10" or "v11" in the header, hard refresh again — Vercel sometimes serves cached pages.

### Step 5: Test
1. Enter an idea
2. Click **"🚀 RUN FULL AUTOPILOT"**
3. **Open a second tab** with Render Logs
4. Within ~5 seconds you should see lines like:
   ```
   [AUTOPILOT] Stage 1: Detailed PM Planning
   [AUTOPILOT]  Running Methodology Expert...
   ```
5. The full run takes 3-5 minutes (detailed mode)
6. When complete, you get the dashboard with 3 download buttons that all work

## 🆘 If It Still Fails

If after this you still get the same 500 error, the problem is something else. Check Render Logs:

- **If you see `[AUTOPILOT] Stage 1...` lines** → backend is being called correctly, the issue is inside the backend (probably JSON parsing or token limits). Paste the full traceback and I'll fix it.
- **If you see NO `[AUTOPILOT]` lines** → frontend STILL isn't reaching the backend. Check that:
  - `frontend/app/api/autopilot/route.js` definitely exists on GitHub
  - `BRAIN_URL` environment variable in Vercel is correct
  - Vercel finished deploying the new commit (check Deployments tab)

## 📝 What Each File Does

**`frontend/app/auto/page.js`**
The main UI page. Has a single textarea, single "RUN FULL AUTOPILOT" button, calls one endpoint, renders the full report when done. The v12 version has the detailed rendering for all the new fields.

**`frontend/app/api/autopilot/route.js`** (NEW)
A Next.js API route that proxies requests from your browser to the Render backend's `/autopilot` endpoint. Has a 5-minute timeout to handle the longer detailed-mode runs. This file did NOT exist in v10 — that's why you're getting 500 errors right now.

---

**Drag the `frontend` folder onto GitHub, commit, wait 90 seconds, hard refresh, test.** That's literally it. The backend is already perfect — we just need to give it a frontend that knows how to talk to it. 🚀
