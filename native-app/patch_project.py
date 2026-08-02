"""
Run from the native-app/ folder, AFTER `npx cap add android` has created the
android/ project. Copies the Kotlin plugin files into place and patches
AndroidManifest.xml and MainActivity.java/.kt so NativeFocus and its service/
activity are registered. Also ensures the generated Android project is
configured to compile Kotlin sources (adds the kotlin-gradle-plugin and
applies the kotlin-android plugin to the app module) so the Kotlin plugin
files are visible to the Java sources.
Safe to re-run — it checks before adding anything.
"""
import os

BASE = "android/app/src/main"
PKG_DIR = "com/timesup/app"
FOCUS_DIR = f"{BASE}/java/{PKG_DIR}/focus"


def copy_plugin_files():
    os.makedirs(FOCUS_DIR, exist_ok=True)
    for fname in ["NativeFocusPlugin.kt", "FocusBlockerService.kt", "BlockerOverlayActivity.kt"]:
        src = f"native/{fname}"
        dst = f"{FOCUS_DIR}/{fname}"
        try:
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"ERROR: Expected plugin source '{src}' not found. Ensure you have the native/ files and re-run.")
            raise
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Copied {fname} -> {dst}")


def patch_manifest():
    path = f"{BASE}/AndroidManifest.xml"
    with open(path, "r", encoding="utf-8") as f:
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

    with open(path, "w", encoding="utf-8") as f:
        f.write(manifest)
    print("Patched AndroidManifest.xml")


def patch_gradle_for_kotlin():
    # Ensure the generated Android project will compile Kotlin sources.
    root_build = os.path.join("android", "build.gradle")
    app_build = os.path.join("android", "app", "build.gradle")
    kotlin_version = "1.8.22"

    # Patch root build.gradle to include the kotlin-gradle-plugin classpath
    if os.path.exists(root_build):
        with open(root_build, "r", encoding="utf-8") as f:
            content = f.read()

        if "kotlin-gradle-plugin" not in content:
            if "buildscript" in content:
                # Try to insert ext.kotlin_version and the classpath into the existing buildscript
                if "ext.kotlin_version" not in content:
                    content = content.replace("buildscript {", f"buildscript {{\n    ext.kotlin_version = '{kotlin_version}'", 1)
                # Insert classpath into the dependencies block inside buildscript
                bs_idx = content.find("buildscript")
                deps_idx = content.find("dependencies", bs_idx)
                if deps_idx != -1:
                    open_brace = content.find("{", deps_idx)
                    if open_brace != -1:
                        # find the closing brace for this dependencies block (naive - first '}' after open_brace)
                        close_brace = content.find("}", open_brace)
                        insert_at = close_brace
                        insert_text = f"\n        classpath \"org.jetbrains.kotlin:kotlin-gradle-plugin:{kotlin_version}\""
                        content = content[:insert_at] + insert_text + content[insert_at:]
                else:
                    # no dependencies block found; append a dependencies block
                    content = content.replace("buildscript {", f"buildscript {{\n    ext.kotlin_version = '{kotlin_version}'\n    repositories {{ google(); mavenCentral() }}\n    dependencies {{ classpath \"org.jetbrains.kotlin:kotlin-gradle-plugin:{kotlin_version}\" }}", 1)
            else:
                # No buildscript block at all; prepend one.
                bs = (
                    f"buildscript {{\n    ext.kotlin_version = '{kotlin_version}'\n    repositories {{ google(); mavenCentral() }}\n    dependencies {{ classpath \"org.jetbrains.kotlin:kotlin-gradle-plugin:{kotlin_version}\" }}\n}}\n\n"
                )
                content = bs + content

            with open(root_build, "w", encoding="utf-8") as f:
                f.write(content)
            print("Patched android/build.gradle to include kotlin-gradle-plugin")
        else:
            print("android/build.gradle already configures kotlin-gradle-plugin (or contains it); skipping patch")
    else:
        print("android/build.gradle not found — skipping kotlin Gradle patch")

    # Patch app module build.gradle to apply kotlin-android plugin and add stdlib dependency
    if os.path.exists(app_build):
        with open(app_build, "r", encoding="utf-8") as f:
            content = f.read()

        changed = False
        if "kotlin-android" not in content:
            # Apply plugin after the com.android.application apply line if present
            if "apply plugin: 'com.android.application'" in content:
                content = content.replace(
                    "apply plugin: 'com.android.application'",
                    "apply plugin: 'com.android.application'\napply plugin: 'kotlin-android'",
                    1,
                )
                changed = True
            elif content.strip().startswith("plugins {"):
                # Try to add id("org.jetbrains.kotlin.android") into plugins block
                plugins_start = content.find("plugins {")
                plugins_end = content.find("}", plugins_start)
                if plugins_end != -1:
                    insertion = "\n    id 'org.jetbrains.kotlin.android'"
                    content = content[:plugins_end] + insertion + content[plugins_end:]
                    changed = True

        # Ensure the kotlin stdlib dependency is present
        if "org.jetbrains.kotlin:kotlin-stdlib" not in content and "org.jetbrains.kotlin:kotlin-stdlib-jdk" not in content:
            # naive: insert into the first dependencies { ... } block
            deps_idx = content.find("dependencies {")
            if deps_idx != -1:
                open_brace = content.find("{", deps_idx)
                close_brace = content.find("}", open_brace)
                if close_brace != -1:
                    insert_at = close_brace
                    insert_text = f"\n    implementation \"org.jetbrains.kotlin:kotlin-stdlib:{kotlin_version}\""
                    content = content[:insert_at] + insert_text + content[insert_at:]
                    changed = True

        if changed:
            with open(app_build, "w", encoding="utf-8") as f:
                f.write(content)
            print("Patched android/app/build.gradle to apply kotlin-android and add kotlin stdlib")
        else:
            print("android/app/build.gradle already appears to apply kotlin plugin and have stdlib; skipping patch")
    else:
        print("android/app/build.gradle not found — skipping app module Gradle patch")


