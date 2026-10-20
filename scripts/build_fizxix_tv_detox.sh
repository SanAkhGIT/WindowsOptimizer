#!/usr/bin/env bash
# Build a side-by-side FIZXIX-branded TV Detox launcher without replacing the
# official com.ansub.tvhome package or touching the TV.
set -euo pipefail

UPSTREAM_REPO="https://github.com/Ansub/tv-detox.git"
# Default to the upstream repository's current default branch. Set TV_DETOX_REF
# to a tag or commit SHA for a reproducible, pinned build.
UPSTREAM_REF="${TV_DETOX_REF:-HEAD}"
SOURCE_DIR="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/tv-detox-fizxix"
OUTPUT_DIR="${GITHUB_WORKSPACE:-$PWD}/dist"

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

# Pure black is the intended FIZXIX design, so remove the wallpaper chooser rather
# than leaving an option that cannot visibly change the background.
settings = root / "src" / "com" / "ansub" / "tvhome" / "MainActivity.java"
settings_content = settings.read_text(encoding="utf-8")
old_settings = 'private static final String[] SETTINGS_ITEMS = {"Wallpaper", "TV settings"};'
new_settings = 'private static final String[] SETTINGS_ITEMS = {"TV settings", "Wi-Fi", "Bluetooth", "Sound", "Picture"};'
if settings_content.count(old_settings) != 1:
    raise SystemExit("Could not safely locate the upstream Settings menu; refusing an ambiguous patch.")
settings.write_text(settings_content.replace(old_settings, new_settings, 1), encoding="utf-8")

# Keep the home-screen gear menu useful on FIZXIX's pure-black skin: direct TV settings
# plus connectivity, Bluetooth, sound and display shortcuts. Do not restore wallpaper choices.
activity_content = settings.read_text(encoding="utf-8")
old_open = '''            dropdown(tile(SETTINGS), SETTINGS_ITEMS, which -> {
                if (which == 0) showWallpapers();
                else try { startActivity(new Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); }
                catch (Exception ignored) {}
            });'''
new_open = '''            dropdown(tile(SETTINGS), SETTINGS_ITEMS, which -> {
                String action;
                switch (which) {
                    case 0: action = Settings.ACTION_SETTINGS; break;
                    case 1: action = Settings.ACTION_WIFI_SETTINGS; break;
                    case 2: action = Settings.ACTION_BLUETOOTH_SETTINGS; break;
                    case 3: action = Settings.ACTION_SOUND_SETTINGS; break;
                    case 4: action = Settings.ACTION_DISPLAY_SETTINGS; break;
                    default: return;
                }
                try { startActivity(new Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); }
                catch (Exception ignored) {
                    if (which != 0) try {
                        startActivity(new Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                    } catch (Exception ignoredAgain) {}
                }
            });'''
if activity_content.count(old_open) != 1:
    raise SystemExit("Could not safely locate the Settings gear action; refusing an ambiguous patch.")
settings.write_text(activity_content.replace(old_open, new_open, 1), encoding="utf-8")

activity = root / "src" / "com" / "ansub" / "tvhome" / "MainActivity.java"
content = activity.read_text(encoding="utf-8")
start_marker = "    // Static gradient, drawn once by the window: no extra view, no animation.\n"
end_marker = "    // The saved wallpaper, as an index into WALLPAPERS (Dusk if none is saved).\n"
if content.count(start_marker) != 1 or content.count(end_marker) != 1:
    raise SystemExit("Could not safely locate the upstream background implementation; refusing an ambiguous patch.")
