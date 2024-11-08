# Makefile for AskAI project

VENV_PATH=venv
PYTHON=$(VENV_PATH)/bin/python
SRC_DIR=src/main/askai/
BUILD_DIR=build/
DIST_DIR=dist/
APP=$(SRC_DIR)/__main__.py
EXECUTABLE_NAME=askai
PREFIX?=/opt/homebrew/bin
INSTALL_PATH="$(PREFIX)/$(EXECUTABLE_NAME)"

.PHONY: create_venv requirements install_packages activate clean dist run require_sudo install

# Create virtual environment
create_venv:
	@if ! [ -x "$$(command -v python3)" ]; then \
		echo "Python 3 is not installed. Please install it."; \
		exit 1; \
	else \
	  echo "Using $$(python3 -V)."; \
	fi
	@if [ ! -d $(VENV_PATH) ]; then \
		python3 -m venv $(VENV_PATH); \
		echo "Virtual environment created in $(VENV_PATH)."; \
	else \
		echo "Virtual environment already exists."; \
	fi

# Target to generate the requirements file
requirements: create_venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip freeze > requirements.txt

# Target to install packages into venv
install_packages: activate requirements
	echo "Installing $(EXECUTABLE_NAME) into $(INSTALL_PATH)"
	$(PYTHON) -m pip install -r requirements.txt

# Target to activate the virtual environment
activate:
	. $(VENV_PATH)/bin/activate

# Cleanup build
clean:
	@if [ -d $(BUILD_DIR) ]; then \rm -rf $(BUILD_DIR); fi
	@if [ -d $(DIST_DIR) ]; then \rm -rf $(DIST_DIR); fi

# Create a distribution
dist: clean install_packages
	pyinstaller --onefile --name enrager --paths "$(SRC_DIR)" "$(APP)"

# Target to run the app
run:
	PYTHONPATH="$(SRC_DIR)" $(PYTHON) "$(APP)" $(ARGS)

# Target to require sudo before executing other targets
require_sudo:
	@if [ "$$(id -u)" -ne 0 ]; then \
	echo "This target must be run as root. Please use sudo."; \
	exit 1; \
	fi

# Target to install the executable, depends on the 'dist' target
install: dist
	@if [ -f $(DIST_DIR)/$(EXECUTABLE_NAME) ]; then \
		\cp $(DIST_DIR)/$(EXECUTABLE_NAME) $(INSTALL_PATH); \
		echo "Installed $(EXECUTABLE_NAME) to $(INSTALL_PATH)"; \
	else \
		echo "Executable not found in $(DIST_DIR). Ensure 'dist' target builds the executable correctly."; \
		exit 1; \
	fi

# Target to uninstall the executable
uninstall:
	@if [ -f $(INSTALL_PATH) ]; then \
		\rm -f $(INSTALL_PATH); \
		echo "Uninstalled $(EXECUTABLE_NAME) from $(INSTALL_PATH)"; \
	else \
		echo "$(EXECUTABLE_NAME) is not installed."; \
	fi
