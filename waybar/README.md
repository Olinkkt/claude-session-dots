# Waybar / Hyprland frontend

One round disc per running Claude Code session, like the Cinnamon applet: colored by state,
initials inside, white ring for how full the context is. Red means Claude needs you and blinks.
It reuses `../claude-session-dots@cufelix/collect.py` unchanged.

## Install

1. Needs Waybar, Hyprland, Python 3 and `python-cairo` (`sudo pacman -S python-cairo`).
2. Clone it:
   ```bash
   git clone https://github.com/Olinkkt/claude-session-dots.git ~/.local/share/claude-session-dots
   ```
3. Add the six modules from `config.jsonc` to `~/.config/waybar/config`, and list `image#claude-dots-1` to `-6` in one of the `modules-*` arrays.
4. Append `style.css` to `~/.config/waybar/style.css`.
5. Reload: `pkill -SIGUSR2 waybar`

## Use

- **Hover a disc:** name, state and how long, context size, model, folder and branch.
- **Left click a disc:** focuses that session's terminal window.
- **Test without Waybar:** `./csd-waybar image 1` draws session 1 and prints its path and tooltip.
- **Tag mode instead of discs:** `csd-waybar status` prints one colored-text label for a `custom` module. It needs no python-cairo.

## Limits

- Each disc is a separate Waybar module, so the bar supports 6 sessions. Add more modules for more.
- Focus raises the terminal window, not the tab. Sessions inside tmux have no window to raise.