start = content.index(start_marker)
end = content.index(end_marker, start)
black_background = (
    "    // FIZXIX skin: use a true black background instead of the stock gradient.\n"
    "    private Drawable background(int[] c) {\n"
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

# Route the remote Settings/Menu key to the main TV Settings screen, without an extra on-screen gear.
content = activity.read_text(encoding="utf-8")
method_anchor = "    @Override\n    protected void onCreate(Bundle state) {"
settings_method = """    // Linux reports this remote's gear key as KEY_UNKNOWN (Linux key code 240).
    // Android apps do not receive the raw MSC_SCAN HID usage, so scope the fallback
    // to the specific consumer-control device instead of matching every unknown key.
    private static final int LINUX_KEY_UNKNOWN = 240;
    private static final String FIZXIX_REMOTE_DEVICE = "RemoteG10 Consumer Control";

    private boolean isFizxixSettingsKey(KeyEvent event) {
        if (event.getKeyCode() == KeyEvent.KEYCODE_SETTINGS
                || event.getKeyCode() == KeyEvent.KEYCODE_MENU) {
            return true;
        }
        if (event.getKeyCode() != KeyEvent.KEYCODE_UNKNOWN
                || event.getScanCode() != LINUX_KEY_UNKNOWN) {
            return false;
        }
        android.view.InputDevice device = android.view.InputDevice.getDevice(event.getDeviceId());
        return device != null && FIZXIX_REMOTE_DEVICE.equals(device.getName());
    }

    private void openFizxixTvSettings() {
        try {
            startActivity(new Intent()
                    .setClassName("com.android.tv.settings", "com.android.tv.settings.MainSettings")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            android.util.Log.i("FIZXIX-Remote", "Opened main TV Settings from remote key.");
        } catch (Exception explicitFailure) {
            android.util.Log.w("FIZXIX-Remote", "Explicit TV Settings launch failed; trying ACTION_SETTINGS.",
                    explicitFailure);
            try {
                startActivity(new Intent(Settings.ACTION_SETTINGS)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            } catch (Exception fallbackFailure) {
                android.util.Log.e("FIZXIX-Remote", "Could not open TV Settings.", fallbackFailure);
            }
        }
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        // Diagnostic: log every key delivered to the Activity, before any matching.
        android.view.InputDevice diagDevice = android.view.InputDevice.getDevice(event.getDeviceId());
        android.util.Log.i("FIZXIX-Remote", "ACTIVITY KEY action=" + event.getAction()
                + " keyCode=" + event.getKeyCode() + " ("
                + KeyEvent.keyCodeToString(event.getKeyCode()) + ") scanCode=" + event.getScanCode()
                + " deviceId=" + event.getDeviceId() + " device="
                + (diagDevice == null ? "<null>" : diagDevice.getName())
                + " source=0x" + Integer.toHexString(event.getSource())
                + " flags=0x" + Integer.toHexString(event.getFlags()));
        if (isFizxixSettingsKey(event)) {
            if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                android.util.Log.i("FIZXIX-Remote", "Matched remote Settings key: keyCode="
                        + event.getKeyCode() + ", scanCode=0x"
                        + Integer.toHexString(event.getScanCode()) + ", deviceId=" + event.getDeviceId());
                openFizxixTvSettings();
            }
            return true;
        }
        if (event.getAction() == KeyEvent.ACTION_DOWN
                && event.getKeyCode() == KeyEvent.KEYCODE_UNKNOWN) {
            android.view.InputDevice device = android.view.InputDevice.getDevice(event.getDeviceId());
            android.util.Log.d("FIZXIX-Remote", "Observed unknown key: scanCode="
                    + event.getScanCode() + ", device="
                    + (device == null ? "<unknown>" : device.getName())
                    + ", deviceId=" + event.getDeviceId());
        }
        return super.dispatchKeyEvent(event);
    }

"""
if content.count(method_anchor) != 1:
    raise SystemExit("Could not safely locate onCreate for Settings key handler insertion.")
content = content.replace(method_anchor, settings_method + method_anchor, 1)
activity.write_text(content, encoding="utf-8")

# The physical key may be consumed by Android before MainActivity receives it.
# Add a user-enabled AccessibilityService to filter hardware keys globally. It does
# not inspect window content or handle gestures; it only handles Settings/Menu keys
# and the unknown key from RemoteG10 Consumer Control.
manifest_content = manifest.read_text(encoding="utf-8")
version_match = 'android:versionCode="14" android:versionName="1.5.1"'
if manifest_content.count(version_match) != 1:
    raise SystemExit("Could not safely bump the expected upstream app version.")
manifest_content = manifest_content.replace(version_match,
    'android:versionCode="16" android:versionName="1.5.3"', 1)
service_manifest = """        <service
            android:name=".RemoteKeyAccessibilityService"
            android:label="FIZXIX Remote Key Handler"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/fizxix_remote_key_service" />
        </service>
"""
activity_tag = '        <activity android:name=".MainActivity"'
if manifest_content.count(activity_tag) != 1 or "RemoteKeyAccessibilityService" in manifest_content:
    raise SystemExit("Could not safely insert the accessibility service into the manifest.")
manifest_content = manifest_content.replace(activity_tag, service_manifest + activity_tag, 1)
manifest.write_text(manifest_content, encoding="utf-8")

resource = root / "res" / "xml" / "fizxix_remote_key_service.xml"
resource.parent.mkdir(parents=True, exist_ok=True)
resource.write_text("""<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeAllMask"
    android:accessibilityFeedbackType="feedbackGeneric"
    android:accessibilityFlags="flagRequestFilterKeyEvents"
    android:notificationTimeout="0"
    android:canRetrieveWindowContent="false"
    android:canRequestFilterKeyEvents="true" />
""", encoding="utf-8")

service = root / "src" / "com" / "ansub" / "tvhome" / "RemoteKeyAccessibilityService.java"
service.write_text("""package com.fizxix.tvhome;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.util.Log;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;

/** Rootless fallback for remote keys that do not reach MainActivity. */
public final class RemoteKeyAccessibilityService extends AccessibilityService {
    private static final String TAG = "FIZXIX-Remote";
    private static final String REMOTE_DEVICE = "RemoteG10 Consumer Control";
    // KeyEvent.getScanCode() is the Linux key code, not the separate MSC_SCAN HID usage.
    private static final int LINUX_KEY_UNKNOWN = 240;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        AccessibilityServiceInfo info = getServiceInfo();
        if (info != null) {
            info.flags |= AccessibilityServiceInfo.FLAG_REQUEST_FILTER_KEY_EVENTS;
            setServiceInfo(info);
        }
        Log.i(TAG, "Remote key accessibility filter connected. serviceInfo.flags=0x"
                + Integer.toHexString(info == null ? -1 : info.flags)
                + " versionName=1.5.3");
        logInputDevices();
    }

    // Diagnostic: show which input devices Android knows about and how it names them.
    private void logInputDevices() {
        int[] ids = InputDevice.getDeviceIds();
        for (int i = 0; i < ids.length; i++) {
            InputDevice d = InputDevice.getDevice(ids[i]);
            if (d == null) {
                continue;
            }
            Log.i(TAG, "INPUT DEVICE id=" + ids[i] + " name=" + d.getName()
                    + " vendor=0x" + Integer.toHexString(d.getVendorId())
                    + " product=0x" + Integer.toHexString(d.getProductId())
                    + " sources=0x" + Integer.toHexString(d.getSources())
                    + " keyboardType=" + d.getKeyboardType());
        }
    }

    @Override
    public boolean onKeyEvent(KeyEvent event) {
        InputDevice device = InputDevice.getDevice(event.getDeviceId());
        String deviceName = device == null ? "<null>" : device.getName();

        // Diagnostic: log EVERY key the accessibility filter sees, before any matching.
        // If the gear key never appears here while getevent sees it, Android is not
        // delivering it to Java at all.
        Log.i(TAG, "A11Y KEY action=" + event.getAction()
                + " keyCode=" + event.getKeyCode() + " ("
                + KeyEvent.keyCodeToString(event.getKeyCode()) + ")"
                + " scanCode=" + event.getScanCode()
                + " deviceId=" + event.getDeviceId() + " device=" + deviceName
                + " source=0x" + Integer.toHexString(event.getSource())
                + " flags=0x" + Integer.toHexString(event.getFlags()));

        boolean remoteDevice = device != null && REMOTE_DEVICE.equals(device.getName());
        boolean standardSettingsKey = event.getKeyCode() == KeyEvent.KEYCODE_SETTINGS
                || event.getKeyCode() == KeyEvent.KEYCODE_MENU;
        boolean unknownRemoteKey = remoteDevice
                && event.getKeyCode() == KeyEvent.KEYCODE_UNKNOWN;

        // The scanCode == 240 assumption was never verified on this TV, so match any
        // KEYCODE_UNKNOWN from the named remote and rely on the log above for the real value.
        boolean gearKey = standardSettingsKey || unknownRemoteKey;
        if (!gearKey) {
            return false;
        }

        if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
            Log.i(TAG, "Matched Settings/Menu key in accessibility filter: keyCode="
                    + event.getKeyCode() + ", scanCode=" + event.getScanCode()
                    + ", device=" + (device == null ? "<unknown>" : device.getName()));
            openTvSettings();
        }
        // Consume down/up so the key cannot also trigger a second system action.
        return true;
    }

    private void openTvSettings() {
        try {
            startActivity(new Intent()
                    .setClassName("com.android.tv.settings", "com.android.tv.settings.MainSettings")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            Log.i(TAG, "Requested main TV Settings.");
        } catch (Exception explicitFailure) {
            Log.w(TAG, "Explicit Settings component failed; trying ACTION_SETTINGS.", explicitFailure);
            try {
                startActivity(new Intent(android.provider.Settings.ACTION_SETTINGS)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            } catch (Exception fallbackFailure) {
                Log.e(TAG, "Unable to launch TV Settings.", fallbackFailure);
            }
        }
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // No window content is retrieved or read. Log only the first event as a liveness check.
        if (!loggedFirstEvent) {
            loggedFirstEvent = true;
            Log.i(TAG, "First accessibility event received: type=" + event.getEventType());
        }
    }

    private boolean loggedFirstEvent;

    @Override
    public void onInterrupt() {
        Log.w(TAG, "Remote key accessibility filter interrupted.");
    }
}
""", encoding="utf-8")

# Add the new AccessibilityService XML resource to the minimal upstream aapt2 build.
build_file = root / "build.sh"
build_content = build_file.read_text(encoding="utf-8")
old_link = '"$BT/aapt2" link -o out/base.apk -I "$JAR" --manifest AndroidManifest.xml --min-sdk-version 21 --target-sdk-version 34'
new_link = '''"$BT/aapt2" compile --dir res -o out/compiled-resources.zip
"$BT/aapt2" link -o out/base.apk -I "$JAR" -R out/compiled-resources.zip --manifest AndroidManifest.xml --min-sdk-version 21 --target-sdk-version 34'''
if build_content.count(old_link) != 1:
    raise SystemExit("Could not safely locate aapt2 link command.")
build_file.write_text(build_content.replace(old_link, new_link, 1), encoding="utf-8")

# Extend the upstream emulator smoke test to assert that the brand watermark is visible.
smoke = root / "ci" / "smoke-test.sh"
smoke_content = smoke.read_text(encoding="utf-8")
clock_check = """echo "$x" | grep -qE 'text="[0-9]{1,2}:[0-9]{2}"' || fail "no clock"
"""
watermark_check = clock_check + """echo "$x" | grep -q 'text="Modded by FIZXIX"' || fail "no FIZXIX watermark"\n"""
if smoke_content.count(clock_check) != 1:
    raise SystemExit("Could not find exactly one clock smoke-test check; refusing an ambiguous patch.")
smoke.write_text(smoke_content.replace(clock_check, watermark_check, 1), encoding="utf-8")
print("Applied FIZXIX skin: black background, watermark, no extra gear, remote Settings/Menu key routes to the main TV Settings screen.")
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
