"use client";

/* Firm OS — the consulting-firm ERP cockpit. A Senior Partner sees firm-wide billing,
   CAGR, utilization, billable mix, by-sector / by-type and top engagements; RBAC gates
   modules per role; timesheets & expenses (billable/non-billable) submit here. Reads
   /api/firm. Owner = same anon id as /engage (shared firm tenant for the demo). */

import { useEffect, useMemo, useState } from "react";

function ownerId() {
  try { let o = localStorage.getItem("pmguru_owner"); if (!o) { o = "u-" + Math.random().toString(36).slice(2, 11); localStorage.setItem("pmguru_owner", o); } return o; }
  catch { return "demo"; }
}

const NEXT_APPROVER = { junior_consultant: "Consultant", consultant: "Senior Consultant", senior_consultant: "Engagement Manager", engagement_manager: "Engagement Director", engagement_director: "Partner" };
const APPR_LABEL = (role) => NEXT_APPROVER[role] || "approver";

export default function FirmPage() {
  const [rbac, setRbac] = useState(null);
  const [role, setRole] = useState("senior_partner");
  const [ck, setCk] = useState(null);
  const [ts, setTs] = useState(null);
  const [ex, setEx] = useState(null);
  const [err, setErr] = useState("");
  const [tsForm, setTsForm] = useState({ engagement_id: "", role: "consultant", hours: "", billable: true, activity: "" });
  const [exForm, setExForm] = useState({ engagement_id: "", category: "Travel", amount: "", billable: true, note: "", receipt: "", ocr_engine: "" });
  const [appr, setAppr] = useState(null);
  const [ocrMsg, setOcrMsg] = useState("");

  async function load() {
    const o = encodeURIComponent(ownerId());
    try {
      const [c, t, e] = await Promise.all([
        fetch(`/api/firm?view=cockpit&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
        fetch(`/api/firm?view=timesheets&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
        fetch(`/api/firm?view=expenses&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
      ]);
      if (c.error) setErr(c.error); else { setCk(c); setTs(t); setEx(e); }
    } catch (e) { setErr(e.message); }
  }
  async function loadApprovals(r) {
    try { const res = await fetch(`/api/firm?view=approvals&owner=${encodeURIComponent(ownerId())}&role=${encodeURIComponent(r)}`, { cache: "no-store" }); setAppr(await res.json()); } catch {}
  }
  useEffect(() => { (async () => { try { const r = await fetch("/api/firm?view=rbac"); setRbac(await r.json()); } catch {} })(); load(); }, []);
  useEffect(() => { if (role) loadApprovals(role); }, [role]); // eslint-disable-line

  async function onReceipt(file) {
    if (!file) return;
    setOcrMsg("Reading receipt…");
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = String(reader.result).split(",")[1] || "";
      try {
        const r = await fetch("/api/firm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "ocr", image_base64: b64 }) });
        const d = await r.json();
        if (d.ok) {
          setExForm((f) => ({ ...f, amount: d.amount || f.amount, category: d.category || f.category, note: (d.merchant ? `${d.merchant}${d.date ? " · " + d.date : ""}` : f.note), receipt: file.name, ocr_engine: d.engine }));
          setOcrMsg(`✓ OCR (${d.engine}): ₹${d.amount || "?"} · ${d.category}`);
        } else { setExForm((f) => ({ ...f, receipt: file.name })); setOcrMsg(d.note || d.error || "Receipt attached — enter amount manually."); }
      } catch (e) { setOcrMsg("OCR failed; enter manually."); }
    };
    reader.readAsDataURL(file);
  }

  const allowed = useMemo(() => new Set((rbac?.role_access?.[role]) || []), [rbac, role]);
  const can = (m) => allowed.has(m);

  async function submitTs() {
    if (!tsForm.hours) return;
    await fetch("/api/firm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "timesheet", owner: ownerId(), ...tsForm }) });
    setTsForm({ ...tsForm, hours: "", activity: "" }); load();
  }
  async function submitEx() {
    if (!exForm.amount) return;
    await fetch("/api/firm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "expense", owner: ownerId(), role, ...exForm }) });
    setExForm({ engagement_id: "", category: "Travel", amount: "", billable: true, note: "", receipt: "", ocr_engine: "" }); setOcrMsg(""); load(); loadApprovals(role);
  }
  async function decideEx(id, status) {
    await fetch("/api/firm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "expense_status", owner: ownerId(), id, status, approver_role: role }) });
    load(); loadApprovals(role);
  }

  const maxPeriod = Math.max(1, ...((ck?.revenue_by_period || []).map((p) => p.value)));

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Consulting OS <span className="text-indigo-600">· Firm Cockpit</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/engage" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Engagements</a>
            <a href="/catalog" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Catalog</a>
          </div>
        </div>
      </nav>

      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
          <div className="inline-flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full text-[11px] font-bold mb-4">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" /> Consulting-firm ERP · Engagements · Timesheets · Billing · Finance
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Firm Cockpit</h1>
          <p className="text-slate-300 mt-2 max-w-2xl text-sm">Firm-wide billing, CAGR, utilization and the AI-run engagement portfolio — what a Senior Partner sees. Switch role to see RBAC-gated modules.</p>
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-bold text-slate-400">View as:</span>
            {(rbac?.roles || ["senior_partner"]).map((r) => (
              <button key={r} onClick={() => setRole(r)} className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${role === r ? "bg-white text-indigo-700 border-white" : "bg-white/10 border-white/20 text-white"}`}>{r.replace(/_/g, " ")}</button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {err && <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 font-semibold">{err}</div>}

        {/* RBAC module strip */}
        {rbac && (
          <section>
            <div className="text-[11px] uppercase tracking-wide text-slate-400 font-bold mb-2">Modules — access for “{role.replace(/_/g, " ")}”</div>
            <div className="flex flex-wrap gap-2">
              {rbac.modules.map((m) => (
                <span key={m.key} className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border ${can(m.key) ? "bg-white border-slate-200" : "bg-slate-100 border-slate-200 text-slate-300 line-through"}`} title={m.desc}>{m.icon} {m.name}</span>
              ))}
            </div>
          </section>
        )}

        {!can("firm_cockpit") && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-4 text-sm font-semibold">
            The “{role.replace(/_/g, " ")}” role can’t see the Firm Cockpit. Switch to Senior Partner / Partner / Finance to view firm finance.
          </div>
        )}

        {can("firm_cockpit") && ck && (
          <>
            {/* Top metrics */}
            <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {[["Engagements", ck.engagements], ["Contracted", ck.contracted_label], ["Recognised", ck.recognised_label],
                ["CAGR", ck.cagr_pct != null ? `${ck.cagr_pct}%` : "n/a"], ["Utilization", `${ck.utilization_pct}%`], ["Gross margin", ck.gross_margin_pct != null ? `${ck.gross_margin_pct}%` : "n/a"]].map(([k, v], i) => (
                <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4">
                  <div className="text-[10px] uppercase tracking-wide text-slate-400 font-bold">{k}</div>
                  <div className="text-xl font-black mt-0.5">{v}</div>
                </div>
              ))}
            </section>

            {/* Revenue by period + by type */}
            <section className="grid md:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-3">Booked fees by period {ck.cagr_pct != null && <span className="text-emerald-600">· CAGR {ck.cagr_pct}%</span>}</div>
                {(ck.revenue_by_period || []).length === 0 && <p className="text-sm text-slate-400">Run engagements in /engage to populate.</p>}
                <div className="space-y-2">
                  {(ck.revenue_by_period || []).map((p, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-16 text-[11px] text-slate-500 font-semibold">{p.period}</span>
                      <div className="flex-1 bg-slate-100 rounded-full h-3"><div className="bg-indigo-500 h-3 rounded-full" style={{ width: `${(p.value / maxPeriod) * 100}%` }} /></div>
                      <span className="w-24 text-right text-[12px] font-bold">{p.label}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-3">Revenue by engagement type</div>
                <div className="space-y-1.5">
                  {(ck.by_type || []).map((t, i) => (
                    <div key={i} className="flex justify-between text-sm"><span>{t.type}</span><b>{t.label}</b></div>
                  ))}
                </div>
                <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mt-4 mb-2">By sector</div>
                <div className="flex flex-wrap gap-1.5">{(ck.by_sector || []).map((s, i) => <span key={i} className="text-[11px] bg-slate-100 px-2 py-1 rounded font-semibold">{s.sector}: {s.label}</span>)}</div>
              </div>
            </section>

            {/* Top engagements */}
            <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
              <div className="px-3 py-2 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500 font-bold">Top engagements by fee</div>
              <table className="w-full text-sm"><tbody className="divide-y divide-slate-100">
                {(ck.top_engagements || []).map((t, i) => (
                  <tr key={i}><td className="px-3 py-2 font-semibold">{t.title}</td><td className="px-3 py-2 text-slate-500 text-[12px]">{t.sector}</td><td className="px-3 py-2 text-[12px]">{t.posture}</td><td className="px-3 py-2 text-right font-bold">{t.fee_label}</td></tr>
                ))}
              </tbody></table>
            </section>
          </>
        )}

        {/* Timesheets */}
        {can("timesheets") && ts && (
          <section className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">⏱️ Log time</div>
              <input value={tsForm.engagement_id} onChange={(e) => setTsForm({ ...tsForm, engagement_id: e.target.value })} placeholder="Engagement id (optional)" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm mb-2" />
              <div className="flex gap-2 mb-2">
                <input value={tsForm.hours} onChange={(e) => setTsForm({ ...tsForm, hours: e.target.value })} placeholder="Hours" className="w-20 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
                <label className="flex items-center gap-1 text-[12px]"><input type="checkbox" checked={tsForm.billable} onChange={(e) => setTsForm({ ...tsForm, billable: e.target.checked })} /> billable</label>
              </div>
              <input value={tsForm.activity} onChange={(e) => setTsForm({ ...tsForm, activity: e.target.value })} placeholder="Activity" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm mb-2" />
              <button onClick={submitTs} className="w-full px-3 py-2 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500">Log time</button>
            </div>
            <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-4">
              <div className="flex gap-4 mb-3 text-sm">
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Billable</span><div className="text-lg font-black text-emerald-600">{ts.billable_hours}h</div></div>
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Non-billable</span><div className="text-lg font-black text-slate-500">{ts.nonbillable_hours}h</div></div>
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Utilization</span><div className="text-lg font-black text-indigo-600">{ts.utilization_pct}%</div></div>
              </div>
              <div className="max-h-40 overflow-y-auto text-[12px] space-y-1">
                {(ts.entries || []).slice(0, 12).map((e, i) => (
                  <div key={i} className="flex justify-between border-b border-slate-50 py-1"><span>{e.role} · {e.activity || "—"} {e.engagement_id && <span className="text-slate-400">({e.engagement_id})</span>}</span><span className={e.billable ? "text-emerald-600 font-semibold" : "text-slate-400"}>{e.hours}h {e.billable ? "B" : "NB"}</span></div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Expenses + OCR + approvals */}
        {can("expenses") && ex && (
          <section className="grid md:grid-cols-3 gap-4">
            {/* Submit — everyone EXCEPT partner / senior partner */}
            {!["partner", "senior_partner"].includes(role) ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-4">
                <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">🧾 Submit expense</div>
                <label className="block mb-2">
                  <span className="text-[11px] text-indigo-600 font-semibold cursor-pointer">📎 Upload receipt (OCR auto-fills)</span>
                  <input type="file" accept="image/*,application/pdf" onChange={(e) => onReceipt(e.target.files?.[0])} className="block w-full text-[11px] mt-1" />
                </label>
                {ocrMsg && <div className="text-[11px] text-slate-500 mb-2">{ocrMsg}</div>}
                <input value={exForm.engagement_id} onChange={(e) => setExForm({ ...exForm, engagement_id: e.target.value })} placeholder="Engagement id (optional)" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm mb-2" />
                <div className="flex gap-2 mb-2">
                  <select value={exForm.category} onChange={(e) => setExForm({ ...exForm, category: e.target.value })} className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm">
                    {(ex.categories || []).map((c) => <option key={c}>{c}</option>)}
                  </select>
                  <input value={exForm.amount} onChange={(e) => setExForm({ ...exForm, amount: e.target.value })} placeholder="₹" className="w-24 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
                </div>
                <input value={exForm.note} onChange={(e) => setExForm({ ...exForm, note: e.target.value })} placeholder="Merchant / note" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm mb-2" />
                <label className="flex items-center gap-1 text-[12px] mb-2"><input type="checkbox" checked={exForm.billable} onChange={(e) => setExForm({ ...exForm, billable: e.target.checked })} /> billable to client</label>
                <button onClick={submitEx} className="w-full px-3 py-2 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500">Submit for approval</button>
                <p className="text-[10px] text-slate-400 mt-1.5">Routes to your {exForm && APPR_LABEL(role)} for approval.</p>
              </div>
            ) : (
              <div className="bg-slate-50 rounded-2xl border border-slate-200 p-4 text-[12px] text-slate-500">
                Partners don’t file expenses here — you <b>approve</b> them. See the approvals queue →
              </div>
            )}

            {/* Summary + recent */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="flex gap-4 mb-3 text-sm">
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Billable</span><div className="text-lg font-black text-emerald-600">{ex.billable_label}</div></div>
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Non-bill</span><div className="text-lg font-black text-slate-500">{ex.nonbillable_label}</div></div>
                <div><span className="text-slate-400 text-[11px] uppercase font-bold">Pending</span><div className="text-lg font-black text-amber-600">{ex.pending_approval}</div></div>
              </div>
              <div className="max-h-44 overflow-y-auto text-[12px] space-y-1">
                {(ex.expenses || []).slice(0, 14).map((e, i) => (
                  <div key={i} className="flex justify-between items-center border-b border-slate-50 py-1">
                    <span>{e.category} · ₹{(e.amount || 0).toLocaleString()} {e.billable ? "" : "(NB)"}</span>
                    <span className={`text-[10px] font-bold ${e.status === "Approved" ? "text-emerald-600" : e.status === "Rejected" ? "text-rose-600" : "text-amber-600"}`}>{e.status}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Approvals queue — hierarchy */}
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">✅ Approvals queue · {role.replace(/_/g, " ")}</div>
              {!appr || appr.count === 0 ? (
                <p className="text-[12px] text-slate-400">Nothing awaiting your approval.</p>
              ) : (
                <div className="max-h-52 overflow-y-auto space-y-2">
                  {appr.queue.map((e, i) => (
                    <div key={i} className="border border-slate-100 rounded-lg p-2">
                      <div className="flex justify-between text-[12px]"><span className="font-semibold">{e.category} · ₹{(e.amount || 0).toLocaleString()}</span><span className="text-slate-400">{(e.submit_role || "").replace(/_/g, " ")}</span></div>
                      {e.note && <div className="text-[11px] text-slate-500">{e.note}</div>}
                      <div className="flex gap-1.5 mt-1.5">
                        <button onClick={() => decideEx(e.id, "Approved")} className="text-[10px] bg-emerald-600 text-white px-2 py-0.5 rounded font-bold">Approve</button>
                        <button onClick={() => decideEx(e.id, "Rejected")} className="text-[10px] bg-white border border-rose-200 text-rose-600 px-2 py-0.5 rounded font-bold">Reject</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        <p className="text-[11px] text-slate-400 border-t border-slate-200 pt-4">{ck?.note}</p>
      </main>
    </div>
  );
}
