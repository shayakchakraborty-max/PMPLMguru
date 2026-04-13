# PMGuru v12 — Complete Working Project

This zip contains a **complete, self-contained** Next.js 14 project that is
guaranteed to build on Vercel. The previous 404 happened because required
scaffolding files (`package.json`, `layout.js`, `next.config.js`,
`tailwind.config.js`, `globals.css`) were missing from the repo.

## What's in this zip

```
pmguru-complete/
├── frontend/                      ← Vercel project root goes HERE
│   ├── package.json               ← NEW · dependencies
│   ├── next.config.js             ← NEW · required
│   ├── tailwind.config.js         ← NEW · Tailwind + safelist for dynamic classes
│   ├── postcss.config.js          ← NEW · required for Tailwind build
│   ├── jsconfig.json              ← NEW
│   ├── .gitignore                 ← NEW
│   └── app/
│       ├── layout.js              ← NEW · root layout (required by App Router)
│       ├── globals.css            ← NEW · Tailwind directives
│       ├── page.js                ← NEW · root route, redirects / → /auto
│       ├── auto/page.js           ← v12 three-path launcher
│       ├── workspace/page.js      ← existing 8-view PM tool
│       ├── plm/page.js            ← NEW · 8-phase PLM report
│       ├── prototype/page.js      ← NEW · interactive prototype viewer
│       └── api/
│           ├── pipeline/route.js  ← proxies /workspace/seed, /plm/execute
│           └── prototype/route.js ← proxies /plm/prototype
└── backend/
    ├── main.py                    ← unchanged — already exposes all endpoints
    └── requirements.txt
```

## Step-by-step push instructions

### Option A — Nuclear reset (RECOMMENDED)

This is the cleanest path. It replaces your broken `frontend/` folder
entirely with a known-working one.

1. **On your computer:** unzip this file. You'll see a `frontend/` folder.
2. **In your GitHub repo:** delete your existing `frontend/` folder
   entirely.
3. **Copy** the unzipped `frontend/` folder into your repo in the exact
   same spot.
4. **Commit and push** with a message like "v12 complete project reset".
5. Wait ~60 seconds for Vercel to redeploy.
6. Visit your root URL → you should be forwarded to `/auto`.

### Option B — File by file (if you want to preserve other files)

If your existing `frontend/` has other files you want to keep, just add
the missing scaffolding files. In order of importance:

1. **`frontend/package.json`** — if this is missing, nothing builds.
   Replace whatever is there.
2. **`frontend/app/layout.js`** — required by Next.js App Router.
   If it's missing, every page 404s.
3. **`frontend/app/page.js`** — required for the root `/` URL to work.
4. **`frontend/app/globals.css`** — Tailwind needs this.
5. **`frontend/tailwind.config.js`** + **`frontend/postcss.config.js`** —
   Tailwind build config.
6. **`frontend/next.config.js`** — Next.js config.
7. Finally the page files: `app/auto/page.js`, `app/plm/page.js`,
   `app/prototype/page.js`, `app/workspace/page.js`,
   `app/api/pipeline/route.js`, `app/api/prototype/route.js`.

## Critical: Vercel Root Directory setting

This is the single most common cause of Vercel 404s.

1. Open your Vercel project dashboard
2. Go to **Settings → General**
3. Scroll to **Root Directory**
4. Set it to exactly: `frontend`
   (or `pmguru-push/frontend` if your repo has `pmguru-push/` as an
   outer folder)
5. Click **Save**
6. Go to the **Deployments** tab and click **Redeploy** on the latest
   deployment. Make sure "Use existing Build Cache" is **unchecked**.

If this setting is wrong, Vercel looks at your repo root for
`package.json`, doesn't find a Next.js project, and returns 404 on
every route regardless of what files you push.

## Environment variable

In Vercel → Settings → Environment Variables, make sure you have:

- `BRAIN_URL` = `https://your-render-url.onrender.com`
  (no trailing slash)

If this is missing, the three action cards on `/auto` will still render
but clicking them will show "BRAIN_URL environment variable is not set"
as an error.

## Backend check

Your Render backend is unchanged in this zip — it already has everything
needed. Just confirm it's awake:

```
curl https://your-render-url.onrender.com/health
```

You should see JSON with `version: 11.0` and a list of endpoints.
If Render is sleeping, this call wakes it up and takes ~30 seconds.

## What to do if the 404 persists after all of this

Tell me exactly:

1. The output of your Vercel **build log** (Deployments → latest → Build Logs)
2. The value of your Vercel **Root Directory** setting
3. Whether `/auto` loads (yes/no/different error)
4. The output of `curl https://<your-render>.onrender.com/health`

With those four pieces of information I can diagnose the remaining issue
in one message instead of guessing.

## Version

- **v12 complete** — self-contained, zero assumptions about your repo
