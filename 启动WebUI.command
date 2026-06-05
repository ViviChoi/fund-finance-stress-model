#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Mac double-click launcher for the Fund Finance Stress Model WebUI.
#
# Double-click this file in Finder to:
#   1. Auto-setup the Python environment if it's missing
#   2. Start the Streamlit web server
#   3. Auto-open your default browser to http://localhost:8501
#
# Keep the Terminal window open while you use the WebUI.
# Close it (or press Ctrl+C inside it) to stop the server.
# ---------------------------------------------------------------------------

set -e
cd "$(dirname "$0")"

clear
cat <<'BANNER'

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   Fund Finance Stress Model                                  ║
║   A Power-Electronics Sub-Sector Risk Lens                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

BANNER

# ---- Verify Python 3.10+ -----------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "✗  python3 not found."
    echo ""
    echo "   Please install Python 3.10+ first:"
    echo "      brew install python              (recommended)"
    echo "      — or download from python.org"
    echo ""
    echo "Press Enter to close this window..."
    read -r
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓  Python $PY_VER detected"

# ---- Bootstrap venv if missing -----------------------------------------
if [ ! -d ".venv" ] || [ ! -x ".venv/bin/python" ]; then
    echo ""
    echo "→  First-time setup (this takes ~60 seconds)..."
    echo "   Installing numpy, pandas, matplotlib, streamlit, plotly..."
    echo ""
    ./setup.sh
fi

# ---- Launch -------------------------------------------------------------
echo ""
echo "→  Starting WebUI..."
echo "→  Your browser will open in a few seconds."
echo ""
echo "   When you're done: come back to this window and press"
echo "   Ctrl+C, or simply close it. The server will stop."
echo ""

# Open browser after a short delay (gives streamlit time to bind port 8501)
( sleep 4 && open "http://localhost:8501/" ) &

# Run streamlit in foreground; Ctrl+C / window close kills it
.venv/bin/python -m streamlit run app.py \
    --server.headless true \
    --server.port 8501 \
    --browser.gatherUsageStats false

echo ""
echo "Server stopped. Press Enter to close this window..."
read -r
