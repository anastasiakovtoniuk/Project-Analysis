SHELL := /bin/bash

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
ARCHIVE_CSV := dataset/saveecobot-cities-pm25-and-aqi-pm25.csv
RAW_DIR := data/raw
PROCESSED_DIR := data/processed
FIGURES_DIR := outputs/figures
QA_DIR := outputs/qa
CITIES_METADATA := dataset/saveecobot_cities.csv
HOURLY_PATTERN := dataset/saveecobot_cities_pm25_and_aqi_pm25_*.csv
ADMIN_BOUNDARIES := dataset/geo/ukraine_adm_boundaries.geojson
TIMEZONE := Europe/Kyiv
WARTIME_START := 2022-02-24
PM25_GUIDELINE := 15

INGEST_OUT := $(RAW_DIR)/city_hourly_2025.parquet
AGGREGATE_OUT := $(PROCESSED_DIR)/city_daily_pm25.parquet
QA_OUT := $(QA_DIR)/qa_summary.json
FIGURES_OUT := $(FIGURES_DIR)/08_choropleth.png
VENV_MARKER := $(VENV)/.installed

.PHONY: default help ingest aggregate qa figures pipeline full clean

default: help

help:
	@echo "Available targets:"
	@echo "  setup     - Create virtualenv and install dependencies"
	@echo "  ingest    - Ingest hourly CSVs into parquet"
	@echo "  aggregate - Aggregate hourly data to derived tables"
	@echo "  qa        - Generate QA summaries"
	@echo "  figures   - Render publication-ready figures"
	@echo "  pipeline  - Run ingest, aggregate, and QA"
	@echo "  full      - Run pipeline and figures"
	@echo "  clean     - Remove processed artefacts and outputs"

setup: $(VENV_MARKER)

$(VENV_MARKER): requirements.txt
	@test -d $(VENV) || python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $(VENV_MARKER)

$(INGEST_OUT): $(VENV_MARKER)
	@mkdir -p $(RAW_DIR)
	$(PYTHON) -m src.pipeline.run ingest --hourly-pattern "$(HOURLY_PATTERN)" --cities-metadata $(CITIES_METADATA) --raw-dir $(RAW_DIR) --archive-csv $(ARCHIVE_CSV)

ingest: $(INGEST_OUT)

$(AGGREGATE_OUT): $(INGEST_OUT) $(VENV_MARKER)
	@mkdir -p $(PROCESSED_DIR)
	$(PYTHON) -m src.pipeline.run aggregate --raw-dir $(RAW_DIR) --processed-dir $(PROCESSED_DIR) --cities-metadata $(CITIES_METADATA) --admin-boundaries $(ADMIN_BOUNDARIES) --timezone $(TIMEZONE) --wartime-start $(WARTIME_START) --pm25-guideline $(PM25_GUIDELINE)

aggregate: $(AGGREGATE_OUT)

$(QA_OUT): $(AGGREGATE_OUT) $(VENV_MARKER)
	@mkdir -p $(QA_DIR)
	$(PYTHON) -m src.pipeline.run qa --processed-dir $(PROCESSED_DIR) --qa-dir $(QA_DIR) --pm25-guideline $(PM25_GUIDELINE)

qa: $(QA_OUT)

$(FIGURES_OUT): $(AGGREGATE_OUT) $(VENV_MARKER)
	@mkdir -p $(FIGURES_DIR)
	$(PYTHON) -m src.visualization.run all --processed-dir $(PROCESSED_DIR) --figures-dir $(FIGURES_DIR)

figures: $(FIGURES_OUT)

pipeline: qa

full: pipeline figures

clean:
	rm -rf $(RAW_DIR) $(PROCESSED_DIR) $(FIGURES_DIR) $(QA_DIR)
	mkdir -p $(RAW_DIR) $(PROCESSED_DIR) $(FIGURES_DIR) $(QA_DIR)
