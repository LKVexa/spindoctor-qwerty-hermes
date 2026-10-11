#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty for Hermes Agent: host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Run from the repo root:

  python3 tests/hermes_host_check.py                                   # static checks only
  python3 tests/hermes_host_check.py --hermes "$(command -v hermes)"   # + the real Hermes Agent CLI
  python3 tests/hermes_host_check.py --hermes ... --source owner/repo  # install from GitHub instead of a local git copy

Static: plugin.json and mcp.json against the Agent Plugins v1.0.0 rules, the skill's frontmatter, licence headers, the MCP server's
`initialize`, tools/hermes_setup.py, and every CLI command documented in SKILL.md.
--hermes: with a throwaway HERMES_HOME, the real Hermes CLI: `hermes pm install` (the standard install step that provides MCP
support), `plugins validate`, `plugins install` (blocked by the install scan without --force, see README), `--force --no-enable`,
`plugins list/enable/show/doctor`, then one-shot `hermes chat -q ... -Q --yolo` sessions with a `custom` provider pointing at
tests/stub_llm.py, a local scripted stand-in for an OpenAI-compatible endpoint on 127.0.0.1 (placeholder key, no account, nothing
leaves the machine). Covers tool_search/tool_call with the 6 MCP tools, skills_list/skill_view with ${HERMES_SKILL_DIR}, the terminal
fallback, a config.yaml override printed by hermes_setup.py, the shared end-to-end suite through the installed package's server,
disable and remove. Standard library only.
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SK = os.path.join(ROOT, "skills", "spindoctor-qwerty"); MCP = os.path.join(SK, "scripts", "spindoctor_mcp.py")
TOOLS = ["spindoctor_functions", "spindoctor_list_presets", "spindoctor_report", "spindoctor_run_preset", "spindoctor_run_script", "spindoctor_test_theory"]
N = lambda t: "mcp__spindoctor_qwerty__" + t
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"; MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
R = []
OK = lambda s: bool(re.search(r'"ok":\s*true', s or ""))


def unwrap(s):
    """Hermes wraps MCP results as <untrusted_tool_result ...> + {"result": "<tool JSON>"}; return the tool's own JSON text."""
    s = s or ""; i = s.find("{")
    if "<untrusted_tool_result" not in s or i < 0: return s
    try:
        j, _ = json.JSONDecoder().raw_decode(s[i:])
        return j["result"] if isinstance(j, dict) and isinstance(j.get("result"), str) else json.dumps(j)
    except ValueError:
        return s


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


def frontmatter(path):
    t = open(path, encoding="utf-8").read(); end = t.find("\n---\n", 4); fm = {}; cur = None
    for ln in t[4:end].split("\n"):
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", ln)
        if not m: continue
        ind, k, v = m.groups(); v = v.strip().strip('"')
        if ind and cur: fm[cur][k] = v
        elif not v: fm[k] = {}; cur = k
        else: fm[k] = v; cur = None
    return fm, t[end + 5:]


