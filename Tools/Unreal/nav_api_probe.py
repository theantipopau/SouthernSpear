"""Read-only inspection of nav-related APIs exposed to UE 5.8 Python."""
import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "nav_api_probe.json")
result = {
    "navigation_classes": sorted(n for n in dir(unreal) if "nav" in n.lower()),
    "navigation_system_members": sorted(n for n in dir(unreal.NavigationSystemV1) if "build" in n.lower() or "nav" in n.lower()),
    "editor_level_library_members": sorted(n for n in dir(unreal.EditorLevelLibrary) if "build" in n.lower() or "nav" in n.lower()),
    "editor_subsystems": sorted(n for n in dir(unreal) if "editor" in n.lower() and "subsystem" in n.lower()),
}
with open(OUT, "w", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
unreal.log("[NavApiProbe] wrote " + OUT)
