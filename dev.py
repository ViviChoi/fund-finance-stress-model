#!/usr/bin/env python3
"""
Cross-platform task runner — works identically on macOS, Linux, and Windows.

Usage (any OS):
    python dev.py setup        # one-time: create .venv and install deps
    python dev.py all          # rebuild figures + demo + deck
    python dev.py figures      # core PNGs only
    python dev.py demo         # 5-fund comparison
    python dev.py deck         # pptx (depends on figures)
    python dev.py serve        # launch WebUI on localhost:8501
    python dev.py test         # run pytest test suite
    python dev.py clean        # remove generated outputs
    python dev.py distclean    # also remove the .venv

This is the universal fallback for the Makefile / setup.sh combo. On
Mac/Linux either path works; on Windows, prefer this one.

Requires only the system Python 3.10+; no other dependencies before
'setup' runs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQS = ROOT / "code" / "requirements.txt"
TESTS_DIR = ROOT / "tests"

IS_WIN = sys.platform == "win32"
VENV_BIN = VENV_DIR / ("Scripts" if IS_WIN else "bin")
VENV_PY = VENV_BIN / ("python.exe" if IS_WIN else "python")

GENERATED_FIGURES = [
    ROOT / "figures" / "sector_matrix.png",
    ROOT / "figures" / "nav_ltv_heatmap.png",
    ROOT / "figures" / "fund_comparison.png",
]
GENERATED_DECK = ROOT / "slides" / "UniCredit-FirstLook-Deck.pptx"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"→  {msg}", flush=True)


def ok(msg: str) -> None:
    print(f"✓  {msg}", flush=True)


def fail(msg: str, exit_code: int = 1) -> None:
    print(f"✗  {msg}", flush=True, file=sys.stderr)
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Sanity
# ---------------------------------------------------------------------------

def require_python_310() -> None:
    if sys.version_info < (3, 10):
        fail(f"Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor}).")


def require_venv() -> None:
    if not VENV_PY.exists():
        fail("venv not found. Run:  python dev.py setup")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_setup() -> None:
    """Create venv (if missing) and install/refresh dependencies."""
    require_python_310()
    if VENV_DIR.exists():
        ok(f"venv exists at {VENV_DIR.relative_to(ROOT)} — reusing")
    else:
        log(f"Creating venv at {VENV_DIR.relative_to(ROOT)}")
        venv.create(VENV_DIR, with_pip=True, clear=False)

    if not REQS.exists():
        fail(f"Requirements file not found: {REQS}")

    log("Upgrading pip")
    subprocess.run([str(VENV_PY), "-m", "pip", "install", "--quiet",
                    "--upgrade", "pip"], check=True)

    log(f"Installing dependencies from {REQS.relative_to(ROOT)}")
    subprocess.run([str(VENV_PY), "-m", "pip", "install", "--quiet",
                    "-r", str(REQS)], check=True)

    log("Verifying install")
    verify_code = (
        "import numpy, pandas, matplotlib, pptx, pytest;"
        "print(f'  numpy        {numpy.__version__}');"
        "print(f'  pandas       {pandas.__version__}');"
        "print(f'  matplotlib   {matplotlib.__version__}');"
        "print(f'  python-pptx  {pptx.__version__}');"
        "print(f'  pytest       {pytest.__version__}');"
    )
    subprocess.run([str(VENV_PY), "-c", verify_code], check=True)

    ok("Setup complete.")
    print()
    print("Next steps:")
    print("    python dev.py all       # rebuild everything")
    print("    python dev.py test      # run the test suite")
    print("    python dev.py demo      # 5-fund demo run")


def _run_script_in_code(script_name: str) -> None:
    """Run a script in code/ with cwd = code/ so its relative paths resolve."""
    require_venv()
    code_dir = ROOT / "code"
    script = code_dir / script_name
    if not script.exists():
        fail(f"Script not found: {script}")
    subprocess.run([str(VENV_PY), str(script)], cwd=str(code_dir), check=True)


def cmd_figures() -> None:
    _run_script_in_code("sector_matrix.py")
    _run_script_in_code("nav_stress_model.py")


def cmd_demo() -> None:
    _run_script_in_code("demo_runner.py")


def cmd_deck() -> None:
    """Build the pptx. Requires figures."""
    # Make sure figures exist; if they don't, build them first.
    missing = [p for p in GENERATED_FIGURES[:2] if not p.exists()]  # core 2
    if missing:
        log("Figures missing — building them first")
        cmd_figures()
    _run_script_in_code("build_deck.py")


def cmd_all() -> None:
    cmd_figures()
    cmd_demo()
    cmd_deck()
    ok("All artefacts rebuilt.")


def cmd_test() -> None:
    require_venv()
    log("Running pytest")
    subprocess.run(
        [str(VENV_PY), "-m", "pytest", str(TESTS_DIR), "-v", "--tb=short"],
        check=True,
    )


def cmd_serve() -> None:
    """Launch the Streamlit WebUI on localhost:8501."""
    require_venv()
    app_path = ROOT / "app.py"
    if not app_path.exists():
        fail(f"WebUI entry point not found: {app_path}")
    log(f"Launching WebUI — open http://localhost:8501 in any browser")
    log("Press Ctrl+C to stop.")
    subprocess.run([str(VENV_PY), "-m", "streamlit", "run", str(app_path),
                    "--server.headless", "true",
                    "--browser.gatherUsageStats", "false"], check=False)


def cmd_clean() -> None:
    removed = []
    for p in GENERATED_FIGURES + [GENERATED_DECK]:
        if p.exists():
            p.unlink()
            removed.append(p.relative_to(ROOT))
    # Pycache cleanup
    for pyc_dir in ROOT.rglob("__pycache__"):
        if VENV_DIR in pyc_dir.parents:
            continue
        shutil.rmtree(pyc_dir)
        removed.append(pyc_dir.relative_to(ROOT))
    if removed:
        ok(f"Removed {len(removed)} item(s):")
        for r in removed:
            print(f"     {r}")
    else:
        ok("Nothing to clean.")


def cmd_distclean() -> None:
    cmd_clean()
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR)
        ok("Removed .venv")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

COMMANDS = {
    "setup":     cmd_setup,
    "figures":   cmd_figures,
    "demo":      cmd_demo,
    "deck":      cmd_deck,
    "all":       cmd_all,
    "test":      cmd_test,
    "serve":     cmd_serve,
    "clean":     cmd_clean,
    "distclean": cmd_distclean,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] in {"-h", "--help"}:
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        fail(f"Unknown command: {cmd!r}\n\n"
             f"Valid commands: {', '.join(COMMANDS)}")
    COMMANDS[cmd]()


if __name__ == "__main__":
    main()
