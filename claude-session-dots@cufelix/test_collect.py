#!/usr/bin/env python3
"""Self-check for collect.py: python3 claude-session-dots@cufelix/test_collect.py"""
import json
import os
import subprocess
import tempfile

import collect


def write_transcript(path, entries):
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e, separators=(",", ":")) + "\n")  # Compact, like real transcripts.


def assistant(text=None, usage=None, branch="main"):
    content = [{"type": "text", "text": text}] if text else [{"type": "tool_use", "name": "Bash"}]
    message = {"role": "assistant", "content": content, "model": "claude-opus-5-5"}
    if usage:
        message["usage"] = usage
    return {"type": "assistant", "message": message, "gitBranch": branch}


USER = {"type": "user", "message": {"role": "user", "content": "hi"}}
USAGE = {"input_tokens": 1, "cache_read_input_tokens": 199_000, "cache_creation_input_tokens": 999}

# Asking is judged on the last line of the final assistant text only.
assert collect.asks_question("Done.\n\nShould I push this?")
assert collect.asks_question("Mám to pushnout?**")
assert collect.asks_question("Need the full version? Say so.")
assert not collect.asks_question("Is this right? Yes.\n\nAll done.")
assert not collect.asks_question("See https://x.dev/a?b=1")
assert not collect.asks_question(None)

# Attention: an explicit wait always counts, a question only once the turn ended.
assert collect.needs_attention("waiting", None)
assert collect.needs_attention("idle", "Push it?")
assert not collect.needs_attention("busy", "Push it?")
assert not collect.needs_attention("shell", "Push it?")
assert not collect.needs_attention("idle", "All done.")

# Labels are initials, unless they would collide; then the name's suffix tells them apart.
assert collect.abbreviate(["poker-app-c3", "espoo-ed"]) == ["PA", "ES"]
assert collect.abbreviate(["names-e3", "names-09"]) == ["E3", "09"]
assert collect.abbreviate(["x"]) == ["X"]
assert collect.abbreviate(["review-some-code-update"]) == ["RS"]

assert collect.human_duration(30_000) == "<1m"
assert collect.human_duration(3 * 60_000) == "3m"
assert collect.human_duration(125 * 60_000) == "2h 05m"

with tempfile.TemporaryDirectory() as home:
    os.makedirs(f"{home}/sessions")
    os.makedirs(f"{home}/projects/-any")

    # A later user message means the question was already answered.
    path = f"{home}/projects/-any/t.jsonl"
    write_transcript(path, [assistant("Push it?", USAGE), USER])
    assert collect.read_last_turn(path)["text"] is None
    # Usage comes from the newest entry that has it, text from the final one.
    write_transcript(path, [assistant("old", USAGE), assistant("Push it?")])
    turn = collect.read_last_turn(path)
    assert turn["text"] == "Push it?" and turn["context"] == 200_000 and turn["branch"] == "main"
    # Subagent entries say nothing about the main thread.
    write_transcript(path, [assistant("Main."), {**assistant("Side?"), "isSidechain": True}])
    assert collect.read_last_turn(path)["text"] == "Main."
    # Broken and missing transcripts degrade to no data.
    with open(path, "w") as f:
        f.write('{"type":"assistant", broken\n')
    assert collect.read_last_turn(path)["context"] is None
    assert collect.read_last_turn(f"{home}/missing.jsonl")["context"] is None

    # End to end: live sessions are listed oldest first, dead or hidden ones are not.
    child = subprocess.Popen(["sleep", "30"])
    try:
        def session(pid, name, started, **extra):
            data = {
                "pid": pid, "sessionId": name, "cwd": "/w/" + name, "name": name, "kind": "interactive",
                "status": "busy", "startedAt": started, "statusUpdatedAt": 1000,
                "procStart": collect.proc_start(pid), **extra,
            }
            with open(f"{home}/sessions/{pid}{name}.json", "w") as f:
                json.dump(data, f)

        session(child.pid, "blocked-one", 2, status="waiting", waitingFor="permission")
        session(child.pid, "asking-two", 1, status="idle")
        session(child.pid, "reused-pid", 3, procStart="1")
        session(child.pid, "spare", 4, spare=True)
        session(child.pid, "daemon", 5, kind="daemon")
        session(2**22 + 1, "dead", 6)
        with open(f"{home}/sessions/garbage.json", "w") as f:
            f.write("{nope")
        write_transcript(f"{home}/projects/-any/asking-two.jsonl", [assistant("Ship it?", USAGE)])

        rows = collect.collect(home, now_ms=61_000)
        assert [r["name"] for r in rows] == ["asking-two", "blocked-one"], rows
        asking, blocked = rows
        assert asking["attention"] and blocked["attention"]
        assert asking["contextFraction"] == 0.2
        assert "Asked you a question" in asking["tooltip"] and "Ship it?" in asking["tooltip"]
        assert "permission" in blocked["tooltip"] and blocked["contextFraction"] is None
        assert child.pid in blocked["pids"] and os.getpid() in blocked["pids"]
    finally:
        child.kill()
        child.wait()

print("ok")
