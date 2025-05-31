#!/bin/bash

# Get the directory where the script itself is located, reliably.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Default virtual environment folder name (can still be changed here if needed)
VENV_NAME=".venv"

# --- Prompt user for alias name ---
DEFAULT_ALIAS_NAME="fetch-ctf"
read -p "Enter your desired alias name (default: $DEFAULT_ALIAS_NAME): " USER_ALIAS_NAME
ALIAS_NAME=${USER_ALIAS_NAME:-$DEFAULT_ALIAS_NAME}
# --- End prompt for alias name ---

PYTHON_SCRIPT_PATH="$SCRIPT_DIR/main.py"
PYTHON_VENV_PATH="$SCRIPT_DIR/$VENV_NAME" # Changed variable name for clarity

# Check if a virtual environment is created
if [ ! -d "$PYTHON_VENV_PATH" ]; then
    echo "Creating virtual environment at $PYTHON_VENV_PATH..."
    python3 -m venv "$PYTHON_VENV_PATH"

    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi

    # Activate the virtual environment for dependency installation
    source "$PYTHON_VENV_PATH/bin/activate"

    # Install dependencies
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "Installing requirements from $SCRIPT_DIR/requirements.txt..."
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        echo "$SCRIPT_DIR/requirements.txt not found!"
        # Deactivate before exiting if requirements are not found after venv creation
        deactivate
        exit 1
    fi
    
    # Deactivate after installation
    deactivate
    echo "Virtual environment setup complete."
else
    echo "Virtual environment already exists at $PYTHON_VENV_PATH."
fi 

# Determine the correct shell configuration file
SHELL_RC_FILE=""
CURRENT_SHELL_BASENAME=$(basename "$SHELL")

case "$CURRENT_SHELL_BASENAME" in
    bash)
        SHELL_RC_FILE="$HOME/.bashrc"
        ;;
    zsh)
        SHELL_RC_FILE="$HOME/.zshrc"
        ;;
    fish)
        SHELL_RC_FILE="$HOME/.config/fish/config.fish"
        ;;
    *)
        echo "Unsupported shell: $CURRENT_SHELL_BASENAME. Please add the alias manually."
        echo "Alias command to add:"
        if [[ "$CURRENT_SHELL_BASENAME" == "fish" ]]; then
            echo "alias $ALIAS_NAME 'source \"$PYTHON_VENV_PATH/bin/activate\"; python \"$PYTHON_SCRIPT_PATH\"; deactivate'"
        else
            echo "alias $ALIAS_NAME='source \"$PYTHON_VENV_PATH/bin/activate\" && python \"$PYTHON_SCRIPT_PATH\"; deactivate'"
        fi
        exit 1
        ;;
esac

# Define the alias command using absolute paths derived from SCRIPT_DIR
# These paths will be written literally into the shell configuration file.
if [[ "$CURRENT_SHELL_BASENAME" == "fish" ]]; then
    # Fish shell uses a slightly different syntax for alias and command separation
    ALIAS_CMD="alias $ALIAS_NAME 'source \"$PYTHON_VENV_PATH/bin/activate\"; python \"$PYTHON_SCRIPT_PATH\"; deactivate'"
else
    # POSIX-like shells (bash, zsh)
    ALIAS_CMD="alias $ALIAS_NAME='source \"$PYTHON_VENV_PATH/bin/activate\" && python \"$PYTHON_SCRIPT_PATH\"; deactivate'"
fi

# Add alias if it doesn't exist
# Using a more robust grep: -F for fixed string, -q for quiet, -x for whole line match (optional but stricter)
# Simplified grep: check if a line *starts* with "alias ALIAS_NAME=" or "alias ALIAS_NAME "
if ! grep -qE "^alias ${ALIAS_NAME}=" "$SHELL_RC_FILE" && ! grep -qE "^alias ${ALIAS_NAME} " "$SHELL_RC_FILE"; then
    echo "Adding alias '$ALIAS_NAME' to $SHELL_RC_FILE..."
    echo "" >> "$SHELL_RC_FILE" # Add a newline for separation
    echo "# Alias for $ALIAS_NAME (added by setup.sh)" >> "$SHELL_RC_FILE"
    echo "$ALIAS_CMD" >> "$SHELL_RC_FILE"
    echo "Alias added. Please run 'source $SHELL_RC_FILE' or restart your terminal to use it."
else
    echo "Alias '$ALIAS_NAME' or a similar definition already exists in $SHELL_RC_FILE."
fi