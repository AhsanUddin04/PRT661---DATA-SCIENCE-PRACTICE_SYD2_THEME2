.PHONY: setup data features backtest forecast app test db all
setup:      ; pip install -r requirements.txt
data:       ; python -m prt661.pipeline --stages parse clean
features:   ; python -m prt661.pipeline --stages features
backtest:   ; python scripts/run_backtest.py && python scripts/run_statistical_backtest.py sarima && python scripts/run_statistical_backtest.py prophet
forecast:   ; python -m prt661.pipeline --stages forecast app_data
db:         ; python -m prt661.pipeline --stages load_db
report:     ; python scripts/make_report_assets.py && python scripts/run_noise_floor.py && python scripts/run_explain.py
app:        ; streamlit run app/app.py
test:       ; pytest -q
all: data features backtest forecast report test
