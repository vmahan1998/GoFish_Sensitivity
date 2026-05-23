# ============================================================
#  netlogo_runner.py
#  Runs NetLogo headless BehaviorSpace experiments
# ============================================================

import subprocess
import shutil
from pathlib import Path
from config import NETLOGO_PATH, MODEL_PATH, NETLOGO_JAVA, RESULTS_DIR


def run_behaviorspace(
    experiment_xml: Path,
    experiment_name: str,
    output_dir: Path = RESULTS_DIR
) -> Path:
    """
    Run a BehaviorSpace experiment in NetLogo headless mode.
    Returns path to the output CSV.
    """

    output_file = output_dir / f"{experiment_name}_results.csv"

    cmd = [
        NETLOGO_JAVA,
        "-jar", str(NETLOGO_PATH),
        "--model", str(MODEL_PATH),
        "--experiment", experiment_name,
        "--table", str(output_file),
        "--threads", "4"
    ]

    print(f"  Running: {experiment_name}")
    print(f"  Output:  {output_file}")

    result = subprocess.run(
        cmd,
        capture_output = True,
        text           = True,
        timeout        = 3600  # 1 hour timeout per experiment
    )

    if result.returncode != 0:
        print(f"  Error running {experiment_name}:")
        print(f"  {result.stderr[:500]}")
        return None

    print(f"  Completed: {experiment_name}")
    return output_file


def run_all_submodel_experiments(
    experiment_dir: Path,
    submodels: list
) -> dict:
    """
    Run all BehaviorSpace experiments for all submodels.
    Returns dict mapping submodel name to results CSV path.
    """

    results = {}

    for submodel in submodels:
        xml_path = experiment_dir / f"{submodel}_experiments.xml"

        if not xml_path.exists():
            print(f"  Skipping {submodel}: no experiment file found")
            continue

        output_path = run_behaviorspace(
            experiment_xml  = xml_path,
            experiment_name = f"{submodel}_sensitivity",
            output_dir      = RESULTS_DIR / submodel
        )

        if output_path:
            results[submodel] = output_path

    return results