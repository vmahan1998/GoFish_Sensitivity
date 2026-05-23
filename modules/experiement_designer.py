# ============================================================
#  experiment_designer.py
#  Generates BehaviorSpace XML using Groq
# ============================================================

import json
from pathlib import Path
from config import (
    N_REPLICATES, TICKS_PER_RUN, RANDOM_SEEDS,
    PROTOTYPE_SETUP
)
from modules.llm_client import call_llm


def design_experiments(
    submodel_name: str,
    parameters: list,
    experiment_dir: Path
) -> str:

    priority_params = [
        p for p in parameters
        if p.get("sensitivity_priority") in ["high", "medium"]
    ] or parameters[:10]

    system_prompt = f"""
You are an ecological modeler designing BehaviorSpace sensitivity
experiments for a NetLogo agent-based model of migratory fish (GoFish).

The model uses a prototype setup for sensitivity runs:
{PROTOTYPE_SETUP}

Generate a valid NetLogo BehaviorSpace XML file with:

1. ONE-AT-A-TIME: vary each parameter across its plausible range
   in 10 evenly spaced steps, others held at default values.

2. INTERACTION: for parameter pairs that share an equation,
   use a 5x5 factorial design.

3. EXTREME VALUE: test each parameter at biological min and max.

Requirements:
- Valid NetLogo BehaviorSpace XML
- Unique descriptive experiment names
- Output reporters for every experiment:
    [metabolism-rate] [energy] [mehg-total] [hg-total]
    [ionregulatory-stress] [chloride-cell-density]
    [swim-efficiency] [lipid-catabolism-efficiency]
- time-limit: {TICKS_PER_RUN}
- repetitions: {N_REPLICATES}
- runMetricsEveryStep: false
- Setup command: setup-sensitivity

Return ONLY valid XML with no markdown fences.
""".strip()

    user_message = f"""
Submodel: {submodel_name}

Parameters:
{json.dumps(priority_params, indent=2)}

Generate the BehaviorSpace XML.
""".strip()

    print(f"  Designing experiments: {submodel_name} ({len(priority_params)} params)")
    xml_content = call_llm(system_prompt, user_message, quality="quality")

    # Strip fences
    xml_content = xml_content.strip()
    for fence in ["```xml", "```"]:
        if fence in xml_content:
            xml_content = xml_content.split(fence)[1].split("```")[0].strip()
            break

    out_path = experiment_dir / f"{submodel_name}_experiments.xml"
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"  Saved: {out_path.name}")
    return xml_content


def design_cross_submodel_experiments(catalog: dict, experiment_dir: Path) -> str:

    cross = {}
    for submodel, params in catalog.items():
        for p in params:
            if p.get("cross_submodel_effects"):
                name = p["name"]
                if name not in cross:
                    cross[name] = {
                        "parameter"       : p,
                        "origin_submodel" : submodel,
                        "affects"         : p["cross_submodel_effects"]
                    }

    if not cross:
        print("  No cross-submodel parameters found")
        return ""

    print(f"  Cross-submodel parameters: {len(cross)}")

    system_prompt = f"""
Generate NetLogo BehaviorSpace XML experiments for cross-submodel
sensitivity analysis in GoFish. Each experiment varies a parameter
that propagates effects through multiple submodels and records
outputs from all affected downstream submodels.

Setup command: setup-sensitivity
time-limit: {TICKS_PER_RUN}
repetitions: {N_REPLICATES}

Return ONLY valid XML with no markdown fences.
""".strip()

    user_message = f"""
Cross-submodel parameters:
{json.dumps(cross, indent=2)}

Generate cross-submodel sensitivity experiments.
""".strip()

    xml_content = call_llm(system_prompt, user_message, quality="quality")
    xml_content = xml_content.strip()
    if "```xml" in xml_content:
        xml_content = xml_content.split("```xml")[1].split("```")[0].strip()

    out_path = experiment_dir / "cross_submodel_experiments.xml"
    out_path.write_text(xml_content, encoding="utf-8")
    print(f"  Saved: {out_path.name}")
    return xml_content