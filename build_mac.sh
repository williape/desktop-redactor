#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Clean previous builds
rm -rf build dist

# Bundle only small and medium spaCy models (not large)
echo "Bundling small and medium spaCy models only..."

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

echo "Build complete with small and medium models. Large model excluded for size optimization."

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

# Create DMG installer with simplified configuration to avoid AppleScript errors
create-dmg \
    --volname "Presidio Desktop Redactor" \
    --window-size 600 400 \
    --icon-size 100 \
    --app-drop-link 400 190 \
    "Presidio Desktop Redactor.dmg" \
    "dist/"

echo "Build complete! DMG created."