"""
Negative test for Tools/validate_architecture.py.

CLAUDE.md's rule is that the guard is proven by breaking the build it guards: copy Tools/ and the SS
plugins to a scratch folder, inject a violation, and expect exit 1.  This does that for rule SS010
(Core holds shared types, not content) so a future edit that defeats the rule is caught.

It never touches the real tree: everything runs in a temporary directory.

    python Tools/test_architecture_guard.py      # exit 0 when the guard still bites
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GUARD = os.path.join(HERE, "validate_architecture.py")

# A new Core source file that loads an asset, and one that only names a content path.
LOADS_ASSET = """// injected by Tools/test_architecture_guard.py
#include "CoreMinimal.h"
static UObject* SSInjectedLoad()
{
\treturn LoadObject<UObject>(nullptr, TEXT("/Game/Weapons/A88/A88_Test"));
}
"""

NAMES_CONTENT = """// injected by Tools/test_architecture_guard.py
#include "CoreMinimal.h"
namespace { const TCHAR* SSInjectedPath = TEXT("/SSExp_ObjectiveAssault/Test"); }
"""

FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def copy_tree(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("Intermediate", "Binaries", "*.gen.cpp", "*.generated.h"))


def build_scratch(root):
    """A minimal copy of the tree the guard walks: Tools/ and every SS plugin's Source/."""
    os.makedirs(os.path.join(root, "Tools"), exist_ok=True)
    shutil.copy2(GUARD, os.path.join(root, "Tools", "validate_architecture.py"))
    plugins = os.path.join(ROOT, "Plugins")
    for name in sorted(os.listdir(plugins)):
        if not name.startswith("SouthernSpear"):
            continue
        source = os.path.join(plugins, name, "Source")
        if os.path.isdir(source):
            copy_tree(source, os.path.join(root, "Plugins", name, "Source"))


def run_guard(root):
    result = subprocess.run([sys.executable, os.path.join(root, "Tools", "validate_architecture.py")],
                            capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main():
    with tempfile.TemporaryDirectory() as root:
        build_scratch(root)
        code, out = run_guard(root)
        check("the copied tree is clean", code == 0, "exit {0}".format(code))
        check("the accepted SSFonts.h hit is reported as a NOTE, not a failure",
              "SSFonts.h" in out and "NOTE" in out)
        check("SSFonts.h is the only Core exception and no SS010 failure is reported",
              "SS010" in out and "FAIL -" not in out)

        core = os.path.join(root, "Plugins", "SouthernSpearCore", "Source", "SouthernSpearCore", "Private")
        os.makedirs(core, exist_ok=True)
        injected = os.path.join(core, "SSInjectedLoad.cpp")
        with open(injected, "w", encoding="utf-8") as handle:
            handle.write(LOADS_ASSET)
        code, out = run_guard(root)
        check("a Core asset load fails the guard", code == 1 and "SS010" in out, "exit {0}".format(code))
        os.remove(injected)

        injected = os.path.join(core, "SSInjectedPath.cpp")
        with open(injected, "w", encoding="utf-8") as handle:
            handle.write(NAMES_CONTENT)
        code, out = run_guard(root)
        check("a Core content-path reference fails the guard", code == 1 and "SS010" in out,
              "exit {0}".format(code))
        os.remove(injected)

        code, out = run_guard(root)
        check("removing the violation restores exit 0", code == 0, "exit {0}".format(code))

    print("{0} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