def static():
    p = json.load(open(os.path.join(ROOT, "plugin.json"), encoding="utf-8"))
    T("plugin.json: Agent Plugins v1.0.0 schema id, name pattern, only spec fields, author {name,email}, version 1.1.0, GPL-3.0-or-later",
      p.get("$schema") == PLUGIN_SCHEMA and re.fullmatch(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", p.get("name", ""))
      and set(p) <= {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
      and set(p.get("author", {})) <= {"name", "email", "url"} and p["author"].get("name") == "RUSSELL PHILIP SMITHSON"
      and p.get("version") == "1.1.0" and p.get("license") == "GPL-3.0-or-later" and p.get("name") == "spindoctor-qwerty", p)
    m = json.load(open(os.path.join(ROOT, "mcp.json"), encoding="utf-8"))
    s = m.get("mcpServers", {}).get("spindoctor-qwerty", {})
    T("mcp.json: v1.0.0 schema id, one stdio server, bare `python3` token, args under ${PLUGIN_ROOT}, no reserved/secret env",
      set(m) == {"$schema", "mcpServers"} and m["$schema"] == MCP_SCHEMA and list(m["mcpServers"]) == ["spindoctor-qwerty"]
      and set(s) <= {"type", "command", "args", "env", "cwd"} and s.get("type") == "stdio" and s.get("command") == "python3"
      and s.get("args") == ["${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py"]
      and not ({"PLUGIN_ROOT", "PLUGIN_DATA"} & set(s.get("env", {}))) and not any(re.search(r"key|token|secret", k, re.I) for k in s.get("env", {})), m)
    fm, body = frontmatter(os.path.join(SK, "SKILL.md"))
    T("SKILL.md: Agent Skills frontmatter (name = folder, description <= 1024, compatibility, metadata.version 1.1.0, GPL-3.0-or-later)",
      fm.get("name") == "spindoctor-qwerty" and 0 < len(fm.get("description", "")) <= 1024 and 0 < len(fm.get("compatibility", "")) <= 500
      and fm.get("metadata", {}).get("version") == "1.1.0" and fm.get("license") == "GPL-3.0-or-later", fm)
    T("SKILL.md: guardrail, ${HERMES_SKILL_DIR} fallback, Hermes tool names, no other host's variables, no inline-shell `!` snippets",
      "not a\nquantum computer" in body and "298" in body and "${HERMES_SKILL_DIR}/scripts/spindoctor_cli.py" in body
      and N("spindoctor_functions") in body and "tool_call" in body)
    T("SKILL.md: no Droid/Grok/Claude plugin variables and no `!`cmd`` inline shell (Hermes can expand those)",
      not re.search(r"\$\{(DROID|GROK|CLAUDE)_PLUGIN_ROOT\}|!`", body))
    py = [os.path.join(d, f) for d, _, fs in os.walk(ROOT) if "/." not in d and "__pycache__" not in d for f in fs if f.endswith(".py")]
    bad = [x for x in py if "SPDX-License-Identifier: GPL-3.0-or-later" not in open(x, encoding="utf-8").read(2500)]
    T("every .py file has a GPL-3.0-or-later SPDX header (%d files)" % len(py), not bad, bad[:3])
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "check", "version": "1"}}}) + "\n"
    o = subprocess.run([sys.executable, MCP], input=req.encode(), capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
    T("MCP server answers initialize (serverInfo spindoctor-qwerty, tools capability)", '"serverInfo"' in o and '"tools"' in o, o[:300])
    o = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "hermes_setup.py"), "--plugin-dir", ROOT, "--python", "py"], capture_output=True, text=True).stdout
    T("tools/hermes_setup.py prints an mcp_servers override (py -3 + absolute server path that exists)",
      "mcp_servers:" in o and '"py"' in o and '"-3"' in o and MCP.replace("\\", "/") in o, o)
    cmds = [ln.split("  #")[0].strip() for blk in re.findall(r"```bash\n(.*?)```", body, re.S) for ln in blk.splitlines() if ln.startswith("python3 scripts/")]
    ws = tempfile.mkdtemp(prefix="sdq_cli_"); bad = []
    for c in cmds:
        argv = c.split(" ", 2); rest = re.findall(r'"[^"]*"|\S+', argv[2])
        r = subprocess.run([sys.executable, argv[1], "--workspace", ws] + [x.strip('"') for x in rest], cwd=SK, capture_output=True, timeout=300)
        if r.returncode: bad.append((c, r.stderr[-200:]))
    T("every CLI command in SKILL.md runs as written from the skill folder (%d commands, bundled files only)" % len(cmds), cmds and not bad, bad)
    shutil.rmtree(ws, ignore_errors=True)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Host:
    def __init__(self, hermes):
        self.hermes = hermes; self.tmp = tempfile.mkdtemp(prefix="sdq_hermes_"); self.home = os.path.join(self.tmp, "home")
        self.hh = os.path.join(self.home, ".hermes"); os.makedirs(self.hh)
        self.env = dict(os.environ, HOME=self.home, HERMES_HOME=self.hh, USERPROFILE=self.home, NO_COLOR="1", TERM="dumb")
        for k in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "SPINDOCTOR_WORKSPACE"): self.env.pop(k, None)
        self.port = free_port(); self.n = 0

    def run(self, *args, timeout=600, inp=None):
        p = subprocess.run([self.hermes] + list(args), env=self.env, cwd=self.tmp, capture_output=True, text=True, timeout=timeout, input=inp)
        return p.returncode, p.stdout + p.stderr

    def config(self, extra=""):
        base = open(os.path.join(self.hh, "config.yaml")).read() if os.path.exists(os.path.join(self.hh, "config.yaml")) else ""
        base = re.sub(r"(?ms)^model:\n(?:  .*\n)*", "", base); base = re.sub(r"(?ms)^mcp_servers:\n(?:  .*\n)*", "", base)
        open(os.path.join(self.hh, "config.yaml"), "w").write(base.rstrip("\n") + "\nmodel:\n  default: stub\n  provider: custom\n  base_url: http://127.0.0.1:%d/v1\n  api_key: local-stub\n  context_length: 128000\n" % self.port + extra)

    def chat(self, script, prompt):
        self.n += 1; log = os.path.join(self.tmp, "stub%d.jsonl" % self.n); sp = os.path.join(self.tmp, "script%d.json" % self.n)
        json.dump(script, open(sp, "w"))
        stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_llm.py"), str(self.port), log, sp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.8)
        try:
            code, out = self.run("chat", "-q", prompt, "-Q", "--yolo", timeout=600)
        finally:
            stub.terminate(); stub.wait()
        recs = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
        agent = [r for r in recs if r["tools"]]
        results = [unwrap(x) for x in agent[-1]["tool_results"]] if agent else []
        offered = set(agent[0]["tools"]) if agent else set()
        return code, out, results, offered, recs


