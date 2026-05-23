# ============================================================
#  experiment_designer.py
#  Uses Claude API to generate BehaviorSpace XML experiments
# ============================================================

import json
import anthropic
from pathlib import Path
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS,
    N_SAMPLES, N_REPLICATES, TICKS_PER_RUN, RANDOM_SEEDS
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def design_experiments(
    submodel_name: str,
    parameters: list[dict],
    experiment_dir: Path
) -> str:
    """
    Send parameter catalog to Claude and receive BehaviorSpace XML.
    Returns the XML string and saves it to disk.
    """

    # Filter to high and medium priority parameters for efficiency
    priority_params = [
        p for p in parameters
        if p.get("sensitivity_priority") in ["high", "medium"]
    ]

    if not priority_params:
        priority_params = parameters[:10]  # fallback to first 10

    system_prompt = """
    You are an ecological modeler designing sensitivity analyses for
    a NetLogo agent-based model of migratory fish called GoFish.

    Generate a NetLogo BehaviorSpace XML experiment file that includes:

    1. ONE-AT-A-TIME experiments: For each parameter, vary it across
       its plausible range in 10 evenly spaced steps while holding
       all other parameters at their default values.

    2. INTERACTION experiments: For pairs of parameters that appear
       together in the same equation, vary both simultaneously using
       a 5x5 factorial design.

    3. EXTREME VALUE tests: Test each parameter at its biological
       minimum and maximum simultaneously to find failure modes.

    Format requirements:
    - Valid NetLogo BehaviorSpace XML
    - Each experiment has a unique descriptive name
    - Include these output metrics for every experiment:
        [metabolism-rate] [energy] [mehg-total] [hg-total]
        [ionregulatory-stress] [chloride-cell-density]
        [swim-efficiency] [lipid-catabolism-efficiency]
    - Set time-limit to {ticks} ticks
    - Set repetitions to {reps}
    - Include random seeds: {seeds}

    Return ONLY valid XML. No explanation or markdown fences.
    """.format(
        ticks = TICKS_PER_RUN,
        reps  = N_REPLICATES,
        seeds = RANDOM_SEEDS
    ).strip()

    user_message = f"""
    Submodel: {submodel_name}

    Parameters to test:
    {json.dumps(priority_params, indent=2)}

    Generate the BehaviorSpace XML experiment file.
    """.strip()

    print(f"  Designing experiments for: {submodel_name}")
    print(f"  Testing {len(priority_params)} priority parameters")

    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = MAX_TOKENS,
        messages   = [{"role": "user", "content": user_message}],
        system     = system_prompt
    )

    xml_content = response.content[0].text.strip()

    # Strip markdown fences if present
    if "```xml" in xml_content:
        xml_content = xml_content.split("```xml")[1].split("```")[0].strip()
    elif "```" in xml_content:
        xml_content = xml_content.split("```")[1].split("```")[0].strip()

    # Save to file
    out_path = experiment_dir / f"{submodel_name}_experiments.xml"
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"  Saved: {out_path}")

    return xml_content


def design_cross_submodel_experiments(
    catalog: dict,
    experiment_dir: Path
) -> str:
    """
    Design experiments that test parameter propagation across submodels.
    Identifies parameters that appear in multiple submodels and tests
    their cascading effects through the full model.
    """

    # Find parameters that appear in multiple submodels
    cross_submodel = {}
    for submodel, params in catalog.items():
        for p in params:
            effects = p.get("cross_submodel_effects", [])
            if effects:
                name = p["name"]
                if name not in cross_submodel:
                    cross_submodel[name] = {
                        "parameter": p,
                        "origin_submodel": submodel,
                        "affects": effects
                    }

    if not cross_submodel:
        print("  No cross-submodel parameters identified")
        return ""

    print(f"  Found {len(cross_submodel)} cross-submodel parameters")

    system_prompt = """
    You are an ecological modeler designing cross-submodel sensitivity
    analyses for a modular fish ABM. These parameters propagate their
    effects through multiple coupled submodels.

    Generate BehaviorSpace XML experiments that:
    1. Vary each cross-submodel parameter across its full range
    2. Record outputs from ALL affected downstream submodels
    3. Track how sensitivity propagates through the submodel chain

    This reveals emergent sensitivity that single-submodel tests miss.

    Return ONLY valid XML.
    """.strip()

    user_message = f"""
    Cross-submodel parameters identified:
    {json.dumps(cross_submodel, indent=2)}

    Generate cross-submodel sensitivity experiments.
    """.strip()

    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = MAX_TOKENS,
        messages   = [{"role": "user", "content": user_message}],
        system     = system_prompt
    )

    xml_content = response.content[0].text.strip()
    if "```xml" in xml_content:
        xml_content = xml_content.split("```xml")[1].split("```")[0].strip()

    out_path = experiment_dir / "cross_submodel_experiments.xml"
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"  Saved cross-submodel experiments: {out_path}")

    return xml_content