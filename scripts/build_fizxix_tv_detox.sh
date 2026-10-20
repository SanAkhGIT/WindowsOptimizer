#!/usr/bin/env bash
# Build a side-by-side FIZXIX-branded TV Detox launcher without replacing the
# official com.ansub.tvhome package or touching the TV.
set -euo pipefail

UPSTREAM_REPO="https://github.com/Ansub/tv-detox.git"
UPSTREAM_COMMIT="e0bb6073c759baaefc0d4a7426556686e511033b"
SOURCE_DIR="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/tv-detox-fizxix"
OUTPUT_DIR="${GITHUB_WORKSPACE:-$PWD}/dist"

rm -rf "$SOURCE_DIR"
git clone --no-checkout "$UPSTREAM_REPO" "$SOURCE_DIR"
git -C "$SOURCE_DIR" checkout --detach "$UPSTREAM_COMMIT"

python3 - "$SOURCE_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
package_files = [
    root / "AndroidManifest.xml",
    root / "build.sh",
    root / "install.sh",
    root / "check.sh",
    root / "undo.sh",
    root / "ci" / "smoke-test.sh",
    *sorted((root / "src" / "com" / "ansub" / "tvhome").glob("*.java")),
]
old_package = "com.ansub.tvhome"
new_package = "com.fizxix.tvhome"

for path in package_files:
    if not path.is_file():
        raise SystemExit(f"Expected upstream source file is missing: {path}")
    content = path.read_text(encoding="utf-8")
    if old_package in content:
        path.write_text(content.replace(old_package, new_package), encoding="utf-8")

manifest = root / "AndroidManifest.xml"
content = manifest.read_text(encoding="utf-8")
if 'android:label="Home"' not in content:
    raise SystemExit("Could not find expected launcher label in AndroidManifest.xml")
manifest.write_text(content.replace('android:label="Home"', 'android:label="FIZXIX Home"', 1), encoding="utf-8")

activity = root / "src" / "com" / "ansub" / "tvhome" / "MainActivity.java"
content = activity.read_text(encoding="utf-8")
start_marker = "    // Static warm gradient, drawn once by the window: no extra view, no animation.\n"
end_marker = "    private static GradientDrawable radial("
if content.count(start_marker) != 1 or content.count(end_marker) != 1:
    raise SystemExit("Could not safely locate the upstream background implementation; refusing an ambiguous patch.")
start = content.index(start_marker)
end = content.index(end_marker, start)
black_background = (
    "    // FIZXIX skin: use a true black background instead of the stock gradient.\n"
    "    private Drawable background() {\n"
    "        return new ColorDrawable(Color.BLACK);\n"
    "    }\n\n"
)
content = content[:start] + black_background + content[end:]

needle = "        setContentView(scroller);\n"
watermark = """        setContentView(scroller);

        // Fixed, subtle brand mark above the scroll view; it does not take remote focus.
        FrameLayout contentRoot = (FrameLayout) findViewById(android.R.id.content);
        TextView watermark = text(px(20), 0xBFFFFFFF, regular);
        watermark.setText("Modded by FIZXIX");
        watermark.setSingleLine(true);
        watermark.setClickable(false);
        watermark.setFocusable(false);
        FrameLayout.LayoutParams watermarkParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM | Gravity.RIGHT);
        watermarkParams.rightMargin = px(36);
        watermarkParams.bottomMargin = px(20);
        contentRoot.addView(watermark, watermarkParams);
"""
if content.count(needle) != 1:
    raise SystemExit("Could not safely locate setContentView(scroller); refusing to insert duplicate watermark.")
content = content.replace(needle, watermark, 1)
activity.write_text(content, encoding="utf-8")
print("Applied FIZXIX skin: side-by-side package, black background, bottom-right watermark.")
PY

cd "$SOURCE_DIR"
sh build.sh
mkdir -p "$OUTPUT_DIR"
cp out/tvhome.apk "$OUTPUT_DIR/FIZXIX-TV-Detox.apk"
printf 'Built %s\n' "$OUTPUT_DIR/FIZXIX-TV-Detox.apk"
