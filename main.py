# ============================================================
#  main.py
#  Full pipeline orchestrator for GoFish sensitivity analysis
# ============================================================

import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from config import (
    SUBMODEL_DIR, EXPERIMENT_DIR, RESULTS_DIR, REPORT_DIR,
    SUBMODELS
)
from modules.parameter_extractor  import extract_all_submodels
from modules.experiment_designer  import (
    design_experiments,
    design_cross_submodel_experiments
)
from modules.netlogo_runner        import run_all_submodel_experiments
from modules.results_processor     import load_results
from modules.sensitivity_analyzer  import (
    one_at_a_time_analysis,
    plot_tornado_diagram,
    compute_cross_submodel_propagation
)
from modules.report_generator      import (
    generate_submodel_report,
    generate_full_library_report
)

OUTPUT_METRICS = [
    "metabolism_rate", "energy", "mehg_total", "hg_total",
    "ionregulatory_stress", "chloride_cell_density",
    "swim_efficiency", "lipid_catabolism_efficiency"
]


def run_pipeline(
    skip_extraction  : bool = False,
    skip_experiments : bool = False,
    skip_running     : bool = False,
    skip_analysis    : bool = False,
    skip_reports     : bool = False
):
    """
    Run the full sensitivity analysis pipeline.
    Skip flags allow restarting from any stage without rerunning
    completed steps.
    """

    print("=" * 60)
    print("GoFish Automated Sensitivity Analysis Pipeline")
    print("=" * 60)

    # ----------------------------------------------------------
    # Stage 1: Extract parameters from ODD documentation
    # ----------------------------------------------------------

    if not skip_extraction:
        print("\n[Stage 1] Extracting parameters from ODD documentation")
        catalog = extract_all_submodels(SUBMODELS, SUBMODEL_DIR)

        catalog_path = SUBMODEL_DIR / "full_parameter_catalog.json"
        with open(catalog_path, "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"\nFull catalog saved: {catalog_path}")
    else:
        print("\n[Stage 1] Loading existing parameter catalog")
        catalog_path = SUBMODEL_DIR / "full_parameter_catalog.json"
        with open(catalog_path) as f:
            catalog = json.load(f)

    # ----------------------------------------------------------
    # Stage 2: Design BehaviorSpace experiments
    # ----------------------------------------------------------

    if not skip_experiments:
        print("\n[Stage 2] Designing BehaviorSpace experiments")
        for submodel in tqdm(SUBMODELS, desc="Designing"):
            if submodel not in catalog:
                continue
            design_experiments(
                submodel_name  = submodel,
                parameters     = catalog[submodel],
                experiment_dir = EXPERIMENT_DIR
            )

        print("\nDesigning cross-submodel experiments")
        design_cross_submodel_experiments(catalog, EXPERIMENT_DIR)
    else:
        print("\n[Stage 2] Skipping experiment design")

    # ----------------------------------------------------------
    # Stage 3: Run NetLogo experiments
    # ----------------------------------------------------------

    if not skip_running:
        print("\n[Stage 3] Running NetLogo BehaviorSpace experiments")
        simulation_results = run_all_submodel_experiments(
            EXPERIMENT_DIR, SUBMODELS
        )
    else:
        print("\n[Stage 3] Skipping NetLogo runs")
        simulation_results = {
            s: RESULTS_DIR / s / f"{s}_sensitivity_results.csv"
            for s in SUBMODELS
            if (RESULTS_DIR / s / f"{s}_sensitivity_results.csv").exists()
        }

    # ----------------------------------------------------------
    # Stage 4: Statistical sensitivity analysis
    # ----------------------------------------------------------

    if not skip_analysis:
        print("\n[Stage 4] Running statistical sensitivity analysis")

        sensitivity_results = {}
        loaded_dfs          = {}

        for submodel in tqdm(SUBMODELS, desc="Analyzing"):
            if submodel not in simulation_results:
                continue

            results_path = simulation_results[submodel]
            if not results_path or not results_path.exists():
                continue

            df = load_results(results_path)
            loaded_dfs[submodel] = df

            params = catalog.get(submodel, [])

            sensitivity_df = one_at_a_time_analysis(
                df, params, OUTPUT_METRICS
            )
            sensitivity_results[submodel] = sensitivity_df

            # Save sensitivity table
            out_path = RESULTS_DIR / f"{submodel}_sensitivity.csv"
            sensitivity_df.to_csv(out_path, index=False)

            # Generate tornado diagrams for each output metric
            for metric in OUTPUT_METRICS:
                if metric in df.columns:
                    plot_tornado_diagram(
                        sensitivity_df = sensitivity_df,
                        submodel_name  = submodel,
                        output_metric  = metric,
                        output_dir     = REPORT_DIR
                    )

        # Cross-submodel propagation analysis
        print("\nComputing cross-submodel propagation")
        propagation_df = compute_cross_submodel_propagation(
            loaded_dfs, catalog
        )
        propagation_df.to_csv(
            RESULTS_DIR / "cross_submodel_propagation.csv",
            index=False
        )

    else:
        print("\n[Stage 4] Loading existing sensitivity results")
        sensitivity_results = {}
        for submodel in SUBMODELS:
            path = RESULTS_DIR / f"{submodel}_sensitivity.csv"
            if path.exists():
                sensitivity_results[submodel] = pd.read_csv(path)

        prop_path = RESULTS_DIR / "cross_submodel_propagation.csv"
        propagation_df = pd.read_csv(prop_path) if prop_path.exists() \
                         else pd.DataFrame()

    # ----------------------------------------------------------
    # Stage 5: Generate reports
    # ----------------------------------------------------------

    if not skip_reports:
        print("\n[Stage 5] Generating sensitivity analysis reports")

        submodel_reports = {}

        for submodel in tqdm(SUBMODELS, desc="Reporting"):
            if submodel not in sensitivity_results:
                continue

            report = generate_submodel_report(
                submodel_name  = submodel,
                parameters     = catalog.get(submodel, []),
                sensitivity_df = sensitivity_results[submodel],
                propagation_df = propagation_df,
                report_dir     = REPORT_DIR
            )
            submodel_reports[submodel] = report

        print("\nGenerating full library report")
        generate_full_library_report(
            submodel_reports = submodel_reports,
            propagation_df   = propagation_df,
            report_dir       = REPORT_DIR
        )
    else:
        print("\n[Stage 5] Skipping report generation")

    # ----------------------------------------------------------
    # Done
    # ----------------------------------------------------------

    print("\n" + "=" * 60)
    print("Pipeline complete")
    print(f"  Parameter catalog : {SUBMODEL_DIR}/full_parameter_catalog.json")
    print(f"  Experiments       : {EXPERIMENT_DIR}")
    print(f"  Results           : {RESULTS_DIR}")
    print(f"  Reports           : {REPORT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline(
        skip_extraction  = False,
        skip_experiments = False,
        skip_running     = True,   # Set True after first run
        skip_analysis    = False,
        skip_reports     = False
    )