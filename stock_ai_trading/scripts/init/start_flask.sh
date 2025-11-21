#!/bin/bash
source /home/meiming/miniconda3/etc/profile.d/conda.sh
conda activate stock_trading
python run_flask.py --host 0.0.0.0 --port 5000
