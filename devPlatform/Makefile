.PHONY: all runserver venv clean

# Define variables
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
REQUIREMENTS_FILE := requirements/requirements.txt

all: migrate runserver

migrate:
	@echo "\n| Applying Migrations..."
	$(PYTHON) manage.py migrate

# Target to run the Django development server
runserver: $(VENV_DIR)
	@echo "Starting Django development server..."
	$(PYTHON) manage.py runserver localhost:8000

# Target to create and set up the virtual environment
$(VENV_DIR):
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing/Upgrading pip in virtual environment..."
	$(PIP) install --upgrade pip
	@echo "Installing project requirements..."
	$(PIP) install -r $(REQUIREMENTS_FILE)

# Target to clean up the virtual environment and database
clean:
	@echo "Cleaning up virtual environment and database..."
	rm -rf $(VENV_DIR) db.sqlite3
