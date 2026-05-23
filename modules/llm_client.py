# ============================================================
#  modules/llm_client.py
#  Unified LLM client supporting Groq, xAI, Google, 
#  Ollama, and Anthropic
# ============================================================

import os
import json
import requests
from config import (
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL,
    XAI_API_KEY, XAI_MODEL, XAI_BASE_URL,
    GOOGLE_API_KEY, GOOGLE_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    MAX_TOKENS
)


def call_llm(system_prompt: str, user_message: str) -> str:
    """
    Unified LLM call that works with any configured provider.
    Returns the response text as a string.
    """

    providers = {
        "groq"      : _call_groq,
        "xai"       : _call_xai,
        "google"    : _call_google,
        "ollama"    : _call_ollama,
        "anthropic" : _call_anthropic
    }

    if LLM_PROVIDER not in providers:
        raise ValueError(
            f"Unknown LLM provider: {LLM_PROVIDER}\n"
            f"Available: {list(providers.keys())}"
        )

    print(f"    [LLM: {LLM_PROVIDER}]")
    return providers[LLM_PROVIDER](system_prompt, user_message)


# ------------------------------------------------------------
# Groq
# ------------------------------------------------------------

def _call_groq(system_prompt: str, user_message: str) -> str:
    """
    Call Groq API using OpenAI-compatible endpoint.
    Groq is very fast — typically under 2 seconds per call.
    """

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set in .env file.\n"
            "Get your key at console.groq.com"
        )

    headers = {
        "Authorization" : f"Bearer {GROQ_API_KEY}",
        "Content-Type"  : "application/json"
    }

    payload = {
        "model"      : GROQ_MODEL,
        "max_tokens" : MAX_TOKENS,
        "temperature": 0.1,  # low temperature for structured outputs
        "messages"   : [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    }

    response = requests.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers = headers,
        json    = payload,
        timeout = 60
    )

    if response.status_code == 429:
        # Rate limit hit — wait and retry
        import time
        print("    Rate limit hit, waiting 30 seconds...")
        time.sleep(30)
        return _call_groq(system_prompt, user_message)

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ------------------------------------------------------------
# xAI Grok
# ------------------------------------------------------------

def _call_xai(system_prompt: str, user_message: str) -> str:
    """Call xAI Grok API using OpenAI-compatible endpoint."""

    headers = {
        "Authorization" : f"Bearer {XAI_API_KEY}",
        "Content-Type"  : "application/json"
    }

    payload = {
        "model"      : XAI_MODEL,
        "max_tokens" : MAX_TOKENS,
        "messages"   : [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    }

    response = requests.post(
        f"{XAI_BASE_URL}/chat/completions",
        headers = headers,
        json    = payload,
        timeout = 120
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ------------------------------------------------------------
# Google Gemini
# ------------------------------------------------------------

def _call_google(system_prompt: str, user_message: str) -> str:
    """Call Google Gemini API."""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(
            model_name        = GOOGLE_MODEL,
            system_instruction = system_prompt
        )
        response = model.generate_content(user_message)
        return response.text.strip()

    except ImportError:
        raise ImportError(
            "Google Generative AI package not installed.\n"
            "Run: pip install google-generativeai"
        )


# ------------------------------------------------------------
# Ollama local
# ------------------------------------------------------------

def _call_ollama(system_prompt: str, user_message: str) -> str:
    """Call local Ollama instance. No API key required."""

    payload = {
        "model"   : OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "stream"  : False,
        "options" : {"num_predict": MAX_TOKENS}
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json    = payload,
        timeout = 300
    )

    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ------------------------------------------------------------
# Anthropic Claude
# ------------------------------------------------------------

def _call_anthropic(system_prompt: str, user_message: str) -> str:
    """Call Anthropic Claude API."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model      = CLAUDE_MODEL,
            max_tokens = MAX_TOKENS,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_message}]
        )
        return response.content[0].text.strip()

    except ImportError:
        raise ImportError(
            "Anthropic package not installed.\n"
            "Run: pip install anthropic"
        )
    
def call_llm(
    system_prompt : str,
    user_message  : str,
    quality       : str = "fast"   # "fast" or "quality"
) -> str:
    """
    Unified LLM call that works with any configured provider.
    Quality parameter can be used to select different models if supported.
    Returns the response text as a string.
    """

    providers = {
        "groq"      : _call_groq,
        "xai"       : _call_xai,
        "google"    : _call_google,
        "ollama"    : _call_ollama,
        "anthropic" : _call_anthropic
    }

    if LLM_PROVIDER not in providers:
        raise ValueError(
            f"Unknown LLM provider: {LLM_PROVIDER}\n"
            f"Available: {list(providers.keys())}"
        )

    print(f"    [LLM: {LLM_PROVIDER}, Quality: {quality}]")
    return providers[LLM_PROVIDER](system_prompt, user_message)