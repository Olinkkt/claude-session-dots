# Waybar / Hyprland frontend

One colored dot and the session's initials for every running Claude Code session,
in a single Waybar module. Red means Claude needs you. Same data as the Cinnamon applet,
since it reuses `../claude-session-dots@cufelix/collect.py` unchanged.

## Install

1. Needs Waybar, Hyprland, Python 3.
2. Clone it:
   ```bash
   git clone https://github.com/Olinkkt/claude-session-dots.git ~/.local/share/claude-session-dots
   ```
3. Add the module from `config.jsonc` to `~/.config/waybar/config`, and put `"custom/claude-dots"` in one of the `modules-*` lists.
4. Append `style.css` to `~/.config/waybar/style.css`.
5. Reload: `pkill -SIGUSR2 waybar`

## Use

- **Hover:** name, state and how long, context size, model, folder and branch for every session.
- **Left click:** focuses the terminal of the session that needs you (the oldest session if none does).
- **Test without Waybar:** `./csd-waybar status`

## Limits

- Waybar draws one text label per module, so there is no per-dot click, no context ring, and the red blink pulses the whole module.
- Focus raises the terminal window, not the tab. Sessions inside tmux have no window to raise.
