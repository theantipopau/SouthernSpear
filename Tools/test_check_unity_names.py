"""
Tests for Tools/check_unity_names.py, on fixture files rather than the real tree.

    python Tools/test_check_unity_names.py      # exit 0 when the checker still bites
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_unity_names as c  # noqa: E402

CHECKER = os.path.join(HERE, "check_unity_names.py")
FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


ALPHA = """// fixture: shares Helper and Shared with Beta.cpp
namespace
{
\tint Helper(int Value)
\t{
\t\treturn Value + 1;
\t}
\tstatic int Shared = 1;
}

int AlphaEntry()
{
\treturn Helper(Shared);
}
"""

BETA = """// fixture: shares Helper and Shared with Alpha.cpp
namespace
{
\tint Helper(int Value)
\t{
\t\treturn Value + 2;
\t}
\tstatic int Shared = 2;
}

int BetaEntry()
{
\treturn Helper(Shared);
}
"""

GAMMA = """// fixture: names nothing else in the module uses
namespace
{
\tint Unique(int Value)
\t{
\t\treturn Value;
\t}
}

int GammaEntry()
{
\treturn Unique(3);
}
"""

DELTA = """// fixture: a local shadows the file's own helper
namespace
{
\tint Compute(int Value)
\t{
\t\treturn Value * 2;
\t}
}

int DeltaEntry()
{
\tint32 Compute = 5;
\treturn Compute;
}
"""


EPSILON = """// fixture: a local hides a member of the class it is defined in (C4458)
struct FEpsilon
{
	static int Compute(int Value);
};

int FEpsilon::Compute(int Value)
{
	const int Compute = Value;
	return Compute;
}
"""

ZETA = """// fixture: a local does NOT hide a member of some other class - no C4458, no C4459
struct FZetaMotion
{
	static void Step(int Value);
};

void FZetaMotion::Step(int Value)
{
	(void)Value;
}

void FZetaEntry()
{
	const float Step = 0.5f;
	FZetaMotion::Step((int)Step);
}
"""


def write(root, name, text):
    path = os.path.join(root, "Plugins", "SouthernSpearFixture", "Source",
                        "SouthernSpearFixture", "Private", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def main():
    with tempfile.TemporaryDirectory() as root:
        write(root, "Alpha.cpp", ALPHA)
        write(root, "Beta.cpp", BETA)
        write(root, "Gamma.cpp", GAMMA)
        write(root, "Delta.cpp", DELTA)
        write(root, "Epsilon.cpp", EPSILON)
        write(root, "Zeta.cpp", ZETA)

        findings = c.check_tree(root)
        found = {(f["kind"], f["name"]) for f in findings}
        shadows = [f for f in findings if f["kind"] == "shadow"]

        check("a helper defined in two files is flagged", ("clash", "Helper") in found, str(sorted(found)))
        check("a file-static variable defined in two files is flagged", ("clash", "Shared") in found)
        check("a local that shadows a file helper is flagged", ("shadow", "Compute") in found)
        check("a local that hides a member of its own class is flagged",
              any(f["name"] == "Compute" and "FEpsilon" in f["detail"] for f in shadows))
        check("a local does not hide a member of another class",
              not any(f["name"] == "Step" for f in findings),
              str([f["detail"] for f in findings if f["name"] == "Step"]))
        check("only the two real shadows are reported", len(shadows) == 2,
              "{0}".format([f["name"] for f in shadows]))
        check("a name unique to one file is not flagged",
              not any(f["name"] == "Unique" for f in findings))
        check("the module is named in the finding",
              all(f["module"] == "SouthernSpearFixture" for f in findings))
        check("only the two clashes are reported",
              len([f for f in findings if f["kind"] == "clash"]) == 2)

        result = subprocess.run([sys.executable, CHECKER, "--root", root], capture_output=True, text=True)
        check("the command exits 1 on a clash", result.returncode == 1, "exit {0}".format(result.returncode))

        private = os.path.join(root, "Plugins", "SouthernSpearFixture", "Source",
                               "SouthernSpearFixture", "Private")
        os.remove(os.path.join(private, "Beta.cpp"))  # the duplicate
        os.remove(os.path.join(private, "Delta.cpp"))  # the shadow
        os.remove(os.path.join(private, "Epsilon.cpp"))  # the second shadow
        result = subprocess.run([sys.executable, CHECKER, "--root", root], capture_output=True, text=True)
        check("removing the duplicates restores exit 0", result.returncode == 0,
              "exit {0}".format(result.returncode))

    with tempfile.TemporaryDirectory() as root:
        write(root, "Only.cpp", GAMMA)
        check("a clean module passes", c.check_tree(root) == [])

    print("{0} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
