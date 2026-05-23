# ============================================================
#  parameter_extractor.py
#  Reads Rmd + nls files, sends to Groq, returns parameter catalog
# ============================================================

import json
import re
from pathlib import Path
from config import SUBMODEL_DIR, SUBMODEL_FILES
from modules.llm_client import call_llm


def load_submodel_content(submodel_name: str) -> dict:
    """
    Load ODD text from the Rmd chapter and NetLogo code from the nls file.
    Both live in data/submodels/.
    """
    files   = SUBMODEL_FILES.get(submodel_name, {})
    content = {"odd": "", "code": "", "name": submodel_name}

    # ---- Rmd → ODD text ----
    rmd_path = SUBMODEL_DIR / files.get("rmd", "")
    if rmd_path.exists():
        raw = rmd_path.read_text(encoding="utf-8")
        # Strip R chunk headers, HTML blocks, netlogo blocks (save separately)
        nls_from_rmd = re.findall(
            r"```\{netlogo\}(.*?)```", raw, flags=re.DOTALL
        )
        raw = re.sub(r"```\{r[^}]*\}.*?```",   "", raw, flags=re.DOTALL)
        raw = re.sub(r"```\{=html\}.*?```",     "", raw, flags=re.DOTALL)
        raw = re.sub(r"```\{netlogo\}.*?```",   "", raw, flags=re.DOTALL)
        raw = re.sub(r"<[^>]+>",                "", raw)
        content["odd"]      = raw.strip()
        content["rmd_code"] = "\n".join(nls_from_rmd)
        print(f"  Rmd loaded  : {rmd_path.name}  ({len(content['odd'])} chars)")
    else:
        print(f"  ✗ Rmd missing: {rmd_path}")

    # ---- nls → NetLogo code ----
    nls_path = SUBMODEL_DIR / files.get("nls", "")
    if nls_path.exists():
        content["code"] = nls_path.read_text(encoding="utf-8")
        print(f"  nls loaded  : {nls_path.name}  ({len(content['code'])} chars)")
    else:
        # Fall back to code blocks extracted from the Rmd
        content["code"] = content.get("rmd_code", "")
        print(f"  nls missing : {files.get('nls','')}  (using Rmd code blocks)")

    return content


def extract_parameters(submodel_name: str, content: dict) -> list:
    """Send ODD + code to Groq and return structured parameter list."""

    system_prompt = """
You are an ecological modeler specializing in agent-based models of
migratory fish. Extract every parameter from the submodel ODD
documentation and NetLogo code provided.

Return a JSON array where each element has exactly these fields:
  name                   - variable name as it appears in the code
  description            - plain language description
  current_value          - default or initialized value
  min_value              - biologically plausible minimum (number)
  max_value              - biologically plausible maximum (number)
  units                  - units of measurement
  parameter_type         - species_specific | environmental |
                           physiological_constant | scaling_exponent
  affects_outputs        - list of output variable names
  appears_in_equations   - equation numbers from the ODD e.g. ["C.1","C.5"]
  sensitivity_priority   - high | medium | low
                           (exponents and multipliers = high,
                            additive offsets = low)
  cross_submodel_effects - list of GoFish submodel names downstream
                           of this parameter

Return ONLY a valid JSON array. No markdown fences, no explanation.
""".strip()

    user_message = f"""
Submodel: {submodel_name}

ODD DOCUMENTATION:
{content['odd'][:6000]}

NETLOGO CODE:
{content['code'][:3000]}

Extract all parameters and return as a JSON array.
""".strip()

    print(f"  Calling Groq: {submodel_name}")
    raw = call_llm(system_prompt, user_message, quality="fast")

    # Strip markdown fences if the model added them
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    try:
        params = json.loads(raw.strip())
        print(f"  Extracted   : {len(params)} parameters")
        return params
    except json.JSONDecodeError as e:
        print(f"  Parse error : {e}")
        print(f"  Raw snippet : {raw[:300]}")
        return []


def extract_all_submodels(submodels: list, submodel_dir: Path) -> dict:
    catalog = {}
    for submodel in submodels:
        print(f"\n{'='*50}\nProcessing: {submodel}")
        content = load_submodel_content(submodel)
        params  = extract_parameters(submodel, content)
        catalog[submodel] = params

        out = submodel_dir / f"{submodel}_parameters.json"
        out.write_text(json.dumps(params, indent=2), encoding="utf-8")
        print(f"  Saved: {out.name}")

    return catalog