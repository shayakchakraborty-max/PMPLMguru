"""
Free-LLM stack — optional augmentation layer.
Tries free/low-cost providers in order of whichever API keys are present:
  Groq -> Gemini -> Mistral -> HuggingFace -> OpenRouter
Graceful by design: if NO keys are set, augment() returns None instantly so the
deterministic engine stays swift and always-on. When keys exist, it adds a
research-grade narrative on top of the deterministic output.

Set any of these env vars on Railway to enable:
  GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, HF_API_KEY, OPENROUTER_API_KEY
"""
import os
import httpx

# Provider order + their default free/cheap models.
_PROVIDERS = [
    ("groq",       "GROQ_API_KEY"),
    ("gemini",     "GEMINI_API_KEY"),
    ("mistral",    "MISTRAL_API_KEY"),
    ("huggingface","HF_API_KEY"),
    ("openrouter", "OPENROUTER_API_KEY"),
]


def available() -> list:
    """Which providers have a key configured."""
    return [name for name, env in _PROVIDERS if os.getenv(env, "").strip()]


def _call(provider: str, system: str, user: str, max_tokens: int) -> str:
    key = os.getenv(dict(_PROVIDERS)[provider], "").strip()
    timeout = 30
    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {"model": "llama-3.3-70b-versatile", "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            return r.json()["choices"][0]["message"]["content"]
    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, json={"contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
                                  "generationConfig": {"maxOutputTokens": max_tokens}})
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    if provider == "mistral":
        url = "https://api.mistral.ai/v1/chat/completions"
        payload = {"model": "mistral-small-latest", "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            return r.json()["choices"][0]["message"]["content"]
    if provider == "huggingface":
        url = "https://router.huggingface.co/v1/chat/completions"
        payload = {"model": "meta-llama/Llama-3.3-70B-Instruct:novita", "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            return r.json()["choices"][0]["message"]["content"]
    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {"model": "meta-llama/llama-3.3-70b-instruct:free", "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            return r.json()["choices"][0]["message"]["content"]
    raise ValueError(f"unknown provider {provider}")


def augment(system: str, user: str, max_tokens: int = 900) -> dict:
    """Try providers in order; return {text, provider} or {text:None, provider:None}.
    Never raises — augmentation is best-effort."""
    for provider in available():
        try:
            text = _call(provider, system, user, max_tokens)
            if text and text.strip():
                return {"text": text.strip(), "provider": provider}
        except Exception as e:
            print(f"[llm_stack] {provider} failed: {str(e)[:120]}", flush=True)
            continue
    return {"text": None, "provider": None}
