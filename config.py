# ============================================================
#  config.py
#  GoFish Sensitivity Analysis Pipeline
#  Repo root: E:\AutoFish\GoFish_Sensitivity\
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ------------------------------------------------------------
# Repo-local paths
# ------------------------------------------------------------

REPO_ROOT      = Path(__file__).parent
DATA_DIR       = REPO_ROOT / "data"
SUBMODEL_DIR   = DATA_DIR / "submodels"   # Rmd AND nls files live here
EXPERIMENT_DIR = DATA_DIR / "experiments"
RESULTS_DIR    = DATA_DIR / "results"
REPORT_DIR     = DATA_DIR / "reports"

for _d in [SUBMODEL_DIR, EXPERIMENT_DIR, RESULTS_DIR, REPORT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# External paths — only NetLogo and the .nlogo file
# ------------------------------------------------------------

MODEL_PATH = Path(os.getenv(
    "MODEL_PATH",
    r"E:\Penobscot_Mercury_Exposure\Penobscot_Mercury_Exposure.nlogo"
))

NETLOGO_PATH = Path(os.getenv(
    "NETLOGO_PATH",
    r"C:\Program Files\NetLogo 6.4.0\app\netlogo-6.4.0.jar"
))
NETLOGO_JAVA = os.getenv("JAVA_PATH", "java")

# ------------------------------------------------------------
# LLM — Groq primary
# ------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
GROQ_MODEL_FAST    = "llama-3.1-8b-instant"
GROQ_MODEL_QUALITY = "llama-3.3-70b-versatile"
GROQ_BASE_URL      = "https://api.groq.com/openai/v1"

XAI_API_KEY     = os.getenv("XAI_API_KEY")
XAI_MODEL       = "grok-beta"
XAI_BASE_URL    = "https://api.x.ai/v1"

GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL    = "gemini-1.5-flash"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.1"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"

MAX_TOKENS = 8000

# ------------------------------------------------------------
# Sensitivity settings
# ------------------------------------------------------------

N_SAMPLES     = 100
N_REPLICATES  = 5
TICKS_PER_RUN = 2016
RANDOM_SEEDS  = [42, 123, 456, 789, 1011]

OUTPUT_METRICS = [
    "metabolism-rate",
    "energy",
    "mehg-total",
    "hg-total",
    "ionregulatory-stress",
    "chloride-cell-density",
    "swim-efficiency",
    "lipid-catabolism-efficiency",
]

# ------------------------------------------------------------
# Submodel registry — both Rmd and nls live in SUBMODEL_DIR
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
    "predation",
]

SUBMODEL_FILES = {
    "metabolism"          : {"rmd": "04-Metabolism.Rmd",
                             "nls": "Calculate-metabolism.nls"},
    "digestion"           : {"rmd": "05-Digestion.Rmd",
                             "nls": "digestion.nls"},
    "salinity_exposure"   : {"rmd": "06-Salinity_Exposure.Rmd",
                             "nls": "Osmoregulation.nls"},
    "migration_cue"       : {"rmd": "07-Migration_Cue.Rmd",
                             "nls": "Migration-cue.nls"},
    "contaminant_exposure": {"rmd": "08-Contaminant_Exposure.Rmd",
                             "nls": "Mercury-Contamination.nls"},
    "filter_feeding"      : {"rmd": "09-Filter_Feeding.Rmd",
                             "nls": "Foraging_postworkshop_update.nls"},
    "lipid_catabolism"    : {"rmd": "10-Lipid_Catabolism.Rmd",
                             "nls": "Foraging_postworkshop_update.nls"},
    "landward_migration"  : {"rmd": "11-Landward_Migration.Rmd",
                             "nls": "Landward-Migration.nls"},
    "seaward_migration"   : {"rmd": "12-Seaward_Migration.Rmd",
                             "nls": "Seaward-Migration.nls"},
    "schooling"           : {"rmd": "13-Schooling.Rmd",
                             "nls": "Schooling.nls"},
    "stst"                : {"rmd": "14-Selective_Tidal_Stream_Transport.Rmd",
                             "nls": "Selective-Tidal-Stream-Transport.nls"},
    "predation"           : {"rmd": "15-Predation.Rmd",
                             "nls": "Chase-nearest-alewife.nls"},
}

# ------------------------------------------------------------
# Prototype NetLogo setup — no GIS, no CSV inputs
# ------------------------------------------------------------

PROTOTYPE_SETUP = """
to setup-sensitivity
  resize-world 0 200 0 350
  set-patch-size 3
  set Hg-threshold 150
  set MeHg-threshold 15
  set day 120
  set hour 0
  set monthnum 4
  set month "April"
  set month-list ["January" "February" "March" "April" "May"
                  "June" "July" "August" "September" "October"
                  "November" "December"]
  set max-seaward-velocity  1.5
  set max-landward-velocity -1.5
  set max-Hg   700
  set min-Hg   0
  set max-MeHg 65
  set min-MeHg 0
  ask patches [
    ifelse (pxcor = min-pxcor or pxcor = max-pxcor or
            pycor = min-pycor or pycor = max-pycor) [
      set patch-terrain "land"
      set pcolor brown
      set cost-to-home 1e12
      set cost-to-sea  1e12
    ] [
      set patch-terrain "water"
      set pcolor blue
      set velocity     (random-float 3.0) - 1.5
      set depth         random-float 5.0
      set salinity      random-float 35.0
      set temperature   15 + random-float 10.0
      set SPM           random-float 0.0004
      set mercury       random-float 700.0
      set methylmercury random-float 65.0
      set cost-to-home 1e6
      set cost-to-sea  1e6
      set visits-by-alewife   0
      set ticks-spent-alewife 0
    ]
  ]
  reset-ticks
end
"""