const Applet = imports.ui.applet;
const Main = imports.ui.main;
const Tooltips = imports.ui.tooltips;
const St = imports.gi.St;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Clutter = imports.gi.Clutter;
const Cairo = imports.cairo;

const POLL_SECONDS = 2;
const BLINK_MS = 600;
const BLINK_OPACITY = 90;
const COLORS = {
    attention: [0.90, 0.16, 0.13],
    busy: [0.11, 0.55, 0.30],
    other: [0.45, 0.47, 0.50],
};

function colorFor(session) {
    if (session.attention) return COLORS.attention;
    return session.status === "busy" ? COLORS.busy : COLORS.other;
}

function paintDot(cr, width, height, session) {
    const ringWidth = Math.max(2, Math.round(height * 0.1));
    const cx = width / 2, cy = height / 2;
    const discRadius = Math.min(width, height) / 2 - ringWidth - 1;
    const ringRadius = Math.min(width, height) / 2 - ringWidth / 2;

    const [r, g, b] = colorFor(session);
    cr.setSourceRGB(r, g, b);
    cr.arc(cx, cy, discRadius, 0, 2 * Math.PI);
    cr.fill();

    // The ring is how full the session's context is.
    if (session.contextFraction !== null) {
        const start = -Math.PI / 2;
        cr.setLineWidth(ringWidth);
        cr.setSourceRGBA(1, 1, 1, 0.2);
        cr.arc(cx, cy, ringRadius, 0, 2 * Math.PI);
        cr.stroke();
        cr.setSourceRGB(1, 1, 1);
        cr.arc(cx, cy, ringRadius, start, start + 2 * Math.PI * session.contextFraction);
        cr.stroke();
    }

    cr.selectFontFace("Sans", Cairo.FontSlant.NORMAL, Cairo.FontWeight.BOLD);
    cr.setFontSize(discRadius * 0.95);
    const box = cr.textExtents(session.label);
    cr.setSourceRGB(1, 1, 1);
    cr.moveTo(cx - box.width / 2 - box.xBearing, cy - box.height / 2 - box.yBearing);
    cr.showText(session.label);
}

// ponytail: raises the terminal window only. It cannot pick the tab, a terminal server
// with many windows raises the first one, and tmux has no window to find at all.
function focusTerminal(pids) {
    for (const actor of global.get_window_actors()) {
        const win = actor.get_meta_window();
        if (pids.includes(win.get_pid())) {
            Main.activateWindow(win);
            return;
        }
    }
}

class SessionDotsApplet extends Applet.Applet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.collector = `${metadata.path}/collect.py`;
        this.polling = false;
        this.dots = [];
        this.box = new St.BoxLayout({ style_class: "csd-box", y_align: Clutter.ActorAlign.CENTER });
        this.emptyLabel = new St.Label({ text: "–", y_align: Clutter.ActorAlign.CENTER });
        this.actor.add_child(this.box);
        this.actor.add_child(this.emptyLabel);

        this.blinkOn = true;
        this.blinkId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, BLINK_MS, () => {
            this.blinkOn = !this.blinkOn;
            for (const dot of this.dots)
                dot.area.opacity = dot.session.attention && !this.blinkOn ? BLINK_OPACITY : 255;
            return GLib.SOURCE_CONTINUE;
        });
        this.pollId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, POLL_SECONDS, () => {
            this._poll();
            return GLib.SOURCE_CONTINUE;
        });
        this._poll();
    }

    on_applet_removed_from_panel() {
        GLib.source_remove(this.pollId);
        GLib.source_remove(this.blinkId);
    }

    on_panel_height_changed() {
        this._show(this.dots.map(dot => dot.session), true);
    }

    _poll() {
        if (this.polling) return;
        this.polling = true;
        try {
            const proc = Gio.Subprocess.new(
                ["python3", "-I", this.collector],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
            proc.communicate_utf8_async(null, null, (p, res) => {
                this.polling = false;
                try {
                    this._show(JSON.parse(p.communicate_utf8_finish(res)[1]));
                } catch (e) {
                    this._fail(e);
                }
            });
        } catch (e) {
            this.polling = false;
            this._fail(e);
        }
    }

    _fail(error) {
        global.logError(`claude-session-dots: ${error.message}`);
        this.set_applet_tooltip(`Cannot read Claude sessions: ${error.message}`);
    }

    _show(sessions, forceRebuild) {
        // Rebuild only when dots appear or vanish, so tooltips stay open between polls.
        if (forceRebuild || sessions.length !== this.dots.length)
            this._rebuild(sessions.length);
        sessions.forEach((session, i) => {
            const dot = this.dots[i];
            dot.session = session;
            dot.tooltip.set_text(session.tooltip);
            dot.area.queue_repaint();
        });
        // Without dots this stays the only thing to hover and right-click.
        this.emptyLabel.visible = sessions.length === 0;
        this._applet_tooltip.preventShow = sessions.length > 0;
        this.set_applet_tooltip("No active Claude sessions");
    }

    _rebuild(count) {
        for (const dot of this.dots) dot.tooltip.destroy();
        this.box.destroy_all_children();
        const size = Math.max(16, Math.round(this._panelHeight * 0.8));
        this.dots = Array.from({ length: count }, () => {
            const area = new St.DrawingArea({ width: size, height: size, reactive: true, y_align: Clutter.ActorAlign.CENTER });
            const dot = { area, session: null, tooltip: new Tooltips.Tooltip(area, "") };
            area.connect("repaint", () => {
                if (!dot.session) return;
                const cr = area.get_context();
                const [width, height] = area.get_surface_size();
                paintDot(cr, width, height, dot.session);
                cr.$dispose();
            });
            area.connect("button-release-event", (_actor, event) => {
                if (event.get_button() !== Clutter.BUTTON_PRIMARY) return Clutter.EVENT_PROPAGATE;
                focusTerminal(dot.session.pids);
                return Clutter.EVENT_STOP;
            });
            this.box.add_child(area);
            return dot;
        });
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new SessionDotsApplet(metadata, orientation, panelHeight, instanceId);
}
