#!/bin/bash
cd "$(dirname "$0")"

# Try WarMap venv first, then system, then create local venv
if [ -f "../WarMap/.venv/bin/activate" ]; then
    source ../WarMap/.venv/bin/activate
    pip install -q plotly 2>/dev/null
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q streamlit pandas numpy plotly
fi

streamlit run app.py --server.port 8502 --server.headless false
