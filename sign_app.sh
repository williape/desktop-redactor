#!/bin/bash

# Simple script to sign the app bundle properly
export CODESIGN_IDENTITY="Developer ID Application: Peter Williams (MCGN49R93E)"

echo "Code signing with identity: $CODESIGN_IDENTITY"

APP_PATH="dist/Presidio Desktop Redactor.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App bundle not found at $APP_PATH"
    exit 1
fi

echo "Creating entitlements file..."
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

echo "Signing all .so files..."
find "$APP_PATH" -name "*.so" -exec codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" {} \;

echo "Signing all .dylib files..."
find "$APP_PATH" -name "*.dylib" -exec codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" {} \;

echo "Signing main executable..."
codesign --force --verbose --timestamp --options runtime --sign "$CODESIGN_IDENTITY" "$APP_PATH/Contents/MacOS/Presidio Desktop Redactor"

echo "Signing app bundle with entitlements..."
codesign --force --verbose --timestamp --options runtime --entitlements entitlements.plist --sign "$CODESIGN_IDENTITY" "$APP_PATH"

echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

echo "Testing Gatekeeper..."
spctl --assess --type execute --verbose "$APP_PATH"

echo "Cleaning up..."
rm -f entitlements.plist

echo "✅ Signing complete!"