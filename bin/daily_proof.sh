#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
BASE="/opt/lumen-core"
PYV="$BASE/.venv"
RPT="$BASE/reports"
LOG="$BASE/logs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# activate venv
source "$PYV/bin/activate"

# ensure deps (idempotent; fast if already installed)
python - <<'PY'
import sys, subprocess
pkgs = ["numpy","matplotlib","pandas"]
subprocess.run([sys.executable,"-m","pip","install","-q","--upgrade","pip"],check=False)
subprocess.run([sys.executable,"-m","pip","install","-q",*pkgs],check=False)
PY

mkdir -p "$RPT" "$LOG"

# run stability sim (uses your evo_kpi.py if present, else fallback)
if [ -f "$BASE/evo_kpi.py" ]; then
  python "$BASE/evo_kpi.py" || true
elif [ -f "$BASE/bin/sim_stability.py" ]; then
  python "$BASE/bin/sim_stability.py" "$RPT" || true
fi

# evo sweep (fallback)
[ -f "$BASE/bin/sim_evo.py" ] && python "$BASE/bin/sim_evo.py" "$RPT" || true

# ROI stress (uses your roi_report.py if present)
if [ -f "$BASE/roi_report.py" ]; then
  python "$BASE/roi_report.py" --sites 20 --out "$RPT" || true
elif [ -f "$BASE/bin/sim_roi.py" ]; then
  python "$BASE/bin/sim_roi.py" "$RPT" 20 || true
fi

# compose proof PDF
PDF_PATH="$(python "$BASE/bin/make_proof_pdf.py" | tail -n1)"
[ -f "$PDF_PATH" ] || { echo "[ERR] report compose failed" >&2; exit 1; }

# handy symlink to "latest"
ln -sfn "$PDF_PATH" "$RPT/latest_proof.pdf"

echo "[OK] $(date -u) → $PDF_PATH"
