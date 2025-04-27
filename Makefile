PYTHON = python3
NUITKA = $(PYTHON) -m nuitka
COMPILER_SCRIPT = compiler.py
OUTPUT_DIR = build
EXECUTABLE_NAME = wakec
EXECUTABLE_PATH = $(OUTPUT_DIR)/$(EXECUTABLE_NAME)

# Default target
all: build

# Compile the script into a single executable using Nuitka
build:
	@echo "Compiling $(COMPILER_SCRIPT) with Nuitka..."
	$(NUITKA) --onefile --output-dir=$(OUTPUT_DIR) --output-filename=$(EXECUTABLE_NAME) $(COMPILER_SCRIPT)
	@echo "Build complete: $(EXECUTABLE_PATH)"

# Remove build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(OUTPUT_DIR) $(EXECUTABLE_NAME).build $(EXECUTABLE_NAME).onefile-build *.pyc __pycache__
	@echo "Clean complete."

# Phony targets
.PHONY: all build clean

