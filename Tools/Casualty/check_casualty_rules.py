"""
Southern Spear - casualty rule checks outside Unreal (ADR-040).

Compiles the game's own engine-free headers (SSCasualtyRules.h and the shared checks in
Private/Tests/SSCasualtyRuleChecks.h, the same ones SouthernSpear.Casualty.Rules runs) with g++
and runs every check.

    python Tools/Casualty/check_casualty_rules.py

Exit 0 only when every check holds.
"""

import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = os.path.join(ROOT, "Plugins", "SouthernSpearCasualty", "Source", "SouthernSpearCasualty")
MAIN = r"""
#include "SSCasualtyRuleChecks.h"
#include <cstdio>
int main()
{
    const SSCasualtyChecks::FReport R = SSCasualtyChecks::RunAll();
    for (const std::string& F : R.Failures) std::printf("FAIL %s\n", F.c_str());
    std::printf("%d checks, %d failure(s)\n", R.Checks, (int)R.Failures.size());
    return R.Failures.empty() ? 0 : 1;
}
"""


def main():
    compiler = os.environ.get("CXX", "g++")
    with tempfile.TemporaryDirectory() as scratch:
        source = os.path.join(scratch, "main.cpp")
        binary = os.path.join(scratch, "casualty_checks" + (".exe" if os.name == "nt" else ""))
        with open(source, "w", encoding="utf-8") as fh:
            fh.write(MAIN)
        build = [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                 "-I", os.path.join(MODULE, "Public"), "-I", os.path.join(MODULE, "Private", "Tests"),
                 source, "-o", binary]
        result = subprocess.run(build, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout + result.stderr)
            print("compile failed")
            return 1
        return subprocess.run([binary]).returncode


if __name__ == "__main__":
    sys.exit(main())
