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
    --add-data "src/ui:ui" \
    --add-data "src/core:core" \
    --add-data "src/utils:utils" \
    --add-data "src/resources:resources" \
    --add-data "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/presidio_analyzer:presidio_analyzer" \
    --paths "src" \
    --hidden-import "spacy" \
    --hidden-import "presidio_analyzer" \
    --hidden-import "presidio_anonymizer" \
    --hidden-import "pandas" \
    --hidden-import "pandas._libs.tslibs.base" \
    --hidden-import "yaml" \
    --hidden-import "ui" \
    --hidden-import "ui.main_window" \
    --hidden-import "ui.components" \
    --hidden-import "ui.components.preview_panel" \
    --hidden-import "ui.components.findings_table" \
    --hidden-import "ui.widgets" \
    --hidden-import "ui.widgets.encryption_widget" \
    --hidden-import "ui.widgets.list_widget" \
    --hidden-import "core" \
    --hidden-import "core.presidio_manager" \
    --hidden-import "core.file_processor" \
    --hidden-import "core.custom_recognizers" \
    --hidden-import "core.encryption_manager" \
    --hidden-import "core.list_manager" \
    --hidden-import "core.preview_manager" \
    --hidden-import "core.findings_model" \
    --hidden-import "utils" \
    --hidden-import "utils.logging_config" \
    --hidden-import "utils.config_manager" \
    src/main.py

echo "Build complete with small and medium models."

# Create entitlements file for PyQt/PyInstaller apps
cat > entitlements.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
EOF

# Enhanced code signing for PyQt/PyInstaller apps
# Auto-detect signing identity if not set
if [ -z "$CODESIGN_IDENTITY" ]; then
    echo "No CODESIGN_IDENTITY set, attempting to auto-detect Developer ID..."
    DETECTED_IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)"/\1/')
    if [ -n "$DETECTED_IDENTITY" ]; then
        CODESIGN_IDENTITY="$DETECTED_IDENTITY"
        echo "Auto-detected identity: $CODESIGN_IDENTITY"
    fi
fi

if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Code signing with identity: $CODESIGN_IDENTITY"
    echo "Verifying signing identity exists..."
    security find-identity -v -p codesigning | grep "$CODESIGN_IDENTITY" || echo "Warning: Identity not found in keychain"
    
    APP_PATH="dist/Presidio Desktop Redactor.app"
    BUNDLE_PATH="dist/Presidio Desktop Redactor"
    
    # Determine which format PyInstaller created
    if [ -d "$APP_PATH" ]; then
        echo "Found app bundle format: $APP_PATH"
        SIGN_PATH="$APP_PATH"
    elif [ -d "$BUNDLE_PATH" ]; then
        echo "Found onedir bundle format: $BUNDLE_PATH"
        SIGN_PATH="$BUNDLE_PATH"
    else
        echo "❌ Could not find built application"
        exit 1
    fi
    
    # Sign all .so files (Python extensions) - verbose mode for debugging
    echo "Signing Python extensions (.so files)..."
    echo "Looking for .so files in: $SIGN_PATH"
    find "$SIGN_PATH" -name "*.so" -print0 | while IFS= read -r -d '' file; do
        echo "Signing: $file"
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$file" || echo "Failed to sign: $file"
    done
    
    # Sign all dylibs
    echo "Signing dynamic libraries..."
    echo "Looking for .dylib files in: $SIGN_PATH"
    find "$SIGN_PATH" -name "*.dylib" -print0 | while IFS= read -r -d '' file; do
        echo "Signing: $file"
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$file" || echo "Failed to sign: $file"
    done
    
    # Sign all frameworks and their internal binaries
    echo "Signing frameworks..."
    find "$SIGN_PATH" -name "*.framework" -print0 | while IFS= read -r -d '' framework; do
        echo "Signing framework: $framework"
        # Sign the main framework binary if it exists
        framework_name=$(basename "$framework" .framework)
        framework_binary="$framework/Versions/Current/$framework_name"
        if [ ! -f "$framework_binary" ]; then
            # Try alternative paths
            framework_binary="$framework/Versions/5/$framework_name"
        fi
        if [ ! -f "$framework_binary" ]; then
            framework_binary="$framework/$framework_name"
        fi
        
        if [ -f "$framework_binary" ]; then
            echo "Signing framework binary: $framework_binary"
            codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$framework_binary" || echo "Failed to sign: $framework_binary"
        fi
        
        # Sign the framework bundle itself
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$framework" || echo "Failed to sign: $framework"
    done
    
    # Sign the main executable (different paths for app bundle vs onedir)
    echo "Signing main executable..."
    if [ -d "$APP_PATH" ]; then
        # App bundle format
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$APP_PATH/Contents/MacOS/Presidio Desktop Redactor"
    else
        # Onedir format
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$BUNDLE_PATH/Presidio Desktop Redactor"
    fi
    
    # Sign any other executables
    echo "Signing other executables..."
    find "$SIGN_PATH" -type f -perm +111 -not -name "Presidio Desktop Redactor" -print0 | while IFS= read -r -d '' file; do
        echo "Signing executable: $file"
        codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$file" || echo "Failed to sign: $file"
    done
    
    # Sign the main bundle with entitlements
    echo "Signing main application bundle..."
    if [ -d "$APP_PATH" ]; then
        codesign --force --verify --verbose --timestamp --options runtime --entitlements entitlements.plist --sign "$CODESIGN_IDENTITY" "$APP_PATH"
    else
        # For onedir, we can't use entitlements on the directory, sign the main executable instead
        codesign --force --verify --verbose --timestamp --options runtime --entitlements entitlements.plist --sign "$CODESIGN_IDENTITY" "$BUNDLE_PATH/Presidio Desktop Redactor"
    fi
    
    echo "Verifying code signature..."
    if codesign --verify --deep --strict --verbose=2 "$SIGN_PATH"; then
        echo "✅ Code signature verification successful"
    else
        echo "❌ Code signature verification failed"
        exit 1
    fi
    
    # Test Gatekeeper assessment
    echo "Testing Gatekeeper assessment..."
    if [ -d "$APP_PATH" ]; then
        # App bundle format
        if spctl --assess --type execute --verbose "$APP_PATH"; then
            echo "✅ Gatekeeper assessment passed"
        else
            echo "⚠️  Gatekeeper assessment failed - app may be blocked"
        fi
    else
        # Onedir format - skip Gatekeeper test as it's for app bundles
        echo "⚠️  Skipping Gatekeeper assessment for onedir format"
    fi
    
