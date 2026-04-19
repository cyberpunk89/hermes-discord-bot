#!/bin/bash
set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Setting up Hermes bot at: $INSTALL_DIR"

# Inject the install path into all SKILL.md files
find "$INSTALL_DIR/skills" -name "SKILL.md" | while read -r f; do
    sed -i "s|<INSTALL_DIR>|$INSTALL_DIR|g" "$f"
done
echo "Skill paths configured."

# Copy .env template if .env doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    echo "Created .env — fill in your API keys before starting."
else
    echo ".env already exists, skipping."
fi

# Wire up skills in Hermes config
HERMES_CONFIG="$HOME/.hermes/config.yaml"
if [ -f "$HERMES_CONFIG" ]; then
    if ! grep -q "$INSTALL_DIR/skills" "$HERMES_CONFIG"; then
        echo ""
        echo "Add this to $HERMES_CONFIG under 'skills.external_dirs':"
        echo "  - $INSTALL_DIR/skills"
    fi
else
    echo ""
    echo "Hermes config not found at $HERMES_CONFIG."
    echo "Create it and add:"
    echo ""
    echo "skills:"
    echo "  external_dirs:"
    echo "    - $INSTALL_DIR/skills"
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Update ~/.hermes/config.yaml (see above)"
echo "  3. Run: hermes gateway run"
