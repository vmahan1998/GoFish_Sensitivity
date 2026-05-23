# ============================================================
#  sensitivity_analyzer.py
#  Statistical sensitivity analysis on simulation results
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from SALib.analyze import sobol, morris
from SALib.sample import saltelli


def load_results(results_path: Path) -> pd.DataFrame:
    """Load and clean BehaviorSpace output CSV."""

    df = pd.read_csv(results_path, skiprows=6)
    df.columns = df.columns.str.strip().str.replace(
        r'[\[\]]', '', regex=True
    ).str.replace(' ', '_').str.lower()
    return df


def one_at_a_time_analysis(
    df: pd.DataFrame,
    parameters: list[dict],
    output_metrics: list[str]
) -> pd.DataFrame:
    """
    Compute sensitivity indices for one-at-a-time experiments.
    Returns a dataframe of parameter-output sensitivity scores.
    """

    results = []

    for param in parameters:
        param_name = param["name"].lower().replace("-", "_")

        if param_name not in df.columns:
            continue

        for metric in output_metrics:
            if metric not in df.columns:
                continue

            # Pearson correlation as simple sensitivity index
            corr = df[param_name].corr(df[metric])

            # Coefficient of variation of output across parameter range
            cv = df.groupby(param_name)[metric].mean().std() / \
                 df[metric].mean() if df[metric].mean() != 0 else 0

            results.append({
                "parameter"        : param["name"],
                "output_metric"    : metric,
                "correlation"      : corr,
                "cv_sensitivity"   : cv,
                "abs_sensitivity"  : abs(corr),
                "priority"         : param.get("sensitivity_priority", "unknown"),
                "units"            : param.get("units", ""),
                "description"      : param.get("description", "")
            })

    return pd.DataFrame(results).sort_values(
        "abs_sensitivity", ascending=False
    )


def plot_tornado_diagram(
    sensitivity_df: pd.DataFrame,
    submodel_name: str,
    output_metric: str,
    output_dir: Path
) -> Path:
    """
    Generate a tornado diagram showing parameter sensitivity ranking.
    """

    subset = sensitivity_df[
        sensitivity_df["output_metric"] == output_metric
    ].head(15)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [
        "#1e90ff" if c >= 0 else "#e74c3c"
        for c in subset["correlation"]
    ]

    ax.barh(
        y      = range(len(subset)),
        width  = subset["correlation"],
        color  = colors,
        alpha  = 0.8,
        edgecolor = "#0a3d62"
    )

    ax.set_yticks(range(len(subset)))
    ax.set_yticklabels(subset["parameter"], fontsize=9)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.set_xlabel("Pearson Correlation with Output", fontsize=10)
    ax.set_title(
        f"{submodel_name} — Sensitivity to {output_metric}",
        fontsize=12, fontweight="bold", color="#0a3d62"
    )

    # Color theme matching GoFish site
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f0f8ff")
    fig.patch.set_facecolor("white")

    plt.tight_layout()

    out_path = output_dir / f"{submodel_name}_{output_metric}_tornado.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"  Saved tornado diagram: {out_path}")
    return out_path


def compute_cross_submodel_propagation(
    results_by_submodel: dict,
    catalog: dict
) -> pd.DataFrame:
    """
    Identify how parameter sensitivity in one submodel propagates
    to outputs of downstream submodels.
    """

    propagation_records = []

    for origin_submodel, params in catalog.items():
        for param in params:
            cross_effects = param.get("cross_submodel_effects", [])
            if not cross_effects:
                continue

            param_name = param["name"]

            for downstream in cross_effects:
                if downstream not in results_by_submodel:
                    continue

                downstream_df = results_by_submodel[downstream]
                param_col     = param_name.lower().replace("-", "_")

                if param_col not in downstream_df.columns:
                    continue

                for metric in ["metabolism_rate", "mehg_total",
                               "energy", "ionregulatory_stress"]:
                    if metric not in downstream_df.columns:
                        continue

                    corr = downstream_df[param_col].corr(
                        downstream_df[metric]
                    )

                    propagation_records.append({
                        "origin_submodel"    : origin_submodel,
                        "parameter"          : param_name,
                        "downstream_submodel": downstream,
                        "downstream_metric"  : metric,
                        "propagated_sensitivity": corr
                    })

    return pd.DataFrame(propagation_records)