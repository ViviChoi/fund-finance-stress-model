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
REQS_CORE="code/requirements.txt"
REQS_WEBUI="code/requirements-webui.txt"

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

if [ ! -f "$REQS_CORE" ]; then
    echo "✗  $REQS_CORE not found. Expected this script to be run from project root."
    exit 1
fi

echo "→  Upgrading pip"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

echo "→  Installing core dependencies from $REQS_CORE"
"$VENV_DIR/bin/pip" install --quiet -r "$REQS_CORE"

# ---- Verify core ----------------------------------------------------------

echo "→  Verifying core install"
"$VENV_DIR/bin/python" -c "
import numpy, pandas, matplotlib, pptx, pytest
print(f'  numpy        {numpy.__version__}')
print(f'  pandas       {pandas.__version__}')
print(f'  matplotlib   {matplotlib.__version__}')
print(f'  python-pptx  {pptx.__version__}')
print(f'  pytest       {pytest.__version__}')
"

# ---- WebUI dependencies (best-effort) --------------------------------------

if [ -f "$REQS_WEBUI" ]; then
    echo "→  Installing WebUI dependencies from $REQS_WEBUI"
    if "$VENV_DIR/bin/pip" install --quiet -r "$REQS_WEBUI" 2>/dev/null; then
        "$VENV_DIR/bin/python" -c "import streamlit, plotly; print(f'  streamlit    {streamlit.__version__}'); print(f'  plotly       {plotly.__version__}')"
        echo "✓  WebUI dependencies installed."
    else
        echo "⚠️  WebUI install failed. Core functionality still works."
        echo "    On Windows ARM64 this is expected (no prebuilt wheels for"
        echo "    pyarrow / httptools). Use the Mac path for the WebUI."
    fi
fi

cat <<EOF

✓  Setup complete.

Next steps:
    make figures   # regenerate sector_matrix.png and nav_ltv_heatmap.png
    make deck      # rebuild the pptx (also runs figures)
    make all       # everything
    make clean     # remove generated outputs (keeps venv)
EOF
