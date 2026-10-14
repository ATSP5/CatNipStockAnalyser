"""Run a CatNip graph from a terminal, without opening CatNip.

CatNip compiles a program from the main block plus every block that reaches it:
each block is written out as `<Name>.py`, the folder holding them goes on
`sys.path`, and the main block is executed with `__name__ == "__main__"`. Blocks
reach each other by ordinary Python import, which is why every block that uses
another one imports it at the top.

This script does the same thing straight from the .catnip file. Because it
re-derives the modules from the project every time, it cannot drift out of step
with what the canvas shows, and what it runs is what CatNip runs.

It lives in tools/ rather than beside the project on purpose: CatNip's Generate
Source clears stray .py files out of the project folder, and would take this
script with them.

The modules it builds go into the project folder itself, which is where CatNip
generates them too, and -- importantly -- what a Docker run copies into /app.
Writing them anywhere else leaves two copies that can disagree, and a container
that cannot import them.

    python tools/run.py 0000006865 2023 2024
"""

import glob
import io
import json
import os
import runpy
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)


def find_project(root=ROOT):
    """The single .catnip file beside this tools folder."""
    candidates = sorted(glob.glob(os.path.join(root, "*.catnip")))
    if not candidates:
        raise RuntimeError("no .catnip project found in %s" % root)
    if len(candidates) > 1:
        names = ", ".join(os.path.basename(c) for c in candidates)
        raise RuntimeError("more than one .catnip project in %s: %s"
                           % (root, names))
    return candidates[0]


def load_project(path=None):
    with io.open(path or find_project(), encoding="utf-8") as handle:
        return json.load(handle)


def block_table(project):
    """id -> the bits of a node this runner cares about."""
    blocks = {}
    for node in project.get("nodes", []):
        data = node.get("nodeData", {})
        settings = data.get("settings", {})
        blocks[data["id"]] = {
            "id": data["id"],
            "title": data.get("title", "block%s" % data["id"]),
            "name": settings.get("description") or data.get("title"),
            "code": data.get("codeText", ""),
            "is_main": bool(settings.get("isMain")),
        }
    return blocks


def write_sources(blocks, out_dir=ROOT):
    """Write one .py per block, the way Generate Source does.

    Non-main blocks are named after the class they hold, so `from Numbers
    import Numbers` resolves. The main block becomes main_1.py, matching what
    CatNip executes. These are the same filenames CatNip writes, so there is
    one set of generated sources rather than two.
    """
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    main_path = None
    for block in sorted(blocks.values(), key=lambda b: b["id"]):
        filename = "main_1.py" if block["is_main"] else "%s.py" % block["name"]
        path = os.path.join(out_dir, filename)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(block["code"])
        if block["is_main"]:
            main_path = path

    if main_path is None:
        raise RuntimeError("no block in the project is marked as main")
    return main_path


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    # Output lands beside the project, not beside the shell's current directory.
    os.chdir(ROOT)

    main_path = write_sources(block_table(load_project()))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    # The main block reads its configuration from sys.argv, exactly as it does
    # when CatNip passes the Run Engine's script arguments through.
    sys.argv = [main_path] + list(argv)

    try:
        runpy.run_path(main_path, run_name="__main__")
    except ValueError as problem:
        # A bad argument is user error, not a crash worth a traceback.
        sys.stderr.write("error: %s\n" % problem)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
