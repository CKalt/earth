#!/bin/sh
python3 -m venv env
source env/bin/activate

# Upgrade pip, setuptools, and wheel:
pip install --upgrade pip setuptools wheel

# Now install Dash, Plotly, and numpy with pinned versions:
pip install dash==2.9.3 dash-core-components==2.0.0 dash-html-components==2.0.0 \
            plotly==5.14.1 numpy

