"use client";

/* Clients & Contracts — client master data + contract management (MSA / SOW /
   Engagement Letter), with stored engagement-letter emails and a billing summary
   wired from signed contracts. Reads /api/clients. Owner = shared firm tenant. */

import { useEffect, useState } from "react";

function ownerId() {
  try { let o = localStorage.getItem("pmguru_owner"); if (!o) { o = "u-" + Math.random().toString(36).slice(2, 11); localStorage.setItem("pmguru_owner", o); } return o; }
  catch { return "demo"; }
}
const ST = { Signed: "bg-emerald-100 text-emerald-700", Active: "bg-emerald-100 text-emerald-700", Sent: "bg-amber-100 text-amber-700", Draft: "bg-slate-100 text-slate-600", Closed: "bg-slate-200 text-slate-600" };

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [billing, setBilling] = useState(null);
  const [sel, setSel] = useState(null); // selected client 360
  const [meta, setMeta] = useState({ types: ["MSA", "SOW", "Engagement Letter", "NDA", "Retainer"], fee_models: ["Time & Materials", "Fixed Fee", "Monthly Retainer", "Outcome-linked (capped)"], statuses: ["Draft", "Sent", "Signed", "Active", "Closed"] });
  const [cf, setCf] = useState({ name: "", industry: "", gstin: "", billing_terms: "Net 30", notes: "" });
  const [kf, setKf] = useState({ client_id: "", type: "Engagement Letter", fee_model: "Fixed Fee", contract_value: "", engagement_id: "", letter_text: "" });
  const [mailFor, setMailFor] = useState(null);
  const [mail, setMail] = useState({ subject: "", from: "", to: "", body: "" });

  async function load() {
    const o = encodeURIComponent(ownerId());
    const [c, k, b] = await Promise.all([
      fetch(`/api/clients?view=clients&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
      fetch(`/api/clients?view=contracts&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
      fetch(`/api/clients?view=billing&owner=${o}`, { cache: "no-store" }).then((r) => r.json()),
    ]);
    if (c.clients) setClients(c.clients);
    if (k.contracts) { setContracts(k.contracts); if (k.types) setMeta(k); }
    if (!b.error) setBilling(b);
  }
  useEffect(() => { load(); }, []);

  async function post(payload) { await fetch("/api/clients", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ owner: ownerId(), ...payload }) }); }
  async function addClient() { if (!cf.name) return; await post({ action: "add_client", ...cf }); setCf({ name: "", industry: "", gstin: "", billing_terms: "Net 30", notes: "" }); load(); }
  async function addContract() { if (!kf.client_id || !kf.contract_value) return; await post({ action: "add_contract", ...kf }); setKf({ ...kf, contract_value: "", letter_text: "" }); load(); }
  async function signContract(id) { await post({ action: "contract_status", id, status: "Signed", signed_date: new Date().toISOString().slice(0, 10) }); load(); }
  async function sendMail() { if (!mail.subject && !mail.body) return; await post({ action: "contract_email", id: mailFor, ...mail }); setMail({ subject: "", from: "", to: "", body: "" }); setMailFor(null); load(); }
  async function attachDoc(contractId, file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = String(reader.result).split(",")[1] || "";
      const up = await fetch("/api/blob", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ owner: ownerId(), scope: "contract", filename: file.name, content_base64: b64, content_type: file.type }) }).then((r) => r.json());
      if (up.key) { await post({ action: "contract_email", id: contractId, subject: `📎 Document: ${file.name}`, from: "attachment", to: up.key, body: up.url || up.key }); load(); }
    };
    reader.readAsDataURL(file);
  }
  async function open360(cid) { const d = await fetch(`/api/clients?view=client&owner=${encodeURIComponent(ownerId())}&id=${cid}`).then((r) => r.json()); setSel(d); }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="sticky top-0 z-30 bg-white/85 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <a href="/auto" className="font-black tracking-tight text-sm sm:text-base">Consulting OS <span className="text-indigo-600">· Clients & Contracts</span></a>
          <div className="flex items-center gap-1 text-sm">
            <a href="/firm" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Firm Cockpit</a>
            <a href="/engage" className="px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-semibold">Engagements</a>
          </div>
        </div>
      </nav>

      <header className="bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-9">
          <h1 className="text-3xl font-black tracking-tight">Clients & Contracts</h1>
          <p className="text-slate-300 mt-2 text-sm max-w-2xl">Client master data, contracts (MSA / SOW / Engagement Letter) with stored engagement-letter emails — wired into billing.</p>
          {billing && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
              {[["Clients", billing.clients], ["Contracts", billing.contracts], ["Signed value", billing.signed_label], ["Pipeline", billing.pipeline_label]].map(([k, v], i) => (
                <div key={i} className="bg-white/10 rounded-xl p-3"><div className="text-[10px] uppercase tracking-wide text-slate-300 font-bold">{k}</div><div className="text-lg font-black">{v}</div></div>
              ))}
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 grid lg:grid-cols-3 gap-6">
        {/* Clients */}
        <section className="space-y-3">
          <h2 className="font-black">🏢 Clients</h2>
          <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-2">
            <input value={cf.name} onChange={(e) => setCf({ ...cf, name: e.target.value })} placeholder="Client name *" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            <div className="flex gap-2">
              <input value={cf.industry} onChange={(e) => setCf({ ...cf, industry: e.target.value })} placeholder="Industry" className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
              <input value={cf.billing_terms} onChange={(e) => setCf({ ...cf, billing_terms: e.target.value })} placeholder="Terms" className="w-24 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            </div>
            <input value={cf.gstin} onChange={(e) => setCf({ ...cf, gstin: e.target.value })} placeholder="GSTIN" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            <button onClick={addClient} className="w-full px-3 py-2 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500">+ Add client</button>
          </div>
          <div className="space-y-1.5">
            {clients.map((c) => (
              <button key={c.id} onClick={() => { open360(c.id); setKf((k) => ({ ...k, client_id: c.id })); }} className={`w-full text-left bg-white rounded-xl border p-3 hover:border-indigo-300 ${sel?.client?.id === c.id ? "border-indigo-400 ring-1 ring-indigo-100" : "border-slate-200"}`}>
                <div className="font-bold text-sm">{c.name}</div>
                <div className="text-[11px] text-slate-400">{c.industry || "—"} · {c.billing_terms} · {c.gstin || "no GSTIN"}</div>
              </button>
            ))}
            {clients.length === 0 && <p className="text-xs text-slate-400">No clients yet.</p>}
          </div>
        </section>

        {/* Contracts */}
        <section className="space-y-3">
          <h2 className="font-black">📜 New contract</h2>
          <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-2">
            <select value={kf.client_id} onChange={(e) => setKf({ ...kf, client_id: e.target.value })} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm">
              <option value="">Select client *</option>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <div className="flex gap-2">
              <select value={kf.type} onChange={(e) => setKf({ ...kf, type: e.target.value })} className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm">{meta.types.map((t) => <option key={t}>{t}</option>)}</select>
              <select value={kf.fee_model} onChange={(e) => setKf({ ...kf, fee_model: e.target.value })} className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm">{meta.fee_models.map((t) => <option key={t}>{t}</option>)}</select>
            </div>
            <div className="flex gap-2">
              <input value={kf.contract_value} onChange={(e) => setKf({ ...kf, contract_value: e.target.value })} placeholder="Contract value ₹ *" className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
              <input value={kf.engagement_id} onChange={(e) => setKf({ ...kf, engagement_id: e.target.value })} placeholder="Engagement id" className="w-28 border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            </div>
            <textarea value={kf.letter_text} onChange={(e) => setKf({ ...kf, letter_text: e.target.value })} rows={3} placeholder="Engagement-letter text (optional)" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm" />
            <button onClick={addContract} className="w-full px-3 py-2 rounded-lg bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-500">+ Create contract</button>
          </div>
          {billing?.by_client?.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold mb-2">Billing by client</div>
              {billing.by_client.map((c, i) => <div key={i} className="flex justify-between text-sm"><span>{c.client}</span><b>{c.label}</b></div>)}
            </div>
          )}
        </section>

        {/* Contract list / client 360 */}
        <section className="space-y-3">
          <h2 className="font-black">{sel ? `📂 ${sel.client?.name} — 360` : "📑 All contracts"}</h2>
          {(sel ? sel.contracts : contracts).map((k) => (
            <div key={k.id} className="bg-white rounded-2xl border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="font-bold text-sm">{k.type} · {k.value_label || ("₹" + (k.contract_value || 0).toLocaleString())}</div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${ST[k.status] || ST.Draft}`}>{k.status}</span>
              </div>
              <div className="text-[11px] text-slate-400">{k.client_name || sel?.client?.name} · {k.fee_model}{k.engagement_id ? ` · eng ${k.engagement_id}` : ""}</div>
              {k.letter_text && <div className="text-[11px] text-slate-500 mt-1 line-clamp-2">✉ {k.letter_text}</div>}
              {(k.emails || []).length > 0 && <div className="text-[10px] text-indigo-600 mt-1">📧 {k.emails.length} engagement-letter mail(s) stored</div>}
              <div className="flex gap-1.5 mt-2">
                {k.status !== "Signed" && k.status !== "Active" && <button onClick={() => signContract(k.id)} className="text-[10px] bg-emerald-600 text-white px-2 py-0.5 rounded font-bold">Mark signed</button>}
                <button onClick={() => setMailFor(mailFor === k.id ? null : k.id)} className="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-bold">Store letter mail</button>
                <label className="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-bold cursor-pointer">📎 Attach doc<input type="file" className="hidden" onChange={(e) => attachDoc(k.id, e.target.files?.[0])} /></label>
              </div>
              {mailFor === k.id && (
                <div className="mt-2 bg-slate-50 rounded-lg p-2 space-y-1.5">
                  <input value={mail.subject} onChange={(e) => setMail({ ...mail, subject: e.target.value })} placeholder="Subject" className="w-full border border-slate-200 rounded px-2 py-1 text-[12px]" />
                  <div className="flex gap-1.5">
                    <input value={mail.from} onChange={(e) => setMail({ ...mail, from: e.target.value })} placeholder="From" className="flex-1 border border-slate-200 rounded px-2 py-1 text-[12px]" />
                    <input value={mail.to} onChange={(e) => setMail({ ...mail, to: e.target.value })} placeholder="To" className="flex-1 border border-slate-200 rounded px-2 py-1 text-[12px]" />
                  </div>
                  <textarea value={mail.body} onChange={(e) => setMail({ ...mail, body: e.target.value })} rows={2} placeholder="Email body / paste engagement letter" className="w-full border border-slate-200 rounded px-2 py-1 text-[12px]" />
                  <button onClick={sendMail} className="px-3 py-1 rounded bg-indigo-600 text-white text-[12px] font-bold">Store mail</button>
                </div>
              )}
              {(k.emails || []).map((m, i) => (
                <div key={i} className="mt-1.5 border-l-2 border-indigo-200 pl-2 text-[11px]"><b>{m.subject}</b> <span className="text-slate-400">{m.from}→{m.to}</span><div className="text-slate-500">{m.body}</div></div>
              ))}
            </div>
          ))}
          {(sel ? sel.contracts : contracts).length === 0 && <p className="text-xs text-slate-400">No contracts yet.</p>}
        </section>
      </main>
    </div>
  );
}
