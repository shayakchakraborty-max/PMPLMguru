"""
LiteLLM-style smart router — picks the best free AI model for each task.
Supports: Groq (fastest), Gemini (most capable free), HuggingFace (fully free).
Auto-fallback on failure.
"""
import os
import httpx
import json
from typing import Optional

PROVIDERS = ["groq", "gemini", "huggingface"]

# Task-to-provider mapping (smart routing)
TASK_ROUTING = {
    "creative": "gemini",      # Vision, ideation, design
    "structured": "groq",      # User stories, test plans, RAID
    "code": "groq",            # Prototype generation
    "analysis": "gemini",      # Market research, risk
    "default": "groq",
}


async def call_groq(system: str, user: str, max_tokens: int = 1500) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        d = r.json()
        return d["choices"][0]["message"]["content"]


async def call_gemini(system: str, user: str, max_tokens: int = 1500) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={
                "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        d = r.json()
        return d["candidates"][0]["content"]["parts"][0]["text"]


async def call_hf(system: str, user: str, max_tokens: int = 1500) -> str:
    key = os.getenv("HF_API_KEY")
    if not key:
        raise ValueError("HF_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/Llama-3.3-70B-Instruct:novita",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        d = r.json()
        return d["choices"][0]["message"]["content"]


PROVIDER_FNS = {"groq": call_groq, "gemini": call_gemini, "huggingface": call_hf}


async def smart_route(system: str, user: str, task_type: str = "default", max_tokens: int = 1500) -> dict:
    """
    Smart routing with auto-fallback.
    Returns: {output, provider_used, attempts}
    """
    primary = TASK_ROUTING.get(task_type, "groq")
    order = [primary] + [p for p in PROVIDERS if p != primary]
    attempts = []
    for provider in order:
        try:
            fn = PROVIDER_FNS[provider]
            output = await fn(system, user, max_tokens)
            attempts.append({"provider": provider, "status": "success"})
            return {"output": output, "provider_used": provider, "attempts": attempts}
        except Exception as e:
            attempts.append({"provider": provider, "status": "failed", "error": str(e)[:100]})
            continue
    return {"output": "All providers failed", "provider_used": None, "attempts": attempts}
