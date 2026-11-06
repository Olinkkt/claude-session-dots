#!/usr/bin/env python3
"""Print every live Claude Code session as JSON for the panel applet.

Reads Claude Code's own bookkeeping: ~/.claude/sessions/<pid>.json for state and
the tail of the session transcript for context size and the last message.
"""
import glob
import json
import os
import re
import time

HOME = os.path.expanduser("~")
# ponytail: assumes the 1M context window, the ring just reads low on 200k models.
CONTEXT_WINDOW = 1_000_000
# Must reach the last usage entry; attachments can push it over 1 MB back.
TAIL_BYTES = 4 << 20
SNIPPET_CHARS = 200
QUESTION = re.compile(r"\?(\s|$)")
HASH_SUFFIX = re.compile(r"[0-9a-f]{2}")


def proc_start(pid):
    """Kernel start time of pid, or None if it is gone. Field 22 of /proc/pid/stat."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            # The command name may contain spaces, so split after its closing paren.
            return f.read().rpartition(")")[2].split()[19]
    except (OSError, IndexError):
        return None


def parent_pid(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return int(f.read().rpartition(")")[2].split()[1])
    except (OSError, IndexError, ValueError):
        return 0


def ancestors(pid):
    """pid and its parents, so the applet can find the terminal window that hosts it."""
    chain = []
    while pid > 1:
        chain.append(pid)
        pid = parent_pid(pid)
    return chain


def is_alive(session):
    """A session file can outlive its process, and the pid can get reused."""
    started = proc_start(session.get("pid"))
    return started is not None and session.get("procStart") in (None, started)


def asks_question(text):
    # ponytail: Claude asking in plain prose leaves status "idle", so this reads the
    # last line for a "?". Misses questions followed by more lines.
    if not text:
        return False
    return bool(QUESTION.search(text.strip().splitlines()[-1].rstrip("*_` ")))


def needs_attention(status, last_text):
    return status == "waiting" or (status == "idle" and asks_question(last_text))


def abbreviate(names):
    def initials(name):
        words = [w for w in re.split(r"[-_. ]+", name) if w]
        # Drop the hash suffix Claude adds to derived names ("poker-app-c3").
        if len(words) > 1 and HASH_SUFFIX.fullmatch(words[-1]):
            words = words[:-1]
        return ("".join(w[0] for w in words) if len(words) > 1 else words[0])[:2].upper() if words else "?"

    labels = [initials(n) for n in names]
    return [n[-2:].upper() if labels.count(label) > 1 else label for n, label in zip(names, labels)]


def human_duration(ms):
    minutes = int(ms // 60_000)
    if minutes < 1:
        return "<1m"
    return f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"


def read_last_turn(path):
    """Newest context size and model, plus the final assistant text if nothing followed it."""
    turn = {"context": None, "model": None, "branch": None, "text": None}
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - TAIL_BYTES))
            lines = f.read().split(b"\n")
    except OSError:
        return turn

    final_seen = False
    for line in reversed(lines):
        if b'"type":"assistant"' not in line and (final_seen or b'"type":"user"' not in line):
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # The first line of the tail is usually cut in half.
        if entry.get("isSidechain") or entry.get("type") not in ("user", "assistant"):
            continue
        if not final_seen:
            final_seen = True
            if entry["type"] == "assistant":
                blocks = entry.get("message", {}).get("content")
                texts = [b.get("text", "") for b in blocks if b.get("type") == "text"] if isinstance(blocks, list) else []
                turn["text"] = "\n".join(texts) or None
        usage = entry.get("message", {}).get("usage")
        if entry["type"] == "assistant" and usage:
            turn["context"] = sum(usage.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            turn["model"] = entry["message"].get("model")
            turn["branch"] = entry.get("gitBranch")
            break
    return turn


def describe_state(session, attention):
    status = session.get("status") or "unknown"
    if status == "waiting":
        return f"NEEDS YOU: {session.get('waitingFor') or 'waiting'}"
    if attention:
        return "Asked you a question"
    return {"busy": "Working", "idle": "Idle", "shell": "In shell"}.get(status, status)


def build_tooltip(session, turn, attention, now_ms):
    state = describe_state(session, attention)
    since = session.get("statusUpdatedAt")
    facts = [f"{state} for {human_duration(now_ms - since)}" if since else state]
    if turn["context"] is not None:
        facts.append(f"{round(turn['context'] / 1000)}k context")
    if turn["model"]:
        facts.append(turn["model"].removeprefix("claude-"))
    cwd = session.get("cwd") or "?"
    place = "~" + cwd[len(HOME):] if cwd.startswith(HOME) else cwd
    lines = [session.get("name") or place, " · ".join(facts), f"{place} ({turn['branch']})" if turn["branch"] else place]
    if attention and turn["text"]:
        lines.append(" ".join(turn["text"].split())[-SNIPPET_CHARS:])
    return "\n".join(lines)


def load_sessions(claude_dir):
    sessions = []
    for path in glob.glob(f"{claude_dir}/sessions/*.json"):
        try:
            with open(path) as f:
                session = json.load(f)
        except (OSError, ValueError):
            continue
        # Same filter Claude Code uses for its own session list.
        if session.get("kind") in ("interactive", "bg") and not session.get("spare") and is_alive(session):
            sessions.append(session)
    return sorted(sessions, key=lambda s: s.get("startedAt") or 0)  # Oldest first, so dots stay put.


def transcript_path(claude_dir, session):
    session_id = str(session.get("sessionId"))
    expected = f"{claude_dir}/projects/{re.sub(r'[^a-zA-Z0-9]', '-', session.get('cwd') or '')}/{session_id}.jsonl"
    if os.path.exists(expected):
        return expected
    # The session may have moved since it started, so its folder may not match cwd.
    found = glob.glob(f"{claude_dir}/projects/*/{glob.escape(session_id)}.jsonl")
    return found[0] if found else ""


def collect(claude_dir, now_ms):
    sessions = load_sessions(claude_dir)
    labels = abbreviate([s.get("name") or os.path.basename(s.get("cwd") or "?") for s in sessions])
    rows = []
    for session, label in zip(sessions, labels):
        turn = read_last_turn(transcript_path(claude_dir, session))
        attention = needs_attention(session.get("status"), turn["text"])
        rows.append({
            "name": session.get("name"),
            "label": label,
            "status": session.get("status"),
            "attention": attention,
            "contextFraction": None if turn["context"] is None else min(1, turn["context"] / CONTEXT_WINDOW),
            "tooltip": build_tooltip(session, turn, attention, now_ms),
            "pids": ancestors(session["pid"]),
        })
    return rows


if __name__ == "__main__":
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR") or f"{HOME}/.claude"
    print(json.dumps(collect(claude_dir, int(time.time() * 1000))))
