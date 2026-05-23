# ============================================================
#  report_generator.py — sensitivity reports via Groq
# ============================================================

import pandas as pd
from pathlib import Path
from modules.llm_client import call_llm


def generate_submodel_report(
    submodel_name:  str,
    parameters:     list,
    sensitivity_df: pd.DataFrame,
    propagation_df: pd.DataFrame,
    report_dir:     Path
) -> str:

    top_params   = sensitivity_df.head(10).to_dict(orient="records")
    prop_summary = propagation_df[
        propagation_df["origin_submodel"] == submodel_name
    ].to_dict(orient="records") if not propagation_df.empty else []

    system_prompt = """
You are an ecological modeler writing a sensitivity analysis report
for the GoFish migratory fish ABM. Audience: computational ecologists
and fisheries managers.

Write a report section (400-600 words) covering:
1. Which parameters drive the most output variation and why ecologically
2. Which parameters need precise empirical values vs those the model
   is robust to
3. How sensitivity propagates to downstream submodels
4. Any biologically unrealistic edge cases identified
5. Management implications for mercury risk assessment

Write in clear scientific prose suitable for Ecological Modelling.
""".strip()

    user_message = f"""
Submodel: {submodel_name}

Top sensitive parameters:
{pd.DataFrame(top_params).to_string() if top_params else "None"}

Cross-submodel propagation:
{pd.DataFrame(prop_summary).to_string() if prop_summary else "None identified"}

All parameters: {[p["name"] for p in parameters]}

Write the sensitivity analysis section.
""".strip()

    print(f"  Generating report: {submodel_name}")
    report_text = call_llm(system_prompt, user_message, quality="quality")

    out_path = report_dir / f"{submodel_name}_sensitivity_report.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"  Saved: {out_path.name}")
    return report_text


def generate_full_library_report(
    submodel_reports: dict,
    propagation_df:   pd.DataFrame,
    report_dir:       Path
) -> str:

    system_prompt = """
Write the sensitivity analysis section of a methods paper for the
GoFish agent-based modeling library (Ecological Modelling).
800-1200 words covering:
1. Parameters most influential across the full library
2. Critical cross-submodel propagation pathways and ecological significance
3. Guidance for adapting GoFish to new species or systems
4. Common sensitivity themes across submodels
5. A parameter priority table for manuscript inclusion
""".strip()

    summaries = "\n\n".join([
        f"## {name}\n{text[:400]}..."
        for name, text in submodel_reports.items()
    ])

    user_message = f"""
Submodel summaries:
{summaries}

Cross-submodel propagation:
{propagation_df.to_string() if not propagation_df.empty else "Not available"}

Generate the full library sensitivity analysis section.
""".strip()

    report_text = call_llm(system_prompt, user_message, quality="quality")

    out_path = report_dir / "GoFish_Full_Sensitivity_Analysis.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"\nSaved full report: {out_path.name}")
    return report_text