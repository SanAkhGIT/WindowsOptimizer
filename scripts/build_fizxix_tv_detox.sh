#!/usr/bin/env bash
# Build a side-by-side FIZXIX-branded TV Detox launcher without replacing the
# official com.ansub.tvhome package or touching the TV.
set -euo pipefail

UPSTREAM_REPO="https://github.com/Ansub/tv-detox.git"
# Default to the upstream repository's current default branch. Set TV_DETOX_REF
# to a tag or commit SHA for a reproducible, pinned build.
UPSTREAM_REF="\${TV_DETOX_REF:-origin/HEAD}"
SOURCE_DIR="\${RUNNER_TEMP:-\${TMPDIR:-/tmp}}/tv-detox-fizxix"
OUTPUT_DIR="\${GITHUB_WORKSPACE:-$PWD}/dist"

rm -rf "$SOURCE_DIR"
git clone --no-checkout "$UPSTREAM_REPO" "$SOURCE_DIR"
git -C "$SOURCE_DIR" fetch --force origin "$UPSTREAM_REF"
UPSTREAM_COMMIT="$(git -C "$SOURCE_DIR" rev-parse FETCH_HEAD)"
git -C "$SOURCE_DIR" checkout --detach "$UPSTREAM_COMMIT"
printf 'TV Detox upstream ref: %s\nTV Detox upstream commit: %s\n' "$UPSTREAM_REF" "$UPSTREAM_COMMIT"

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
        TextView watermark = text(px(24), 0xBFFFFFFF, regular);
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

# Extend the upstream emulator smoke test to assert that the brand watermark is visible.
smoke = root / "ci" / "smoke-test.sh"
smoke_content = smoke.read_text(encoding="utf-8")
clock_check = """echo "$x" | grep -qE 'text="[0-9]{1,2}:[0-9]{2}"' || fail "no clock"
"""
watermark_check = clock_check + """echo "$x" | grep -q 'text="Modded by FIZXIX"' || fail "no FIZXIX watermark"\n"""
if smoke_content.count(clock_check) != 1:
    raise SystemExit("Could not find exactly one clock smoke-test check; refusing an ambiguous patch.")
smoke.write_text(smoke_content.replace(clock_check, watermark_check, 1), encoding="utf-8")
print("Applied FIZXIX skin: side-by-side package, black background, bottom-right watermark and a UI smoke assertion.")
PY

cd "$SOURCE_DIR"
sh build.sh
mkdir -p "$OUTPUT_DIR"
cp out/tvhome.apk "$OUTPUT_DIR/FIZXIX-TV-Detox.apk"
cp LICENSE "$OUTPUT_DIR/FIZXIX-TV-Detox-LICENSE.txt"
cat > "$OUTPUT_DIR/FIZXIX-TV-Detox-NOTICE.txt" <<NOTICE
FIZXIX Home is a modified build based on TV Detox by Ansub.
Upstream source: https://github.com/Ansub/tv-detox
Upstream ref: $UPSTREAM_REF
Upstream commit: $UPSTREAM_COMMIT
The upstream MIT license is included as FIZXIX-TV-Detox-LICENSE.txt.
FIZXIX-specific changes: separate package ID com.fizxix.tvhome, solid black background,
and a fixed bottom-right "Modded by FIZXIX" watermark.
NOTICE
printf '%s\n' "$UPSTREAM_COMMIT" > "$OUTPUT_DIR/FIZXIX-TV-Detox-UPSTREAM-COMMIT.txt"
printf 'Built %s from upstream commit %s\n' "$OUTPUT_DIR/FIZXIX-TV-Detox.apk" "$UPSTREAM_COMMIT"
