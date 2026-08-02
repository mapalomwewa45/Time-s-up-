"""
Run from the native-app/ folder, AFTER `npx cap add android` has created the
android/ project. Copies the Kotlin plugin files into place and patches
AndroidManifest.xml and MainActivity.java so NativeFocus and its service/
activity are registered. Safe to re-run — it checks before adding anything.
"""
import os

BASE = "android/app/src/main"
PKG_DIR = "com/timesup/app"
FOCUS_DIR = f"{BASE}/java/{PKG_DIR}/focus"

def copy_plugin_files():
    os.makedirs(FOCUS_DIR, exist_ok=True)
    for fname in ["NativeFocusPlugin.kt", "FocusBlockerService.kt", "BlockerOverlayActivity.kt"]:
        with open(f"native/{fname}") as f:
            content = f.read()
        with open(f"{FOCUS_DIR}/{fname}", "w") as f:
            f.write(content)
        print(f"Copied {fname} -> {FOCUS_DIR}/{fname}")

def patch_manifest():
    path = f"{BASE}/AndroidManifest.xml"
    with open(path) as f:
        manifest = f.read()

    if "xmlns:tools" not in manifest:
        manifest = manifest.replace(
            "<manifest ", '<manifest xmlns:tools="http://schemas.android.com/tools" ', 1
        )

    if "PACKAGE_USAGE_STATS" not in manifest:
        permissions = (
            '\n    <uses-permission android:name="android.permission.PACKAGE_USAGE_STATS" '
            'tools:ignore="ProtectedPermissions" />'
            '\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />'
            '\n    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />'
            '\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />'
            '\n    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n'
        )
        manifest = manifest.replace("<application", permissions + "\n    <application", 1)

    if "FocusBlockerService" not in manifest:
        additions = (
            '\n        <service android:name=".focus.FocusBlockerService" '
            'android:foregroundServiceType="specialUse" android:exported="false" />'
            '\n        <activity android:name=".focus.BlockerOverlayActivity" android:exported="false" '
            'android:theme="@style/Theme.AppCompat.NoActionBar" android:excludeFromRecents="true" '
            'android:launchMode="singleTask" />\n    '
        )
        manifest = manifest.replace("</application>", additions + "</application>", 1)

    with open(path, "w") as f:
        f.write(manifest)
    print("Patched AndroidManifest.xml")

def patch_main_activity():
    main_activity_path = None
    for root, _dirs, files in os.walk(f"{BASE}/java"):
        if "MainActivity.java" in files:
            main_activity_path = os.path.join(root, "MainActivity.java")
            break
    if not main_activity_path:
        print("WARNING: MainActivity.java not found — plugin not registered. Register it manually.")
        return

    with open(main_activity_path) as f:
        content = f.read()

    if "registerPlugin" in content:
        print("MainActivity.java already patched, skipping")
        return

    content = content.replace(
        "import com.getcapacitor.BridgeActivity;",
        "import android.os.Bundle;\nimport com.getcapacitor.BridgeActivity;\nimport com.timesup.app.focus.NativeFocusPlugin;",
    )
    content = content.replace(
        "public class MainActivity extends BridgeActivity {}",
        "public class MainActivity extends BridgeActivity {\n"
        "    @Override\n"
        "    public void onCreate(Bundle savedInstanceState) {\n"
        "        registerPlugin(NativeFocusPlugin.class);\n"
        "        super.onCreate(savedInstanceState);\n"
        "    }\n"
        "}",
    )
    with open(main_activity_path, "w") as f:
        f.write(content)
    print(f"Patched {main_activity_path}")

if __name__ == "__main__":
    copy_plugin_files()
    patch_manifest()
    patch_main_activity()
    print("Done.")
