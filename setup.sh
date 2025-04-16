#!/bin/bash

SCRIPT_DIR="$(pwd)" # shell script directory
ALIAS_NAME="new_challenge" # new alias; can be changed
VENV=".venv" # virtual enviroment folder; can be changed

PYTHON_SCRIPT_PATH="$SCRIPT_DIR/main.py"
PYTHON_VENV="$SCRIPT_DIR/$VENV"

# Check if a virtual enviroment is created
if [ ! -d "$PYTHON_VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $PYTHON_VENV

    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi

    source "$PYTHON_VENV/bin/activate"

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        echo "Installing requirements..."
        pip install -r requirements.txt
        deactivate
    else
        echo "requirements.txt not found!"
        deactivate
        exit 1
    fi

    echo "Setup complete."
    exit 0
fi 

# Create the alias in the correct shell
case "$SHELL" in
    */bash)
        SHELL_RC="$HOME/.bashrc"
        ;;
    */zsh)
        SHELL_RC="$HOME/.zshrc"
        ;;
    */fish)
        SHELL_RC="$HOME/.config/fish/config.fish"
        ;;
    *)
        echo "Unknown shell. Please add the alias manually."
        exit 1
        ;;
esac

if [[ "$SHELL" == */fish ]]; then
    ALIAS_CMD="alias $ALIAS_NAME 'source $(pwd)/$VENV/bin/activate; python $(pwd)/main.py'"
else
    ALIAS_CMD="alias $ALIAS_NAME=\"source $(pwd)/$VENV/bin/activate && python $(pwd)/main.py\""
fi

# Add alias if it doesn't exist
if ! grep -q "$ALIAS_NAME" "$SHELL_RC"; then
    echo "Adding alias '$ALIAS_NAME' to $SHELL_RC..."
    echo "$ALIAS_CMD" >> "$SHELL_RC"
    echo "Alias added. Run 'source $SHELL_RC' or restart your terminal to use it."
else
    echo "Alias '$ALIAS_NAME' already exists in $SHELL_RC."
fi