def real(hermes, source):
    h = Host(hermes)
    code, out = h.run("--version"); ver = (re.search(r"Hermes Agent v\S+(?: \([^)]*\))?", out) or [out[:60]])[0]
    T("Hermes CLI runs: " + ver, code == 0, out[-300:])
    code, out = h.run("pm", "install", timeout=1800)
    T("`hermes pm install` (standard install step; provides the MCP SDK) completes in the throwaway HERMES_HOME", code == 0, out[-400:])
    code, out = h.run("plugins", "validate", ROOT)
    T("`hermes plugins validate <repo>`: portable manifest parses (Agent Plugins v1), validation passed",
      code == 0 and "Agent Plugins v1" in out and "Validation passed" in out, out[-600:])
    if source:
        src = source
    else:
        rep = os.path.join(h.tmp, "repo"); shutil.copytree(ROOT, rep, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        for c in (["init", "-q", "-b", "main"], ["add", "-A"], ["-c", "user.name=check", "-c", "user.email=check@localhost", "commit", "-qm", "check"]):
            subprocess.run(["git"] + c, cwd=rep, check=True, capture_output=True)
        src = "file://" + rep
    code, out = h.run("plugins", "install", src, "--no-enable")
    highs = re.findall(r"^\s*(HIGH|CRITICAL)\s+(\S+)\s+(\S+)", out, re.M)
    T("install without --force is blocked by the install scan: exactly one HIGH finding (proc_access, the engine reading its own "
      "memory use from /proc/self/status), no CRITICAL", "BLOCKED" in out.upper() and len(set(highs)) == 1 and highs[0][1] == "traversal"
      and "register.py" in highs[0][2] and not os.path.isdir(os.path.join(h.hh, "plugins", "spindoctor-qwerty")), highs or out[-600:])
    code, out = h.run("plugins", "install", src, "--no-enable", "--force")
    inst = os.path.join(h.hh, "plugins", "spindoctor-qwerty")
    T("`plugins install --force --no-enable` installs to $HERMES_HOME/plugins/spindoctor-qwerty, disabled",
      code == 0 and os.path.isfile(os.path.join(inst, "plugin.json")) and "not enabled" in out, out[-500:])
    code, out = h.run("plugins", "list", "--plain", "--no-bundled")
    T("`plugins list`: spindoctor-qwerty 1.1.0 listed as not enabled", re.search(r"not enabled\s+\S+\s+1\.1\.0\s+spindoctor-qwerty", out), out[-300:])
    h.config()
    code, out, res, offered, recs = h.chat([{"tool": "tool_search", "args": {"queries": ["spindoctor"], "limit": 10}}, {"text": "ok"}], "hello")
    T("not enabled: tool_search finds no SpinDoctor tools and the skill is not listed", code == 0 and res and "mcp__spindoctor" not in res[0]
      and not any("agent-plugin-spindoctor" in json.dumps(r.get("system") or "") for r in recs), (res[:1] or [out])[0][:300])
    code, out = h.run("plugins", "enable", "spindoctor-qwerty")
    T("`plugins enable spindoctor-qwerty`", code == 0 and "enabled" in out, out[-300:])
    code, out = h.run("plugins", "show", "spindoctor-qwerty")
    T("`plugins show`: v1.1.0, enabled, portable plugin (no Python)", "v1.1.0" in out and "enabled" in out and "portable" in out, out[-500:])
    code, out = h.run("plugins", "doctor", "spindoctor-qwerty", "--ci")
    T("`plugins doctor --ci` passes", code == 0 and "OK" in out, out[-400:])
    ws = os.path.join(h.home, "spindoctor-workspace")
    script = [{"tool": "tool_search", "args": {"queries": ["spindoctor"], "limit": 10}},
              {"tool": "tool_call", "args": {"name": N("spindoctor_functions"), "arguments": {}}},
              {"tool": "tool_call", "args": {"name": N("spindoctor_run_script"), "arguments": {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z"}}},
              {"tool": "tool_call", "args": {"name": N("spindoctor_run_preset"), "arguments": {"preset_id": "qc-001"}}},
              {"tool": "tool_call", "args": {"name": N("spindoctor_test_theory"), "arguments": {"action": "run", "source": "chat",
               "text": "From our chat: H then CX makes a Bell state, so 00 and 11 each appear about half the time.",
               "excerpts": ["User: does H then CNOT give 50/50 on 00 and 11?", "Assistant: yes, that is a Bell state."],
               "hypothesis": "H(0) then CX(0,1) gives P(00) = P(11) = 0.5", "prediction": "P(11) = 0.5 +/- 0.05 over 4000 shots",
               "script": "q.circuit new bt 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z",
               "checks": [{"kind": "probability", "outcome": "11", "expected": 0.5, "tolerance": 0.05}]}}},
              {"text": "done"}]
    code, out, res, offered, recs = h.chat(script, "show the SpinDoctor functions, run a Bell circuit, preset qc-001 and test the Bell theory we discussed")
    T("enabled: session offers tool_search/tool_call (Hermes defers MCP tools behind them) plus skills and terminal",
      code == 0 and {"tool_search", "tool_call", "skills_list", "skill_view", "terminal"} <= offered, sorted(offered))
    T("tool_search (limit 10) finds all 6 MCP tools as mcp__spindoctor_qwerty__* (the default limit 5 shows 5)", len(res) > 0 and all(N(t) in res[0] for t in TOOLS), res[:1])
    T("tool_call spindoctor_functions: the Markdown function table", len(res) > 1 and "| Function | What it does | Command to type |" in res[1], res[1:2])
    T("tool_call spindoctor_run_script: Bell circuit ok", len(res) > 2 and OK(res[2]) and "bell" in res[2], (res[2:3] or [""])[0][:300])
    T("tool_call spindoctor_run_preset qc-001 ok", len(res) > 3 and OK(res[3]) and "qc-001" in res[3], (res[3:4] or [""])[0][:300])
    pdf = re.findall(r'[^"\s]+theory[^"\s]*\.pdf', res[4]) if len(res) > 4 else []
    T("tool_call spindoctor_test_theory (from the chat): verdict supported, 2 excerpts, PDF report written under ~/spindoctor-workspace",
      len(res) > 4 and '"verdict": "supported"' in res[4] and '"excerptsRecorded": 2' in res[4] and pdf
      and os.path.isfile(pdf[0]) and open(pdf[0], "rb").read(5) == b"%PDF-" and pdf[0].startswith(ws), (res[4:5] or [""])[0][:400])
    script = [{"tool": "skills_list", "args": {}}, {"tool": "skill_view", "args": {"name": "$SKILL"}},
              {"tool": "terminal", "args": {"command": "python3 \"$SKILLDIR/scripts/spindoctor_cli.py\" preset qc-002"}}, {"text": "done"}]
    code, out, res, offered, recs = h.chat(script, "use the spindoctor-qwerty skill to run preset qc-002")
    sk = re.search(r"agent-plugin-spindoctor-qwerty-[0-9a-f]+:spindoctor-qwerty", res[0]) if res else None
    T("skills_list shows the package skill as agent-plugin-spindoctor-qwerty-<hash>:spindoctor-qwerty", sk, (res[:1] or [""])[0][-400:])
    view = json.loads(res[1]) if len(res) > 1 and res[1].startswith("{") else {}
    T("skill_view loads SKILL.md with ${HERMES_SKILL_DIR} filled in with the installed skill folder",
      view.get("success") and "${HERMES_SKILL_DIR}" not in view.get("content", "") and os.path.join(inst, "skills", "spindoctor-qwerty") + "/scripts/spindoctor_cli.py" in view.get("content", ""), str(view)[:400])
    T("terminal fallback: the CLI at the filled-in path runs preset qc-002", len(res) > 2 and '"exit_code": 0' in res[2] and "qc-002" in res[2], (res[2:3] or [""])[0][:300])
    g = subprocess.run(["git", "status", "--porcelain"], cwd=inst, capture_output=True, text=True).stdout.strip()
    T("installed package tree unchanged after the sessions (git status clean; state lives in ~/spindoctor-workspace)", g == "", g)
    ovr = os.path.join(h.tmp, "override-ws")
    o = subprocess.run([sys.executable, os.path.join(inst, "tools", "hermes_setup.py"), "--python", sys.executable], env=h.env, capture_output=True, text=True).stdout
    entry = "\n".join(l for l in o.splitlines() if not l.startswith("#")).replace('env: {PYTHONUTF8: "1"', 'env: {SPINDOCTOR_WORKSPACE: "%s", PYTHONUTF8: "1"' % ovr)
    h.config(entry + "\n")
    code, out, res, offered, recs = h.chat([{"tool": "tool_call", "args": {"name": N("spindoctor_run_preset"), "arguments": {"preset_id": "qc-003"}}}, {"text": "done"}], "run preset qc-003")
    T("config.yaml override printed by tools/hermes_setup.py (absolute Python) replaces the package's server: qc-003 ok, reports in its workspace",
      res and OK(res[0]) and ovr in res[0] and os.path.isdir(os.path.join(ovr, "reports")), (res[:1] or [o])[0][:400])
    h.config()
    e2e = os.path.join(HERE, "e2e_results.json")
    p = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server", sys.executable, os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py"),
                        "--examples", os.path.join(inst, "skills", "spindoctor-qwerty", "examples", "theory"), "--out", e2e], env=h.env, capture_output=True, text=True, timeout=3600, cwd=h.tmp)
    last = [l for l in p.stdout.splitlines() if l.strip()][-1:] or [""]
    T("shared end-to-end suite through the installed package's MCP server: " + last[0][:60], p.returncode == 0, p.stdout[-500:])
    code, out = h.run("plugins", "disable", "spindoctor-qwerty")
    code2, out2, res, offered, recs = h.chat([{"tool": "tool_search", "args": {"queries": ["spindoctor"], "limit": 10}}, {"text": "ok"}], "hello")
    T("`plugins disable`: the next session's tool_search finds no SpinDoctor tools", code == 0 and res and "mcp__spindoctor" not in res[0], (res[:1] or [out2])[0][:300])
    code, out = h.run("plugins", "remove", "spindoctor-qwerty", inp="y\n")
    T("`plugins remove spindoctor-qwerty` deletes the package", not os.path.exists(inst), out[-300:])
    return ver


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    static(); ver = None
    if opt.get("--hermes"): ver = real(opt["--hermes"], opt.get("--source"))
    out = opt.get("--out", os.path.join(HERE, "host_check.json"))
    json.dump({"python": sys.version.split()[0], "hermes": ver, "checks": R}, open(out, "w"), indent=1)
    n = sum(r["pass"] for r in R); print("%d/%d passed" % (n, len(R))); return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())