else
    echo "Warning: No code signing identity set. App may be blocked by Gatekeeper."
    echo "To sign: export CODESIGN_IDENTITY='Developer ID Application: name (team-ID)'"
fi

# Clean up onedir format if it exists (only keep app bundle)
if [ -d "dist/Presidio Desktop Redactor" ]; then
    echo "Removing onedir format to avoid conflicts in DMG..."
    rm -rf "dist/Presidio Desktop Redactor"
fi

# Create DMG installer
echo "Creating DMG installer..."
# Remove any existing DMG to avoid "File exists" error
rm -f "Presidio Desktop Redactor.dmg"
create-dmg \
    --volname "Presidio Desktop Redactor" \
    --window-size 600 400 \
    --icon-size 100 \
    --app-drop-link 400 190 \
    "Presidio Desktop Redactor.dmg" \
    "dist/"

# Sign the DMG if code signing identity is available
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "Signing DMG..."
    codesign --force --sign "$CODESIGN_IDENTITY" "Presidio Desktop Redactor.dmg"
    
    echo "Verifying DMG signature..."
    if codesign --verify --verbose "Presidio Desktop Redactor.dmg"; then
        echo "✅ DMG signature verification successful"
    else
        echo "❌ DMG signature verification failed"
    fi
fi

# Clean up
rm -f entitlements.plist

echo "Build complete! DMG created and signed."
echo ""
echo "Next steps for distribution:"
echo "1. Set up notarisation credentials:"
echo "   xcrun notarytool store-credentials \"notarytool-profile\" \\"
echo "   --apple-id \"your-apple-id@example.com\" \\"
echo "   --team-id \"team-ID\" \\"
echo "   --password \"app-specific-password\""
echo ""
echo "2. Submit for notarisation:"
echo "   xcrun notarytool submit \"Presidio Desktop Redactor.dmg\" \\"
echo "   --keychain-profile \"notarytool-profile\" \\"
echo "   --wait"
echo ""
echo "3. Staple notarisation:"
echo "   xcrun stapler staple \"Presidio Desktop Redactor.dmg\""