# Claude Session Dots

A Cinnamon panel applet with one dot for every running [Claude Code](https://claude.com/claude-code) session. A dot turns red and blinks when Claude needs you.

| Dot | Meaning |
|---|---|
| 🔴 Red, blinking | Claude is waiting for you (a permission prompt, a question or a dialog), or it ended its turn with a question |
| 🟢 Green | Claude is working |
| ⚪ Grey | Idle, or you are in the session's shell |

- **Letters:** the session's initials, such as `PA` for `poker-app-c3`.
- **White ring:** how full the session's context is. It assumes a 1M context window.
- **Hover:** session name, state and for how long, context size, model, folder and git branch. On a red dot, the end of Claude's last message too.
- **Left click:** raises the session's terminal window.

## Install

You need Cinnamon, Python 3 and Claude Code on the same machine.

```bash
git clone https://github.com/cufelix/claude-session-dots.git
ln -s "$PWD/claude-session-dots/claude-session-dots@cufelix" ~/.local/share/cinnamon/applets/
```

Then right-click the panel, choose **Applets**, and add **Claude Session Dots**.

## How it works

Every 2 seconds the applet runs `collect.py`, which reads two things:

- `~/.claude/sessions/*.json` for each session's state, skipping processes that have exited
- the last 4 MB of each session's transcript for context size, model and last message

It only reads local files and sends nothing over the network. It respects `CLAUDE_CONFIG_DIR` if that is set in the environment Cinnamon runs in.

These files are Claude Code's internal format, not a public API, so a Claude Code update could break the applet.

## Limitations

- A question is detected by a `?` on the last line of Claude's final message. Questions followed by more lines are missed, and a rhetorical `?` shows red until you reply.
- A clicked dot raises the terminal window but can't switch to the right tab. If one terminal process owns several windows, the first one is raised. Sessions inside tmux have no window to raise.

## Test

```bash
python3 claude-session-dots@cufelix/test_collect.py
```

## License

MIT