def patch_main_activity():
    main_activity_path = None
    # Search for Kotlin MainActivity first, then Java
    for root, _dirs, files in os.walk(f"{BASE}/java"):
        if "MainActivity.kt" in files:
            main_activity_path = os.path.join(root, "MainActivity.kt")
            break
        if "MainActivity.java" in files:
            main_activity_path = os.path.join(root, "MainActivity.java")
            break

    if not main_activity_path:
        print("WARNING: MainActivity not found — plugin not registered. Register it manually.")
        return

    with open(main_activity_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "registerPlugin" in content:
        print(f"{os.path.basename(main_activity_path)} already patched, skipping")
        return

    if main_activity_path.endswith('.java'):
        # Java-style patching (preserve existing logic)
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
    else:
        # Kotlin-style patching
        # Ensure imports are present
        if "import android.os.Bundle" not in content:
            content = content.replace(
                "import com.getcapacitor.BridgeActivity",
                "import android.os.Bundle\nimport com.getcapacitor.BridgeActivity\nimport com.timesup.app.focus.NativeFocusPlugin",
            )
        else:
            # ensure NativeFocusPlugin import exists
            if "com.timesup.app.focus.NativeFocusPlugin" not in content:
                content = content.replace(
                    "import com.getcapacitor.BridgeActivity",
                    "import com.getcapacitor.BridgeActivity\nimport com.timesup.app.focus.NativeFocusPlugin",
                )

        # Common Kotlin patterns: "class MainActivity : BridgeActivity()" or with braces
        if "class MainActivity : BridgeActivity()" in content:
            content = content.replace(
                "class MainActivity : BridgeActivity()",
                "class MainActivity : BridgeActivity() {\n"
                "    override fun onCreate(savedInstanceState: Bundle?) {\n"
                "        registerPlugin(NativeFocusPlugin::class.java)\n"
                "        super.onCreate(savedInstanceState)\n"
                "    }\n"
                "}",
            )
        else:
            # fallback: try to inject an onCreate after the class opening brace
            idx = content.find("class MainActivity")
            if idx != -1:
                brace_idx = content.find("{", idx)
                if brace_idx != -1:
                    insert_at = brace_idx + 1
                    oncreate = (
                        "\n    override fun onCreate(savedInstanceState: Bundle?) {\n"
                        "        registerPlugin(NativeFocusPlugin::class.java)\n"
                        "        super.onCreate(savedInstanceState)\n"
                        "    }\n"
                    )
                    content = content[:insert_at] + oncreate + content[insert_at:]
                else:
                    print("WARNING: Could not safely patch Kotlin MainActivity — please add plugin registration manually.")
                    return
            else:
                print("WARNING: Could not find MainActivity class declaration for Kotlin; plugin not registered.")
                return

    with open(main_activity_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched {main_activity_path}")


if __name__ == "__main__":
    copy_plugin_files()
    patch_manifest()
    patch_gradle_for_kotlin()
    patch_main_activity()
    print("Done.")
