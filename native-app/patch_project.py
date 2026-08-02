#!/usr/bin/env python3
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def find_android_manifest():
    android_root = ROOT / "android"
    if not android_root.exists():
        print("DEBUG: android/ directory not found at:", android_root)
        print("DEBUG: listing contents of native-app:")
        for p in sorted(ROOT.iterdir()):
            print("  ", p.name)
        return None

    manifests = list(android_root.rglob("AndroidManifest.xml"))
    if not manifests:
        print("DEBUG: No AndroidManifest.xml found under", android_root)
        # show a small tree for debugging
        for dirpath, dirnames, filenames in os.walk(android_root):
            print(f"  {dirpath}/ -> {len(dirnames)} dirs, {len(filenames)} files")
            # limit output
            break
        return None

    # prefer the one under app/src/main if it exists
    for m in manifests:
        if "app" in m.parts and "src" in m.parts and "main" in m.parts:
            print("DEBUG: Using manifest:", m)
            return m
    print("DEBUG: Using first found manifest:", manifests[0])
    return manifests[0]

def patch_manifest(manifest_path: Path):
    # Example placeholder: open and perform safe text replacement
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except Exception as e:
        print("WARNING: Failed to read manifest", manifest_path, e)
        return
    # perform your existing patching logic here, e.g. ensure activity entry, permissions, etc.
    # For now just print the first 10 lines for debugging:
    print("--- manifest preview ---")
    for i, line in enumerate(text.splitlines()):
        if i >= 10:
            break
        print(line)
    print("--- end preview ---")
    # If you modify the text, write it back:
    # manifest_path.write_text(text, encoding="utf-8")

def main():
    manifest = find_android_manifest()
    if manifest is None:
        print("INFO: Skipping manifest patch because no AndroidManifest.xml was found.")
        # Do not raise / crash — pipeline should continue so next steps surface clearer errors
        return 0

    patch_manifest(manifest)
    return 0

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
