#!/bin/bash

set -e  # Terminates the script in case of errors
set -u  # Terminates the script if an unset variable is used
set -o pipefail  # Terminates the script if a command in a pipe fails

# Update and installation of pipx
apt update && apt install -y pipx

# Installations with pipx
pipx install hatch
pipx install pre-commit
pipx install hatch-pip-compile

# Configure Hatch
hatch config set dirs.env.virtual .direnv

# .pytanis directory and config.toml file (see README)
DIR="$HOME/.pytanis"
FILE="$DIR/config.toml"

# Check if the file exists
if [ ! -f "$FILE" ]; then
    # Create the directory if it doesn't exist
    mkdir -p "$DIR"

    # Write the content to the file
    cat > "$FILE" <<EOF
[Pretalx]
api_token = ""

[Google]
client_secret_json = "client_secret.json"
token_json = "token.json"
service_user_authentication = false

[HelpDesk]
account = ""
entity_id = ""
token = ""
EOF
    echo "File created at $FILE"
else
    echo "File already exists at $FILE"
fi
