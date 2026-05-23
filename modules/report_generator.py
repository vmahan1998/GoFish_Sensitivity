# ============================================================
#  report_generator.py
#  Uses Claude API to generate plain language sensitivity reports
# ============================================================

import anthropic
import pandas as pd
from pathlib import Path
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_submodel_report(
    submodel_name: str,
    parameters: list[dict],
    sensitivity_df: pd.DataFrame,
    propagation_df: pd.DataFrame,
    report_dir: Path
) -> str:
    """
    Send sensitivity results to Claude and receive a formatted report.
    """

    # Summarize top sensitive parameters
    top_params = sensitivity_df.head(10).to_dict(orient="records")

    # Summarize propagation effects
    propagation_summary = propagation_df[
        propagation_df["origin_submodel"] == submodel_name
    ].to_dict(orient="records") if not propagation_df.empty else []

    system_prompt = """
    You are an ecological modeler writing a sensitivity analysis report
    for a migratory fish agent-based model called GoFish. Your audience
    includes both computational ecologists and fisheries managers.

    Write a sensitivity analysis report section that includes:

    1. PARAMETER SENSITIVITY SUMMARY
       Which parameters drive the most variation in model outputs and why
       this matters ecologically for anadromous fish behavior and
       contaminant exposure.

    2. CRITICAL PARAMETERS
       Which parameters most need precise empirical values versus those
       the model is robust to. Frame this as guidance for field work
       and literature review.

    3. CROSS-SUBMODEL PROPAGATION
       How sensitivity in this submodel propagates to affect downstream
       submodels. Explain the ecological mechanism behind each propagation
       pathway.

    4. ANOMALIES AND EDGE CASES
       Any parameter combinations that produced biologically unrealistic
       outputs and what this tells us about model assumptions.

    5. MANAGEMENT IMPLICATIONS
       What the sensitivity results mean for using this submodel in
       applied management contexts such as mercury risk assessment
       and restoration planning.

    Write in clear scientific prose. Use specific parameter names and
    values. Format as a manuscript-ready methods section subsection.
    Length: 400 to 600 words.
    """.strip()

    user_message = f"""
    Submodel: {submodel_name}

    Top sensitive parameters:
    {pd.DataFrame(top_params).to_string()}

    Cross-submodel propagation effects:
    {pd.DataFrame(propagation_summary).to_string() 
     if propagation_summary else "None identified"}

    All parameters in this submodel:
    {[p['name'] for p in parameters]}

    Write the sensitivity analysis report section.
    """.strip()

    print(f"  Generating report for: {submodel_name}")

    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = MAX_TOKENS,
        messages   = [{"role": "user", "content": user_message}],
        system     = system_prompt
    )

    report_text = response.content[0].text.strip()

    # Save report
    out_path = report_dir / f"{submodel_name}_sensitivity_report.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"  Saved report: {out_path}")

    return report_text


def generate_full_library_report(
    submodel_reports: dict,
    propagation_df: pd.DataFrame,
    report_dir: Path
) -> str:
    """
    Generate a combined sensitivity analysis report for the full
    GoFish library including cross-submodel propagation summary.
    """

    system_prompt = """
    You are an ecological modeler writing the sensitivity analysis
    section of a methods paper describing the GoFish agent-based
    modeling library for migratory fish.

    Synthesize the individual submodel sensitivity analyses into a
    cohesive library-level sensitivity assessment that:

    1. Identifies the parameters that most influence model behavior
       across the full library not just individual submodels

    2. Describes the most important cross-submodel sensitivity
       propagation pathways and their ecological significance

    3. Provides guidance for researchers adapting GoFish to new
       species or systems about which parameters require careful
       empirical grounding

    4. Compares sensitivity patterns across submodels to identify
       common themes in how the library responds to parameter
       uncertainty

    5. Concludes with a parameter priority table formatted for
       manuscript inclusion

    Write as a complete sensitivity analysis section for submission
    to Ecological Modelling. Length: 800 to 1200 words.
    """.strip()

    combined_summaries = "\n\n".join([
        f"## {name}\n{text[:500]}..."
        for name, text in submodel_reports.items()
    ])

    user_message = f"""
    Individual submodel sensitivity summaries:
    {combined_summaries}

    Cross-submodel propagation summary:
    {propagation_df.to_string() if not propagation_df.empty else "Not available"}

    Generate the full library sensitivity analysis section.
    """.strip()

    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = MAX_TOKENS,
        messages   = [{"role": "user", "content": user_message}],
        system     = system_prompt
    )

    report_text = response.content[0].text.strip()

    out_path = report_dir / "GoFish_Full_Sensitivity_Analysis.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"\nSaved full library report: {out_path}")

    return report_text