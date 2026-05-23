# ============================================================
#  llm_client.py — unified LLM interface (Groq default)
# ============================================================

import time
import requests
from config import (
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL_FAST, GROQ_MODEL_QUALITY, GROQ_BASE_URL,
    XAI_API_KEY, XAI_MODEL, XAI_BASE_URL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    MAX_TOKENS
)


def call_llm(
    system_prompt: str,
    user_message:  str,
    quality:       str = "fast"   # "fast" or "quality"
) -> str:
    """
    Route to the configured LLM provider.
    quality="fast"    → llama-3.1-8b-instant  (parameter extraction)
    quality="quality" → llama-3.3-70b-versatile (reports, experiments)
    """
    providers = {
        "groq"      : _call_groq,
        "xai"       : _call_xai,
        "google"    : _call_google,
        "ollama"    : _call_ollama,
        "anthropic" : _call_anthropic,
    }

    if LLM_PROVIDER not in providers:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. "
            f"Available: {list(providers.keys())}"
        )

    model = GROQ_MODEL_QUALITY if quality == "quality" else GROQ_MODEL_FAST
    print(f"    [LLM: {LLM_PROVIDER} | {model} | quality={quality}]")
    return providers[LLM_PROVIDER](system_prompt, user_message, quality)


# ------------------------------------------------------------
# Groq
# ------------------------------------------------------------

def _call_groq(
    system_prompt: str,
    user_message:  str,
    quality:       str = "fast"
) -> str:

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set in .env\n"
            "Get your key at console.groq.com"
        )

    model = GROQ_MODEL_QUALITY if quality == "quality" else GROQ_MODEL_FAST

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type" : "application/json",
    }
    payload = {
        "model"      : model,
        "max_tokens" : MAX_TOKENS,
        "temperature": 0.1,
        "messages"   : [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }

    for attempt in range(3):
        response = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers = headers,
            json    = payload,
            timeout = 60,
        )
        if response.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s (attempt {attempt+1}/3)")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    raise RuntimeError("Groq rate limit exceeded after 3 retries")


# ------------------------------------------------------------
# xAI Grok
# ------------------------------------------------------------

def _call_xai(system_prompt, user_message, quality="fast"):
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type" : "application/json",
    }
    payload = {
        "model"      : XAI_MODEL,
        "max_tokens" : MAX_TOKENS,
        "messages"   : [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    response = requests.post(
        f"{XAI_BASE_URL}/chat/completions",
        headers=headers, json=payload, timeout=120
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ------------------------------------------------------------
# Google Gemini
# ------------------------------------------------------------

def _call_google(system_prompt, user_message, quality="fast"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(
            model_name=GOOGLE_MODEL,
            system_instruction=system_prompt
        )
        return model.generate_content(user_message).text.strip()
    except ImportError:
        raise ImportError("Run: pip install google-generativeai")


# ------------------------------------------------------------
# Ollama (local)
# ------------------------------------------------------------

def _call_ollama(system_prompt, user_message, quality="fast"):
    payload = {
        "model"   : OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "stream" : False,
        "options": {"num_predict": MAX_TOKENS},
    }
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload, timeout=300
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ------------------------------------------------------------
# Anthropic Claude
# ------------------------------------------------------------

def _call_anthropic(system_prompt, user_message, quality="fast"):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return resp.content[0].text.strip()
    except ImportError:
        raise ImportError("Run: pip install anthropic")