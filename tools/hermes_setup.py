#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty for Hermes Agent: print a config.yaml override for the MCP server
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Print an `mcp_servers` entry for ~/.hermes/config.yaml that starts the SpinDoctor MCP server with a Python you choose.

The package's mcp.json starts the server as `python3`. Windows (python.org installer: `py` / `python`) and some other systems
have no `python3`. Hermes lets a config.yaml server with the same name replace a package's entry, so instead of editing the
installed package (which `hermes plugins update` would overwrite) run this once and paste what it prints into config.yaml:

  python tools/hermes_setup.py                      # uses the Python running this script, by absolute path
  python tools/hermes_setup.py --python py          # or any command: py | python | python3 | "C:/Path To/python.exe"
  python tools/hermes_setup.py --plugin-dir DIR     # default: $HERMES_HOME/plugins/spindoctor-qwerty, else this clone

Then start a new Hermes session. It prints only; it changes no files. Standard library only.
"""
import json, os, sys


def main():
    a = sys.argv[1:]
    if "-h" in a or "--help" in a:
        print(__doc__); return 0
    opt = dict(zip(a[::2], a[1::2]))
    py = opt.get("--python") or sys.executable
    home = os.environ.get("HERMES_HOME") or os.path.join(os.path.expanduser("~"), ".hermes")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    installed = os.path.join(home, "plugins", "spindoctor-qwerty")
    root = opt.get("--plugin-dir") or (installed if os.path.isfile(os.path.join(installed, "plugin.json")) else here)
    server = os.path.join(os.path.abspath(root), "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py").replace("\\", "/")
    if not os.path.isfile(server):
        print("not found: %s (pass --plugin-dir)" % server); return 1
    args = ["-3", server] if os.path.basename(py).lower() in ("py", "py.exe") else [server]
    q = lambda s: json.dumps(s.replace("\\", "/"))
    print("# Add to %s (replaces the package's spindoctor-qwerty server; same tools):" % os.path.join(home, "config.yaml").replace("\\", "/"))
    print("mcp_servers:")
    print("  spindoctor-qwerty:")
    print("    command: %s" % q(py))
    print("    args: [%s]" % ", ".join(q(x) for x in args))
    print("    env: {PYTHONUTF8: \"1\", PYTHONDONTWRITEBYTECODE: \"1\"}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
