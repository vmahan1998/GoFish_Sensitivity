# ============================================================
#  config.py
#  Central configuration for GoFish sensitivity pipeline
# ============================================================

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT_DIR        = Path(__file__).parent
DATA_DIR        = ROOT_DIR / "data"
SUBMODEL_DIR    = DATA_DIR / "submodels"
EXPERIMENT_DIR  = DATA_DIR / "experiments"
RESULTS_DIR     = DATA_DIR / "results"
REPORT_DIR      = DATA_DIR / "reports"
TEMPLATE_DIR    = ROOT_DIR / "templates"

# Create directories if they do not exist
for d in [SUBMODEL_DIR, EXPERIMENT_DIR, RESULTS_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# NetLogo
# ------------------------------------------------------------

NETLOGO_PATH    = os.getenv(
    "NETLOGO_PATH",
    "C:/Program Files/NetLogo 6.3.0/app/netlogo-6.3.0.jar"
)
MODEL_PATH      = os.getenv(
    "MODEL_PATH",
    "C:/Users/RDEL1VMM/Desktop/current projects/MigratoryFish_ABM_Library/P-MEM.nlogo"
)
NETLOGO_JAVA    = os.getenv("JAVA_PATH", "java")

# ------------------------------------------------------------
# Anthropic API
# ------------------------------------------------------------

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"
MAX_TOKENS        = 8000

# ------------------------------------------------------------
# Sensitivity analysis settings
# ------------------------------------------------------------

N_SAMPLES         = 100    # Sobol sample size per parameter
N_REPLICATES      = 5      # Replicates per parameter combination
TICKS_PER_RUN     = 2016   # One week at 5-minute timesteps
RANDOM_SEEDS      = [42, 123, 456, 789, 1011]

# ------------------------------------------------------------
# Submodels to analyze
# ------------------------------------------------------------

SUBMODELS = [
    "metabolism",
    "digestion",
    "salinity_exposure",
    "migration_cue",
    "contaminant_exposure",
    "filter_feeding",
    "lipid_catabolism",
    "landward_migration",
    "seaward_migration",
    "schooling",
    "stst",
    "predation"
]