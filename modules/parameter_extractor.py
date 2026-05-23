# ============================================================
#  parameter_extractor.py
#  Uses Claude API to extract parameters from ODD + NetLogo code
# ============================================================

import json
import anthropic
from pathlib import Path
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_submodel_content(submodel_name: str, submodel_dir: Path) -> dict:
    """
    Load ODD documentation and NetLogo code for a submodel.
    Expects files named:
        {submodel_name}_odd.md
        {submodel_name}_code.nls
    """
    odd_path  = submodel_dir / f"{submodel_name}_odd.md"
    code_path = submodel_dir / f"{submodel_name}_code.nls"

    content = {}

    if odd_path.exists():
        content["odd"] = odd_path.read_text(encoding="utf-8")
    else:
        print(f"  Warning: ODD file not found for {submodel_name}")
        content["odd"] = ""

    if code_path.exists():
        content["code"] = code_path.read_text(encoding="utf-8")
    else:
        print(f"  Warning: Code file not found for {submodel_name}")
        content["code"] = ""

    return content


def extract_parameters(submodel_name: str, content: dict) -> list[dict]:
    """
    Send ODD + code to Claude and extract structured parameter catalog.
    Returns a list of parameter dictionaries.
    """

    system_prompt = """
    You are an ecological modeler specializing in agent-based models
    of migratory fish. Your task is to extract all parameters from
    a submodel's ODD documentation and NetLogo code.

    For each parameter return a JSON object with these fields:
    - name: the parameter name as it appears in the code
    - description: plain language description of what it controls
    - current_value: the default or initialized value
    - min_value: biologically plausible minimum
    - max_value: biologically plausible maximum
    - units: units of measurement
    - parameter_type: one of [species_specific, environmental, 
                               physiological_constant, scaling_exponent]
    - affects_outputs: list of output variables this parameter influences
    - appears_in_equations: list of equation numbers from the ODD
    - sensitivity_priority: one of [high, medium, low] based on where
                             it appears in equations (exponents = high,
                             additive constants = low)
    - cross_submodel_effects: list of other submodels that use this
                               parameter or are affected by its outputs

    Return ONLY a valid JSON array. No preamble or explanation.
    """.strip()

    user_message = f"""
    Submodel: {submodel_name}

    ODD DOCUMENTATION:
    {content['odd']}

    NETLOGO CODE:
    {content['code']}

    Extract all parameters and return as a JSON array.
    """.strip()

    print(f"  Extracting parameters for: {submodel_name}")

    response = client.messages.create(
        model   = CLAUDE_MODEL,
        max_tokens = MAX_TOKENS,
        messages = [
            {"role": "user", "content": user_message}
        ],
        system = system_prompt
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        parameters = json.loads(raw_text)
        print(f"  Found {len(parameters)} parameters")
        return parameters
    except json.JSONDecodeError as e:
        print(f"  JSON parse error for {submodel_name}: {e}")
        print(f"  Raw response: {raw_text[:500]}")
        return []


def extract_all_submodels(submodels: list, submodel_dir: Path) -> dict:
    """
    Extract parameters for all submodels and return a combined catalog.
    """
    catalog = {}

    for submodel in submodels:
        print(f"\nProcessing: {submodel}")
        content    = load_submodel_content(submodel, submodel_dir)
        parameters = extract_parameters(submodel, content)
        catalog[submodel] = parameters

        # Save individual catalog
        out_path = submodel_dir / f"{submodel}_parameters.json"
        with open(out_path, "w") as f:
            json.dump(parameters, f, indent=2)
        print(f"  Saved: {out_path}")

    return catalog