# ============================================================
#  check_paths.py
#  Run before main.py: python check_paths.py
# ============================================================

from config import (
    REPO_ROOT, SUBMODEL_DIR, EXPERIMENT_DIR, RESULTS_DIR, REPORT_DIR,
    MODEL_PATH, NETLOGO_PATH,
    GROQ_API_KEY, LLM_PROVIDER,
    SUBMODEL_FILES,
)

SEP = "-" * 60

def check(label, path):
    ok = path.exists()
    print(f"  {'✓' if ok else '✗'}  {label:<28} {'OK' if ok else 'MISSING'}")
    print(f"       {path}")
    return ok

all_ok = True

print(f"\n{SEP}")
print("  REPO-LOCAL PATHS")
print(SEP)
for label, path in [
    ("Repo root",        REPO_ROOT),
    ("data/submodels",   SUBMODEL_DIR),
    ("data/experiments", EXPERIMENT_DIR),
    ("data/results",     RESULTS_DIR),
    ("data/reports",     REPORT_DIR),
]:
    all_ok &= check(label, path)

print(f"\n{SEP}")
print("  EXTERNAL PATHS  (.env)")
print(SEP)
for label, path in [
    ("NetLogo jar",  NETLOGO_PATH),
    ("Model .nlogo", MODEL_PATH),
]:
    all_ok &= check(label, path)

print(f"\n{SEP}")
print("  LLM")
print(SEP)
print(f"  Provider  : {LLM_PROVIDER}")
key_ok = bool(GROQ_API_KEY)
print(f"  {'✓' if key_ok else '✗'}  GROQ_API_KEY : {'SET' if key_ok else 'MISSING — add to .env'}")
all_ok &= key_ok

print(f"\n{SEP}")
print("  SUBMODEL FILES  (data/submodels/)")
print(SEP)
for name, files in SUBMODEL_FILES.items():
    rmd = SUBMODEL_DIR / files["rmd"]
    nls = SUBMODEL_DIR / files["nls"]
    rmd_ok = rmd.exists()
    nls_ok = nls.exists()
    flag = "✓" if (rmd_ok and nls_ok) else "✗"
    print(f"  {flag}  {name:<22}  "
          f"rmd={'OK' if rmd_ok else 'MISSING'}  "
          f"nls={'OK' if nls_ok else 'MISSING'}")
    all_ok &= rmd_ok and nls_ok

print(f"\n{SEP}")
if all_ok:
    print("  ✓  All checks passed — ready to run main.py")
else:
    print("  ✗  Fix the issues above before running main.py")
print(SEP + "\n")