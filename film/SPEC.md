GOAL:    A developer running several Claude Code sessions wants this dot on their panel.
OUTPUT:  HyperFrames, 1920x1080, 30 fps. Silent on purpose: a GitHub README plays muted.
TIME:    33.3 s = 999 frames. prompt 4.2, tabs 4, panel 7.4, red 5, answer 5.9, end 6.8.
LOOK:    The product's own palette as worlds: red #E62921, green #1C8C4D, grey #73787F,
         panel #1C1E21, desktop #4F6F64, end card #F4F5F2, ink #16181C.
         Inter 800 at 110-170 px, -2% tracking. JetBrains Mono 40 px for terminal text.
         No gradients, no shadows beyond the window's 0 30 80 at 45%.
OBJECTS: Dot geometry copied from paintDot in applet.js: disc r 39, ring r 45 width 10 on a
         100-unit box, bold label at 37. Prompt wording and tooltip format copied from the
         real Claude Code prompt and collect.py. Session names and times are illustrative.
MOTION:  Arrive expo.out 0.5 s. Camera power2.inOut 0.6 s. Exit power3.in 0.3 s. Floods by
         clip-path from the dot itself. Blink 0.6 s steps at opacity 0.35, as in applet.js.
SHOTS:   prompt  0-126   clock rolls 14:02 to 14:47 under an unanswered prompt
         tabs    126-246 pull back to six alike tabs, cursor hunts, window leaves upward
         panel   246-468 dots land in the panel, panel floods the frame, green, grey, ring
         red     468-618 one dot turns red and blinks, floods, "Claude needs you"
         answer  618-795 hover tooltip, click raises the window, tab click, press 1, dot green
         end     795-999 claim, six dots become one, name, link
BANNED:  the spec.md defaults; implying a click switches tabs (it only raises the window).
QA:      0 prompt legible; 3.5 s 14:47; 6 s tabs and title; 12 s dots fill the frame;
         17 s red dot; 19.5 s flood title; 22.5 s tooltip; 25.5 s prompt; 26.5 s green; 32.5 s end card.
