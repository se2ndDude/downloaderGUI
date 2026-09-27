from pathlib import Path
import re

log = Path("failed.log").read_text(encoding="utf-8", errors="replace")
spec_path = Path("buildozer.spec")
wf_path = Path(".github/workflows/android.yml")

spec = spec_path.read_text(encoding="utf-8")
wf = wf_path.read_text(encoding="utf-8")
changes = []

def replace_once(text, old, new, message):
    if old in text:
        text = text.replace(old, new, 1)
        changes.append(message)
    return text

if re.search(r"\b(?:preadv|pwritev)\b", log):
    spec = replace_once(spec, "android.minapi = 23", "android.minapi = 24",
                        "Raised android.minapi to 24 for preadv/pwritev.")
    spec = replace_once(spec, "android.ndk_api = 23", "android.ndk_api = 24",
                        "Raised android.ndk_api to 24 for preadv/pwritev.")

if "LT_SYS_SYMBOL_USCORE" in log or "undefined macro: LT_" in log:
    wf = replace_once(wf, "runs-on: ubuntu-24.04", "runs-on: ubuntu-22.04",
                      "Pinned the runner to Ubuntu 22.04 for libffi/autotools.")
    if "libltdl-dev" not in wf:
        wf = replace_once(
            wf,
            "openjdk-17-jdk python3-venv autoconf libtool ",
            "openjdk-17-jdk python3-venv autoconf libtool libltdl-dev ",
            "Added libltdl-dev for Libtool macros."
        )

if "fatal: couldn't find remote ref" in log and "python-for-android" in log:
    wf2, n = re.subn(
        r"      - name: Clone patched python-for-android\n"
        r"        run: \|\n"
        r"(?:          .*\n)+\n",
        "",
        wf,
        count=1,
        flags=re.MULTILINE,
    )
    if n:
        wf = wf2
        changes.append("Removed manual python-for-android clone.")
    if "p4a.branch = develop" not in spec:
        spec += "\np4a.branch = develop\np4a.commit = d2ee8c5\n"
        changes.append("Pinned python-for-android through Buildozer.")

if "No such file or directory" in log and ".buildozer/android/platform/python-for-android" in log:
    if "rm -rf .buildozer" not in wf:
        marker = "      - name: Build debug APK\n"
        insert = (
            "      - name: Start from a clean Buildozer state\n"
            "        run: |\n"
            "          rm -rf .buildozer\n"
            "          rm -rf bin\n"
            "          mkdir -p bin\n\n"
        )
        wf = wf.replace(marker, insert + marker)
        changes.append("Added a clean Buildozer state before p4a bootstrap.")

spec_path.write_text(spec, encoding="utf-8")
wf_path.write_text(wf, encoding="utf-8")

if changes:
    Path("autofix_result.txt").write_text(
        "AUTO_FIX_APPLIED\n" + "\n".join(f"- {x}" for x in changes) + "\n",
        encoding="utf-8",
    )
    print("AUTO_FIX_APPLIED")
else:
    interesting = []
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"error:|fatal:|exception|traceback|command failed|failed to", line, re.I):
            interesting.extend(lines[max(0, i - 2): min(len(lines), i + 4)])
    seen = set()
    out = []
    for line in interesting:
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if line not in seen:
            seen.add(line)
            out.append(line)
    Path("autofix_issue.md").write_text(
        "# Android build needs analysis\n\n"
        "The automatic repair rules did not recognize this failure.\n\n"
        "Relevant log excerpt:\n\n"
        "<pre>\n" + "\n".join(out[-120:])[:12000] + "\n</pre>\n",
        encoding="utf-8",
    )
    print("NO_KNOWN_FIX")
