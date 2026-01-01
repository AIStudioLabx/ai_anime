#!/usr/bin/env bash
set -e

# =========================
# Python Project Bootstrap
# pyenv + venv + direnv
# =========================

# ---- configurable defaults ----
PYTHON_VERSION_DEFAULT="3.11.8"
VENV_DIR=".venv"

# ---- helpers ----
error() {
  echo "❌ $1" >&2
  exit 1
}

info() {
  echo "▶ $1"
}

# ---- parse args ----
PROJECT_DIR="${1:-$(pwd)}"
PYTHON_VERSION="${2:-$PYTHON_VERSION_DEFAULT}"

# ---- checks ----
command -v pyenv >/dev/null 2>&1 || error "pyenv not found. Please install pyenv first."
command -v direnv >/dev/null 2>&1 || error "direnv not found. Please install direnv first."

# ---- enter project ----
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

info "Initializing Python project in: $(pwd)"
info "Using Python version: $PYTHON_VERSION"

# ---- pyenv python ----
if ! pyenv versions --bare | grep -q "^$PYTHON_VERSION$"; then
  info "Python $PYTHON_VERSION not found in pyenv. Installing..."
  pyenv install "$PYTHON_VERSION"
else
  info "Python $PYTHON_VERSION already installed."
fi

info "Setting local Python version..."
pyenv local "$PYTHON_VERSION"

# ---- venv ----
if [ ! -d "$VENV_DIR" ]; then
  info "Creating venv: $VENV_DIR"
  python -m venv "$VENV_DIR"
else
  info "venv already exists: $VENV_DIR"
fi

# ---- direnv ----
if [ ! -f ".envrc" ]; then
  info "Creating .envrc for direnv"
  echo "source $VENV_DIR/bin/activate" > .envrc
else
  info ".envrc already exists"
fi

info "Authorizing direnv"
direnv allow

# ---- common files ----
if [ ! -f "requirements.txt" ]; then
  info "Creating empty requirements.txt"
  touch requirements.txt
fi

if [ ! -f "pyproject.toml" ]; then
  info "Creating minimal pyproject.toml"
  cat > pyproject.toml <<EOF
[project]
name = "$(basename "$(pwd)")"
version = "0.1.0"
description = ""
requires-python = ">=$PYTHON_VERSION"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF
fi

# ---- done ----
info "✅ Project initialized successfully!"
echo
echo "Next steps:"
echo "  cd $(pwd)"
echo "  pip install -r requirements.txt"
echo
echo "Environment behavior:"
echo "  cd into this directory  -> venv auto-activated"
echo "  cd out of this directory -> venv auto-deactivated"