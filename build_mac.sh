#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
rm -rf build dist

# Phase 5: Reduced build size by only bundling essential models
# Users can import additional models after installation
pyinstaller --clean --onedir --windowed \
    --name "Presidio Desktop Redactor" \
    --icon "src/resources/icons/app_icon.icns" \
    --add-data "venv/lib/python*/site-packages/spacy/lang:spacy/lang" \
    --add-data "venv/lib/python*/site-packages/en_core_web_sm:en_core_web_sm" \
    --add-data "venv/lib/python*/site-packages/en_core_web_md:en_core_web_md" \
    --hidden-import "spacy" \
    --hidden-import "presidio_analyzer" \
    --hidden-import "presidio_anonymizer" \
    --hidden-import "pandas" \
    --hidden-import "pandas._libs.tslibs.base" \
    --hidden-import "yaml" \
    src/main.py

# Note: Large models (en_core_web_lg) are no longer bundled to reduce installer size
# Users can import them using the model management interface
echo "Note: Large models excluded from bundle. Users can import via UI."

# Code signing (if developer certificate available)
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Code signing with identity: $CODESIGN_IDENTITY"
    codesign --deep --force --verify --verbose --sign "$CODESIGN_IDENTITY" "dist/Presidio Desktop Redactor.app"
    echo "Verifying code signature..."
    codesign --verify --deep --strict --verbose=2 "dist/Presidio Desktop Redactor.app"
else
    echo "Warning: No code signing identity set. App may be blocked by Gatekeeper."
    echo "To sign: export CODESIGN_IDENTITY='Developer ID Application: Your Name'"
fi

# Create DMG installer
create-dmg \
    --volname "Presidio Desktop Redactor" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "Presidio Desktop Redactor.app" 200 190 \
    --hide-extension "Presidio Desktop Redactor.app" \
    --app-drop-link 400 190 \
    "Presidio Desktop Redactor.dmg" \
    "dist/"

echo "Build complete! DMG created."