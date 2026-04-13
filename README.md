# PMGuru v12 — Root 404 Hotfix

## The problem

After deploying v12 to Vercel, visiting the root URL
(`https://your-url.vercel.app/`) returns:

```
404: NOT_FOUND
Code: NOT_FOUND
```

## Why

Next.js App Router only serves URLs that have a matching `page.js` file.
Your app has pages at `/auto`, `/workspace`, `/plm`, `/prototype` — but
**nothing at the root**. So hitting `/` returns 404. This is not a broken
deployment — it's a missing file.

## Immediate workaround (no code change)

Open `https://your-url.vercel.app/auto` directly. Bookmark that.
Everything works from there.

## Proper fix — add one file

Add `frontend/app/page.js` with exactly this content:

```js
import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/auto");
}
```

That's it. Four lines. The `redirect()` helper is a built-in Next.js
server function — no extra dependencies, no environment variables.

## Push steps

1. Copy `frontend/app/page.js` from this hotfix zip into your repo at
   the **same path**: `frontend/app/page.js`
2. Commit and push to GitHub
3. Vercel auto-redeploys in ~60 seconds
4. Visit the root URL → you'll be forwarded to `/auto`

## Debug checklist (if it still 404s)

If `/auto` also 404s after the redirect is live:

1. **Check the Vercel deployment log.** If the build failed, Vercel
   serves the last successful deploy. A fresh failed deploy can look
   like "deployed" in the dashboard but actually be broken.

2. **Verify the Root Directory setting in Vercel.** Go to
   Project → Settings → General → Root Directory. It should be
   `frontend` (not the repo root) because your Next.js project lives
   inside `frontend/`.

3. **Check that the new folders were committed.** On GitHub, navigate to
   `frontend/app/` and confirm you can see `auto/`, `plm/`, `prototype/`,
   `workspace/`, and now `page.js`. If a folder is missing, git may not
   have picked up empty directories — make sure each has its `page.js`.

4. **Test the backend directly.** Hit
   `https://your-render-url.onrender.com/health` — if that also 404s,
   Render is asleep or misdeployed. Wait 30s and retry.

5. **Check `BRAIN_URL` is set in Vercel.** Project → Settings →
   Environment Variables → `BRAIN_URL` should match your Render URL,
   with no trailing slash.

## File list in this hotfix

| File | Status | Purpose |
|------|--------|---------|
| `frontend/app/page.js` | **new** | Root redirect to `/auto` |
