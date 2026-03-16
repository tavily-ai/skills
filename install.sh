#!/bin/sh
set -e

PACKAGE_NAME="tavily-cli"
COMMAND_NAME="tvly"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# Colors (only when outputting to a terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' BOLD='' RESET=''
fi

info()  { printf "${BLUE}${BOLD}==>${RESET} %s\n" "$1"; }
warn()  { printf "${YELLOW}${BOLD}warning:${RESET} %s\n" "$1"; }
error() { printf "${RED}${BOLD}error:${RESET} %s\n" "$1" >&2; exit 1; }

# Find a Python >= 3.10 interpreter
find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -gt "$MIN_PYTHON_MAJOR" ] || \
               { [ "$major" -eq "$MIN_PYTHON_MAJOR" ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; }; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

main() {
    printf "\n${BOLD}Tavily CLI Installer${RESET}\n\n"

    # Install via uv (fastest) — no system Python required
    if command -v uv >/dev/null 2>&1; then
        info "Installing ${PACKAGE_NAME} with uv..."
        uv tool install "$PACKAGE_NAME" || uv tool upgrade "$PACKAGE_NAME"
    else
        # Find Python (needed for pipx / pip)
        PYTHON=$(find_python) || error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required but not found.
  Install it from https://www.python.org/downloads/ or install uv (https://docs.astral.sh/uv/) and try again."

        py_version=$("$PYTHON" --version 2>&1)
        info "Found $py_version"

        if command -v pipx >/dev/null 2>&1; then
            info "Installing ${PACKAGE_NAME} with pipx..."
            pipx install "$PACKAGE_NAME" || pipx upgrade "$PACKAGE_NAME"
        else
            info "Installing ${PACKAGE_NAME} with pip..."
            # Use --user only when outside a virtual environment
            in_venv=$("$PYTHON" -c "import sys; print(int(sys.prefix != sys.base_prefix or hasattr(sys, 'real_prefix')))" 2>/dev/null) || in_venv=0
            if [ "$in_venv" = "1" ]; then
                "$PYTHON" -m pip install "$PACKAGE_NAME"
            else
                "$PYTHON" -m pip install --user "$PACKAGE_NAME"

                # Warn if ~/.local/bin is not in PATH (common pip --user location)
                user_bin=$("$PYTHON" -c "import site; print(site.getusersitepackages().replace('/lib/python', '/bin').split('/lib/')[0] + '/bin')" 2>/dev/null) || true
                if [ -n "$user_bin" ] && ! echo "$PATH" | tr ':' '\n' | grep -qx "$user_bin"; then
                    warn "$user_bin is not in your PATH. Add it with:"
                    printf "  export PATH=\"%s:\$PATH\"\n\n" "$user_bin"
                fi
            fi
        fi
    fi

    # Verify
    if command -v "$COMMAND_NAME" >/dev/null 2>&1; then
        installed_version=$("$COMMAND_NAME" --version 2>/dev/null || echo "unknown")
        printf "\n${GREEN}${BOLD}Success!${RESET} ${PACKAGE_NAME} ${installed_version} is installed.\n"
    else
        printf "\n${GREEN}${BOLD}Installed!${RESET} You may need to restart your shell or add the install directory to your PATH.\n"
    fi

    printf "\nGet started:\n"
    printf "  ${BOLD}${COMMAND_NAME} login${RESET}      # authenticate with your API key\n"
    printf "  ${BOLD}${COMMAND_NAME}${RESET}             # launch interactive mode\n"
    printf "  ${BOLD}${COMMAND_NAME} search${RESET} ...  # search the web\n\n"
}

main
