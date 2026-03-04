#!/bin/bash
set -e

VERSION="$1"

if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh v0.5.5"
  exit 1
fi

ZIP_NAME="p2000-model-${VERSION}"

echo "Creating split zip..."
rm -f ${ZIP_NAME}.zip ${ZIP_NAME}.z[0-9]*
zip -s 1900m -r "${ZIP_NAME}.zip" build/p2000-gguf/

ASSETS="${ZIP_NAME}.zip"
for part in ${ZIP_NAME}.z[0-9]*; do
  [ -f "$part" ] && ASSETS="$ASSETS $part"
done

NOTES="## Download & Extract

\`\`\`bash
VERSION=\$(gh release view --repo david-vos/p2000-location-llm --json tagName -q .tagName) && \\
gh release download \"\$VERSION\" --repo david-vos/p2000-location-llm --dir . && \\
zip -s 0 \"p2000-model-\${VERSION}.zip\" --out \"p2000-model-\${VERSION}-combined.zip\" && \\
unzip \"p2000-model-\${VERSION}-combined.zip\" && \\
rm p2000-model-\${VERSION}.z* p2000-model-\${VERSION}-combined.zip
\`\`\`"

echo "Creating GitHub release ${VERSION}..."
gh release create "$VERSION" $ASSETS --title "$VERSION" --notes "$NOTES"

echo "Cleaning up zip files..."
rm -f ${ZIP_NAME}.zip ${ZIP_NAME}.z[0-9]*

echo "Done! Release ${VERSION} created."
