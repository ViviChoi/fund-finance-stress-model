#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Bootstrap script — create a local venv and install dependencies.
# Idempotent: safe to re-run; will reuse the existing venv if present.
#
# Usage (from project root):
#     ./setup.sh
#
# After this, regenerate all artefacts with:
#     make all
# ---------------------------------------------------------------------------

set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR=".venv"
REQS="code/requirements.txt"

# ---- Sanity checks --------------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
    echo "✗  python3 not found. Install Python 3.10+ first."
    echo "   macOS:  brew install python  (or download from python.org)"
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION##*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "✗  Python 3.10+ required (found $PY_VERSION)."
    exit 1
fi

echo "✓  Using Python $PY_VERSION"

# ---- Create / reuse venv --------------------------------------------------

if [ -d "$VENV_DIR" ]; then
    echo "✓  venv already exists at $VENV_DIR — reusing"
else
    echo "→  Creating venv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# ---- Install dependencies -------------------------------------------------

if [ ! -f "$REQS" ]; then
    echo "✗  $REQS not found. Expected this script to be run from project root."
    exit 1
fi

echo "→  Installing dependencies from $REQS"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$REQS"

# ---- Verify ---------------------------------------------------------------

echo "→  Verifying install"
"$VENV_DIR/bin/python" -c "
import numpy, pandas, matplotlib, pptx
print(f'  numpy        {numpy.__version__}')
print(f'  pandas       {pandas.__version__}')
print(f'  matplotlib   {matplotlib.__version__}')
print(f'  python-pptx  {pptx.__version__}')
"

cat <<EOF

✓  Setup complete.

Next steps:
    make figures   # regenerate sector_matrix.png and nav_ltv_heatmap.png
    make deck      # rebuild the pptx (also runs figures)
    make all       # everything
    make clean     # remove generated outputs (keeps venv)
EOF
