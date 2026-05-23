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
# LLM Provider Configuration
# ------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Groq
GROQ_API_KEY  = os.getenv("GROQ_API_KEY")
GROQ_MODEL_FAST   = "llama-3.1-8b-instant"      # extraction tasks
GROQ_MODEL_QUALITY = "llama-3.3-70b-versatile"   # report generation
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# xAI Grok
XAI_API_KEY   = os.getenv("XAI_API_KEY")
XAI_MODEL     = "grok-beta"
XAI_BASE_URL  = "https://api.x.ai/v1"

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL   = "gemini-1.5-flash"

# Ollama local
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.1"

# Anthropic Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"

MAX_TOKENS = 8000

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