# E2E results - spindoctor-qwerty-hermes 1.1.0

Host: **real Hermes Agent vgit.79b45d1 (2026.9.24)** (source build of NousResearch/hermes-agent, Python 3.14 via uv, plus `hermes pm install`) with a throwaway
HERMES_HOME and no Nous Portal or provider account. Model turns come from `tests/stub_llm.py`, a local scripted stand-in for
an OpenAI-compatible endpoint on 127.0.0.1 (a `custom` provider with a placeholder key), so tool calls are scripted; everything between
the model and the engine (install scan, portable-package loader, enable/disable, `${PLUGIN_ROOT}` expansion, MCP startup,
`tool_search`/`tool_call`, `skills_list`/`skill_view` with `${HERMES_SKILL_DIR}`, the terminal tool, config.yaml override, remove) is
the real Hermes. Python 3.13.5 for the checks.

Not tested: a real model choosing the tools by itself, the interactive TUI and its approval prompts, the messaging gateway, Windows,
macOS.

## Host check: 33/33

| Result | Check |
|---|---|
| PASS | plugin.json: Agent Plugins v1.0.0 schema id, name pattern, only spec fields, author {name,email}, version 1.1.0, GPL-3.0-or-later |
| PASS | mcp.json: v1.0.0 schema id, one stdio server, bare `python3` token, args under ${PLUGIN_ROOT}, no reserved/secret env |
| PASS | SKILL.md: Agent Skills frontmatter (name = folder, description <= 1024, compatibility, metadata.version 1.1.0, GPL-3.0-or-later) |
| PASS | SKILL.md: guardrail, ${HERMES_SKILL_DIR} fallback, Hermes tool names, no other host's variables, no inline-shell `!` snippets |
| PASS | SKILL.md: no Droid/Grok/Claude plugin variables and no `!`cmd`` inline shell (Hermes can expand those) |
| PASS | every .py file has a GPL-3.0-or-later SPDX header (27 files) |
| PASS | MCP server answers initialize (serverInfo spindoctor-qwerty, tools capability) |
| PASS | tools/hermes_setup.py prints an mcp_servers override (py -3 + absolute server path that exists) |
| PASS | every CLI command in SKILL.md runs as written from the skill folder (6 commands, bundled files only) |
| PASS | Hermes CLI runs: Hermes Agent vgit.79b45d1 (2026.9.24) |
| PASS | `hermes pm install` (standard install step; provides the MCP SDK) completes in the throwaway HERMES_HOME |
| PASS | `hermes plugins validate <repo>`: portable manifest parses (Agent Plugins v1), validation passed |
| PASS | install without --force is blocked by the install scan: exactly one HIGH finding (proc_access, the engine reading its own memory use from /proc/self/status), no CRITICAL |
| PASS | `plugins install --force --no-enable` installs to $HERMES_HOME/plugins/spindoctor-qwerty, disabled |
| PASS | `plugins list`: spindoctor-qwerty 1.1.0 listed as not enabled |
| PASS | not enabled: tool_search finds no SpinDoctor tools and the skill is not listed |
| PASS | `plugins enable spindoctor-qwerty` |
| PASS | `plugins show`: v1.1.0, enabled, portable plugin (no Python) |
| PASS | `plugins doctor --ci` passes |
| PASS | enabled: session offers tool_search/tool_call (Hermes defers MCP tools behind them) plus skills and terminal |
| PASS | tool_search (limit 10) finds all 6 MCP tools as mcp__spindoctor_qwerty__* (the default limit 5 shows 5) |
| PASS | tool_call spindoctor_functions: the Markdown function table |
| PASS | tool_call spindoctor_run_script: Bell circuit ok |
| PASS | tool_call spindoctor_run_preset qc-001 ok |
| PASS | tool_call spindoctor_test_theory (from the chat): verdict supported, 2 excerpts, PDF report written under ~/spindoctor-workspace |
| PASS | skills_list shows the package skill as agent-plugin-spindoctor-qwerty-<hash>:spindoctor-qwerty |
| PASS | skill_view loads SKILL.md with ${HERMES_SKILL_DIR} filled in with the installed skill folder |
| PASS | terminal fallback: the CLI at the filled-in path runs preset qc-002 |
| PASS | installed package tree unchanged after the sessions (git status clean; state lives in ~/spindoctor-workspace) |
| PASS | config.yaml override printed by tools/hermes_setup.py (absolute Python) replaces the package's server: qc-003 ok, reports in its workspace |
| PASS | shared end-to-end suite through the installed package's MCP server: SUMMARY 12/12 passed in 12.7s |
| PASS | `plugins disable`: the next session's tool_search finds no SpinDoctor tools |
| PASS | `plugins remove spindoctor-qwerty` deletes the package |

## Shared end-to-end suite through the installed package: 12/12

Started with the installed package's MCP server: `python3 $HERMES_HOME/plugins/spindoctor-qwerty/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py`.

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Clean-room copy of the staged repo, real Hermes CLI: 33/33 host checks, e2e 12/12 (2026-10-11 03:40 PT)
