.PHONY: clean diff-cover docs help quality requirements test upgrade


.DEFAULT_GOAL := help

DASHBOARD_CONFIG_PATH ?= repo_health_dashboard/console_dashboard_config.yaml
REPO_HEALTH_DATA_PATH ?= ../repo-health-data
SQLITE_FILE_PATH = $(REPO_HEALTH_DATA_PATH)/dashboards/dashboard.sqlite3

# For opening files in a browser. Use like: $(BROWSER)relative/path/to/file.html
BROWSER := python -m webbrowser file://$(CURDIR)/

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@awk -F ':.*?## ' '/^[a-zA-Z]/ && NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

generate_sqlite: ## generate the repo health SQLite data file from a local checkout of the repo-health-data repository
	rm -f $(REPO_HEALTH_DATA_PATH)/dashboards/dashboard.sqlite3
	repo_health_dashboard --data-dir $(REPO_HEALTH_DATA_PATH)/individual_repo_data --configuration "repo_health_dashboard/configuration.yaml" --data-life-time=30 --output-sqlite "${REPO_HEALTH_DATA_PATH}/dashboards/dashboard"

streamlit: ## launch the repo health dashboard as a Streamlit app in a web browser window
	streamlit run scripts/streamlit_dashboard.py $(SQLITE_FILE_PATH) $(DASHBOARD_CONFIG_PATH)

console: ## display the console health dashboard, filter to specific squad(s) like 'make squad="arbi-bom fed-bom" console'
ifdef squad
	@python scripts/console_dashboard.py $(SQLITE_FILE_PATH) --configuration=$(DASHBOARD_CONFIG_PATH) --squad='$(squad)'
else
	@python scripts/console_dashboard.py $(SQLITE_FILE_PATH) --configuration=$(DASHBOARD_CONFIG_PATH)
endif

clean: ## remove generated byte code, coverage reports, and build artifacts
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

docs: ## generate Sphinx HTML documentation, including API docs
	tox -v -e docs
	$(BROWSER)docs/_build/html/index.html

# Define PIP_COMPILE_OPTS=-v to get more information during make upgrade.
PIP_COMPILE = pip-compile --upgrade $(PIP_COMPILE_OPTS)

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	$(PIP_COMPILE) --allow-unsafe --rebuild -o requirements/pip.txt requirements/pip.in
	$(PIP_COMPILE) -o requirements/pip-tools.txt requirements/pip-tools.in
	$(PIP_COMPILE) -o requirements/base.txt requirements/base.in
	$(PIP_COMPILE) -o requirements/test.txt requirements/test.in
	$(PIP_COMPILE) -o requirements/doc.txt requirements/doc.in
	$(PIP_COMPILE) -o requirements/quality.txt requirements/quality.in
	$(PIP_COMPILE) -o requirements/ci.txt requirements/ci.in
	$(PIP_COMPILE) -o requirements/dev.txt requirements/dev.in
	# Let tox control the Django version for tests
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

quality: ## check coding style with pycodestyle and pylint
	tox -e quality

requirements: ## install development environment requirements
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	pip-sync requirements/dev.txt requirements/private.*
	pip install -e .

test: clean ## run tests in the current virtualenv
	tox

diff_cover: test ## find diff lines that need test coverage
	diff-cover coverage.xml
