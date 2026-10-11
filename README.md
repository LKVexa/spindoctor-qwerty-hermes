# SpinDoctor Qwerty for Hermes Agent

A portable **Agent Plugins v1** package for [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research) that runs
the **SpinDoctor 3.1.2 quantum-circuit simulator** on your computer: `q.*` circuit scripts (1-298 logical qubits), the 241 built-in
presets, folders of command files (`q.folder`), and theory tests from a file, pasted text or the chat itself, each with TXT, PDF,
JSON and CSV reports. It adds a local MCP server (6 tools) and a skill.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - tested with Hermes Agent 2026.9.24 (git 79b45d1) - Python 3.8+, standard
library only - no network, no account and no keys for the plugin itself.

## Install

```bash
hermes plugins install LKVexa/spindoctor-qwerty-hermes --no-enable --force
hermes plugins enable spindoctor-qwerty
```

Start a new session afterwards. Check with `hermes plugins list` / `hermes plugins show spindoctor-qwerty`; update with
`hermes plugins update spindoctor-qwerty`; turn off with `hermes plugins disable spindoctor-qwerty`; remove with
`hermes plugins remove spindoctor-qwerty`. Portable packages always install disabled until you enable them.

**Why `--force`?** Hermes scans packages from non-catalog sources before installing. It rates this one *caution* and blocks it
until you pass `--force` (you can run the same scan first with `hermes plugins validate <clone>`). The findings, all benign:

| Severity | Finding | What it is |
|---|---|---|
| HIGH | `proc_access` - `skills/spindoctor-qwerty/spindoctor/register.py` | The engine reads its own memory use from `/proc/self/status` (Linux) for the memory-budget report; on Windows it asks the OS instead. (It also reads total RAM from `/proc/meminfo`, which the scanner does not flag.) Nothing is written. |
| MEDIUM | `obfuscation` - `netfmt.py` (1), `reports.py` (3) | Plain escape sequences: JSON-safe `\u003c`-style escaping, the PDF header bytes, and a table that turns typographic dashes and quotes into ASCII for PDF output. |
| MEDIUM | `execution` - `tests/*.py` | The test scripts start the MCP server, Hermes, git and `pdftotext` to check the package. Tests never run inside Hermes. |
| MEDIUM / LOW | `execution`, `traversal`, `persistence` - `README.md`, `CHANGELOG.md`, `tests/hermes_host_check.py` | The documentation and test text that describe these findings and the config.yaml step. |

Only the HIGH finding decides the verdict (medium findings alone count as safe). Review the code before you use `--force`; that is
what the scan asks for.

Requirements: Python 3.8 or newer as `python3`, and a standard Hermes install (the setup script runs `hermes pm install`, which
provides MCP support; a bare `pip install` of Hermes without the `mcp` extra loads the skill but no MCP tools).
**Windows / a different Python:** run `py tools/hermes_setup.py` (or `python ...`) in a clone or in the installed package
(`~/.hermes/plugins/spindoctor-qwerty`) and paste the `mcp_servers` entry it prints into `~/.hermes/config.yaml` (merge it if that
key already exists). A config.yaml server with the same name replaces the package's, so nothing in the package is edited.

## What's in the repo

| Path | What it is |
|---|---|
| `plugin.json` | Agent Plugins v1.0.0 manifest (name, version, license, author) |
| `mcp.json` | MCP server `spindoctor-qwerty`: `python3 ${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py` |
| `skills/spindoctor-qwerty/` | Skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI and MCP server (`scripts/`), examples, LICENSE |
| `tools/hermes_setup.py` | Prints a config.yaml override for Windows or another Python |
| `FUNCTIONS.md` | The full function table with a runnable example for every command |
| `tests/` | Host check, shared end-to-end suite, local OpenAI-compatible stand-in, reference outputs |

The package has no native Hermes Python plugin (`plugin.yaml` + `register(ctx)`), no hooks and no credentials: Hermes reads the
skill and starts the MCP server, nothing else.

## Using it

- Ask in plain language: "show the SpinDoctor functions", "run a 3-qubit GHZ circuit", "test the theory we discussed".
- Hermes registers the tools as `mcp__spindoctor_qwerty__spindoctor_functions`, `..._run_script`, `..._run_preset`,
  `..._list_presets`, `..._report` and `..._test_theory`. With many tools installed Hermes defers MCP tools behind `tool_search` /
  `tool_call`; a search for "spindoctor" lists them (5 matches per query by default, so a `limit` of 6 or more shows all of them).
- The skill shows up in `skills_list` as `agent-plugin-spindoctor-qwerty-<hash>:spindoctor-qwerty`. When the tools are unavailable
  it tells Hermes to run the CLI with the terminal tool: `python3 "${HERMES_SKILL_DIR}/scripts/spindoctor_cli.py" functions`
  (Hermes fills in the installed skill folder).
- Pass absolute paths. Reports and state go to `~/spindoctor-workspace` unless a tool call passes `workspace`; nothing goes into the
  installed package folder.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | Ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | Ask: "run preset qc-067 with shots=64" |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | Ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In Hermes, give the file's absolute path on your computer (or paste the text).
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command |
|---|---|
| Static checks | `python3 tests/hermes_host_check.py` |
| Real Hermes Agent | `python3 tests/hermes_host_check.py --hermes "$(command -v hermes)"` (add `--source LKVexa/spindoctor-qwerty-hermes` to install from GitHub) |
| End-to-end suite only | `python3 tests/e2e_mcp.py --server python3 skills/spindoctor-qwerty/scripts/spindoctor_mcp.py --examples skills/spindoctor-qwerty/examples/theory` |

**Real host, scripted model.** The host check uses the real Hermes Agent CLI (source build 2026.9.24, git 79b45d1) with a throwaway
`HERMES_HOME` and no Nous Portal or provider account: `hermes pm install`, `plugins validate`, the scan-blocked install and the
`--force --no-enable` install, `plugins list/enable/show/doctor`, then one-shot `hermes chat -q ... -Q --yolo` sessions with a
`custom` provider pointing at `tests/stub_llm.py`, a local scripted stand-in for an OpenAI-compatible endpoint on 127.0.0.1
(placeholder key). Through Hermes' own MCP client and tool bridge it searches and calls the 6 tools (function table, a Bell circuit,
qc-001, a theory from the chat: verdict *supported*, PDF written), loads the skill with `${HERMES_SKILL_DIR}` filled in, runs the CLI
through the terminal tool, checks the config.yaml override from `tools/hermes_setup.py`, runs the shared end-to-end suite through the
installed package's server, then disables and removes the package. Not tested: a real model choosing the tools, the interactive TUI
and its approval prompts, the messaging gateway, Windows, macOS. Results: [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). Hermes Agent is a Nous Research project; this package is not
affiliated with Nous Research.
