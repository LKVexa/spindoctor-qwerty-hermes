# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics, CSV report copies and measurement-CSV fitting equations. All 241
  presets replayed. Tools `spindoctor_functions` (function table, marked read-only) and `spindoctor_test_theory` (theory testing
  from a file, pasted text or the chat, with TXT+JSON+PDF theory reports). 1.0 described SpinDoctor 3.0.3 and a 29-qubit cap.
- **Installable with `hermes plugins install`.** The repo root is now the Agent Plugins v1 package (`plugin.json`, `mcp.json`,
  `skills/`), so `hermes plugins install LKVexa/spindoctor-qwerty-hermes` works. 1.0 kept the package in a `spindoctor-qwerty/`
  subfolder and only said "copy this folder into the agent's plugin directory".
- **Checked against the real Hermes Agent.** plugin.json and mcp.json pass Hermes' portable-package loader and `plugins validate` /
  `plugins doctor`; the MCP server registers its 6 tools as `mcp__spindoctor_qwerty__*`; the skill loads as
  `agent-plugin-spindoctor-qwerty-<hash>:spindoctor-qwerty`. SKILL.md now names those tools, explains Hermes' `tool_search` /
  `tool_call`, and uses `${HERMES_SKILL_DIR}` (filled in by Hermes) for the terminal fallback instead of a relative path.
- **Install scan documented.** Hermes scans community packages on install. The engine's memory check reads `/proc/self/status`
  (its own memory use, Linux only), which the scanner rates HIGH, so the install is blocked until you pass `--force`. The README
  lists every finding and why it is benign. The engine is unchanged (same code as the other SpinDoctor Qwerty repos).
- **Reports in one place.** 1.0 pointed the server's workspace at `${PLUGIN_DATA}/workspace` while the CLI fallback used
  `~/spindoctor-workspace`, so reports from one route were invisible to the other. Both now use `~/spindoctor-workspace` (or a
  `workspace` argument / `--workspace`).
- **Windows / other Pythons.** `tools/hermes_setup.py` prints an `mcp_servers` entry for `~/.hermes/config.yaml` that replaces the
  package's `python3` command (Hermes lets config.yaml override a package server of the same name), so nothing in the installed
  package is edited and `hermes plugins update` keeps working.
- SKILL.md examples use bundled files only (`examples/theory/xbasis.q`, new `examples/bell_theory_args.json`) and every one runs as
  written; frontmatter adds `compatibility` and `metadata` (version, engine); the skill folder carries its own LICENSE.
- Tests: `tests/hermes_host_check.py` (static checks and the real Hermes CLI with a local stand-in model) and `tests/stub_llm.py`.
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/` folder in the portable Agent Plugins v1 layout (plugin.json, mcp.json, skill), engine
  described as SpinDoctor 3.0.3.
