# UniCredit Fund Financing — First Look
# Regenerate figures, deck, and demo artefacts from source.
#
# Usage:
#     make all       # everything (figures + deck + demo)
#     make figures   # core PNGs only
#     make deck      # pptx (depends on figures)
#     make demo      # demo run: five-fund comparison + talking points
#     make clean     # remove generated outputs (keeps venv)
#     make distclean # also remove the venv

PYTHON := .venv/bin/python

FIGURES    := figures/sector_matrix.png figures/nav_ltv_heatmap.png
DEMO_FIG   := figures/fund_comparison.png
DECK       := slides/UniCredit-FirstLook-Deck.pptx

.PHONY: all figures deck demo test serve clean distclean check

all: deck demo

serve: | check
	@$(PYTHON) -m streamlit run app.py \
		--server.headless true --browser.gatherUsageStats false

figures: $(FIGURES)

deck: $(DECK)

demo: $(DEMO_FIG)

test: | check
	@$(PYTHON) -m pytest tests/ -v --tb=short

figures/sector_matrix.png: code/sector_matrix.py | check
	@cd code && ../$(PYTHON) sector_matrix.py

figures/nav_ltv_heatmap.png: code/nav_stress_model.py | check
	@cd code && ../$(PYTHON) nav_stress_model.py

$(DEMO_FIG): code/demo_runner.py code/nav_stress_model.py data/example_funds.json | check
	@cd code && ../$(PYTHON) demo_runner.py

$(DECK): code/build_deck.py $(FIGURES) | check
	@cd code && ../$(PYTHON) build_deck.py

check:
	@test -x $(PYTHON) || { \
		echo "✗  venv not found. Run ./setup.sh first."; exit 1; \
	}

clean:
	rm -f $(FIGURES) $(DEMO_FIG) $(DECK)
	@echo "✓  removed generated figures and deck"

distclean: clean
	rm -rf .venv
	@echo "✓  removed venv"
