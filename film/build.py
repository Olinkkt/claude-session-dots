#!/usr/bin/env python3
"""Writes the scene files, so the dot and terminal stay identical across scenes."""
SESSIONS = [
    ("api-server", "AS", "green", .21), ("web-app", "WA", "green", .29), ("docs-site", "DS", "grey", .32),
    ("billing", "BI", "green", .22), ("mobile", "MO", "grey", .17), ("infra", "IN", "green", .13),
]
FILL = {"green": "#1C8C4D", "grey": "#73787F", "red": "#E62921"}
RING = 282.74
BASE = """*{box-sizing:border-box}#root{position:absolute;inset:0;overflow:hidden;font-family:Inter;color:#fff}
.t{font-weight:800;letter-spacing:-.02em;line-height:1.05;position:absolute}
.h{opacity:0}.row{position:absolute;display:flex}.row svg{display:block;flex:none}
.win{position:absolute;background:#16181C;font-family:'JetBrains Mono';font-size:40px;line-height:1.45;overflow:hidden}
.tabs{display:flex;height:84px;background:#26292E}.tab{flex:1;display:flex;align-items:center;justify-content:center;font-size:46px;color:#A9AEB5;border-right:2px solid #16181C}
.tab.on{background:#16181C;color:#fff}.body{position:absolute;left:0;right:0;top:84px;bottom:0;padding:44px 70px;white-space:pre}
.dim{color:#8C929A}.hi{color:#7FB8FF}.warn{color:#E8A33D}
.cur{position:absolute;left:0;top:0;width:66px;height:66px;z-index:50}
.bar{position:absolute;left:0;right:0;bottom:0;height:120px;background:#1C1E21}
.clock{position:absolute;right:50px;bottom:0;height:120px;line-height:120px;font-size:44px;font-weight:600}"""
CURSOR = '<svg class="cur h" id="{id}" viewBox="0 0 24 24"><path d="M3 2l15 12-7 1 4 7-3 1.5-4-7-5 5z" fill="#fff" stroke="#000" stroke-width="1.3" stroke-linejoin="round"/></svg>'
PROMPT = """<span class="warn">Bash command</span>
  npm run deploy
  Deploy the web app to staging

Do you want to proceed?
<span id="{p}-yes"><span class="hi">❯</span> 1. Yes</span>
  2. Yes, and always allow access to build/ from this project
  3. Yes, and switch to auto mode
  4. No"""


def dot(p, s, size, state=None, ring=True):
    name, label, st, f = s
    st = state or st
    key = f"{p}-{label.lower()}"
    r = (f'<circle cx="50" cy="50" r="45" fill="none" stroke="#fff" stroke-opacity=".2" stroke-width="10"/>'
         f'<circle id="{key}-arc" cx="50" cy="50" r="45" fill="none" stroke="#fff" stroke-width="10" stroke-dasharray="{f*RING:.1f} {RING}" transform="rotate(-90 50 50)"/>') if ring else ""
    return (f'<svg id="{key}" class="dot {st}" width="{size}" height="{size}" viewBox="0 0 100 100"><circle id="{key}-disc" cx="50" cy="50" r="39" fill="{FILL[st]}"/>{r}'
            f'<text x="50" y="50" dy=".36em" text-anchor="middle" font-family="Inter" font-weight="800" font-size="37" fill="#fff">{label}</text></svg>')


def row(p, size, gap, css, red=False):
    return f'<div class="row" id="{p}-row" style="gap:{gap}px;{css}">' + "".join(
        dot(p, s, size, "red" if red and s[1] == "WA" else None) for s in SESSIONS) + "</div>"


def tabs(p, on):
    return '<div class="tabs">' + "".join(
        f'<div class="tab{" on" if s[0] == on else ""}" id="{p}-tab-{s[1].lower()}">{s[0]}</div>' for s in SESSIONS) + "</div>"


def scene(name, css, html, js):
    open(f"compositions/{name}.html", "w").write(f"""<template>
<style>{BASE}
{css}</style>
<div id="root" data-composition-id="{name}" data-width="1920" data-height="1080" data-layout-allow-overflow data-layout-allow-overlap>
{html}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["{name}"] = tl;
</script>
</template>
""")


# ---- 1. The prompt nobody answers
minutes = "".join(f"<div>{m:02d}</div>" for m in range(2, 48))
scene("prompt", """#root{background:#16181C}
#a-body{position:absolute;left:0;right:0;top:0;padding:60px 90px;font-family:'JetBrains Mono';font-size:40px;line-height:1.45;white-space:pre}
#a-clock{position:absolute;left:90px;top:620px;font-size:300px;font-weight:800;letter-spacing:-.03em;line-height:360px;height:360px;display:flex;overflow:hidden}
#a-strip{height:360px}#a-strip div{height:360px}
#a-l1,#a-l2{left:1010px;font-size:82px;width:830px}#a-l1{top:680px}#a-l2{top:680px;color:#E62921}
.dim-prompt{color:#fff}""",
f"""<div id="a-body">{PROMPT.format(p="a")}</div>
<div id="a-clock"><div>14:</div><div id="a-strip">{minutes}</div></div>
<div class="t" id="a-l1">Claude asked you something.</div>
<div class="t h" id="a-l2">Nobody answered.</div>""",
"""tl.to("#a-strip",{y:-360*45,duration:1.7,ease:"power2.inOut"},1.2);
tl.to("#a-l1",{opacity:0,filter:"blur(8px)",duration:.18},2.95);
tl.fromTo("#a-l2",{opacity:0,filter:"blur(8px)"},{opacity:1,filter:"blur(0px)",duration:.18},3.05);
tl.to("#a-clock,#a-l2",{opacity:0,filter:"blur(10px)",duration:.2,ease:"power3.in"},4.0);""")

# ---- 2. Six tabs that look alike
WORK = ["✻ Working… running tests", "✻ Thinking…", "✻ Working… editing checkout.ts", "✻ Working… 3 agents running", "✻ Thinking…"]
bodies = "".join(f'<div class="body h" id="b-b{i}">{t}\n\n<span class="dim">esc to interrupt</span></div>' for i, t in enumerate(WORK))
hops = [(0, "as"), (1, "ds"), (2, "bi"), (3, "mo"), (4, "in")]
hop_js = ""
for n, (i, tab) in enumerate(hops):
    t = 1.0 + n * .42
    x = 320 * "as wa ds bi mo in".split().index(tab) + 160
    hop_js += f'tl.to("#b-cur",{{x:{x},y:60,duration:.3,ease:"power2.inOut"}},{t-.3:.2f});\n'
    hop_js += f'tl.set("#b-body0,.body",{{opacity:0}},{t:.2f});tl.set("#b-b{i}",{{opacity:1}},{t:.2f});\n'
    hop_js += f'tl.set(".tab",{{background:"#26292E",color:"#A9AEB5"}},{t:.2f});tl.set("#b-tab-{tab}",{{background:"#16181C",color:"#fff"}},{t:.2f});\n'
scene("tabs", """#root{background:#4F6F64}
#b-win{left:0;top:-84px;width:1920px;height:1164px;box-shadow:0 30px 80px rgba(0,0,0,.45);transform-origin:0 0}
#b-l1,#b-l2{left:70px;font-size:112px;width:560px}#b-l1{top:150px}#b-l2{top:560px}""",
f"""<div class="win" id="b-win">{tabs("b", "web-app")}<div class="body" id="b-body0">{PROMPT.format(p="b")}</div>{bodies}{CURSOR.format(id="b-cur")}</div>
<div class="t h" id="b-l1">Six tabs.</div><div class="t h" id="b-l2">Which one?</div>""",
f"""tl.to("#b-win",{{x:680,y:190,scale:.62,duration:.6,ease:"power2.inOut"}},0);
tl.fromTo("#b-l1",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.18}},.45);
tl.set("#b-cur",{{opacity:1,x:1500,y:900,scale:1.5}},.5);
{hop_js}tl.fromTo("#b-l2",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.18}},2.3);
tl.to("#b-win",{{y:-1100,duration:.4,ease:"power3.in"}},3.6);
tl.to("#b-l1,#b-l2",{{opacity:0,filter:"blur(8px)",duration:.2}},3.6);""")

# ---- 3. The dots arrive and the panel becomes the world
dots_in = "".join(f'tl.fromTo("#c-{s[1].lower()}",{{scale:0}},{{scale:1,duration:.45,ease:"back.out(1.6)",transformOrigin:"50% 50%"}},{.15+i*.09:.2f});\n' for i, s in enumerate(SESSIONS))
green = ",".join(f"#c-{s[1].lower()}" for s in SESSIONS if s[2] == "green")
grey = ",".join(f"#c-{s[1].lower()}" for s in SESSIONS if s[2] == "grey")
scene("panel", """#root{background:#4F6F64}
#c-bar{transform-origin:50% 100%}
#c-row{left:255px;top:915px;transform-origin:0 0}
#c-clockt{z-index:2}
#c-title{left:96px;top:180px;font-size:150px;width:1500px}
.v{left:255px;top:190px;font-size:128px}""",
f"""<div class="bar" id="c-bar"></div><div class="clock" id="c-clockt">14:47</div>
{row("c", 210, 30, "")}
<div class="t h" id="c-title">One dot for every session.</div>
<div class="t h v" id="c-v1">Green: working</div>
<div class="t h v" id="c-v2">Grey: idle</div>
<div class="t h v" id="c-v3">White ring: context used</div>""",
f"""tl.set("#c-row",{{x:809,y:57,scale:.457}},0);
tl.fromTo("#c-bar",{{y:120}},{{y:0,duration:.35,ease:"expo.out"}},0);
tl.fromTo("#c-clockt",{{y:120}},{{y:0,duration:.35,ease:"expo.out"}},0);
{dots_in}tl.fromTo("#c-title",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.2}},1);
tl.to("#c-title",{{opacity:0,filter:"blur(8px)",duration:.18}},3.0);
tl.to("#c-bar",{{scaleY:9,duration:.6,ease:"power2.inOut"}},3.05);
tl.to("#c-clockt",{{opacity:0,duration:.15}},3.05);
tl.to("#c-row",{{x:0,y:-400,scale:1,duration:.6,ease:"power2.inOut"}},3.05);
tl.fromTo("#c-v1",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.15}},3.65);
tl.to("{grey}",{{opacity:.25,duration:.15}},3.65);
tl.to("#c-v1",{{opacity:0,duration:.12}},4.75);
tl.fromTo("#c-v2",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.15}},4.85);
tl.to("{grey}",{{opacity:1,duration:.15}},4.85);tl.to("{green}",{{opacity:.25,duration:.15}},4.85);
tl.to("#c-v2",{{opacity:0,duration:.12}},5.75);
tl.fromTo("#c-v3",{{opacity:0,filter:"blur(8px)"}},{{opacity:1,filter:"blur(0px)",duration:.15}},5.85);
tl.to("{green}",{{opacity:1,duration:.15}},5.85);
tl.fromTo("#c-wa-arc",{{attr:{{"stroke-dasharray":"{.29*RING:.1f} {RING}"}}}},{{attr:{{"stroke-dasharray":"{.62*RING:.1f} {RING}"}},duration:.9,ease:"power2.inOut"}},5.95);
tl.to("#c-wa-arc",{{attr:{{"stroke-dasharray":"{.29*RING:.1f} {RING}"}},duration:.3,ease:"power2.inOut"}},7.05);
tl.to("#c-v3",{{opacity:0,duration:.12}},7.2);""")

# ---- 4. Red
blink = "".join(f'tl.set("#d-wa",{{opacity:{o}}},{t:.1f});\n' for t, o in [(.9, .35), (1.5, 1), (2.1, .35), (2.7, 1)])
scene("red", """#root{background:#1C1E21}
#d-row{left:255px;top:515px}
#d-flood{position:absolute;inset:0;background:#E62921;clip-path:circle(0px at 600px 620px)}
#d-title{left:96px;top:330px;font-size:230px;width:1700px;line-height:1}""",
f"""{row("d", 210, 30, "")}
<div id="d-flood"></div>
<div class="t h" id="d-title">Claude needs you.</div>""",
f"""tl.to("#d-wa-disc",{{attr:{{fill:"#E62921"}},duration:.08}},.3);
{blink}tl.fromTo("#d-flood",{{clipPath:"circle(82px at 600px 620px)"}},{{clipPath:"circle(2100px at 600px 620px)",duration:.65,ease:"power2.inOut",immediateRender:false}},2.9);
tl.set("#d-row",{{opacity:0}},3.56);
tl.fromTo("#d-title",{{opacity:0,filter:"blur(10px)"}},{{opacity:1,filter:"blur(0px)",duration:.2}},3.25);
tl.to("#d-title",{{opacity:0,filter:"blur(8px)",duration:.15}},4.65);
tl.set("#d-row",{{opacity:1}},4.69);
tl.to("#d-flood",{{clipPath:"circle(0px at 600px 620px)",duration:.28,ease:"power3.in"}},4.7);""")

# ---- 5. Answer it
scene("answer", """#root{background:#1C1E21}
#e-row{left:255px;top:515px}
#e-tip{position:absolute;left:255px;top:190px;background:#000;border:2px solid #4A4E55;border-radius:10px;padding:26px 36px;font-size:38px;line-height:1.4;white-space:pre}
#e-tip b{color:#fff}
#e-term{position:absolute;inset:0;clip-path:circle(0px at 600px 620px);background:#16181C}
#e-win{left:0;top:0;width:1920px;height:960px}
#e-p2{top:84px}
#e-wrow{left:1064px;bottom:12px}
#e-cur{z-index:50}""",
f"""{row("e", 210, 30, "", red=True)}
<div id="e-tip" class="h"><b>web-app</b>
NEEDS YOU: permission prompt for 45m · 290k context · opus-5-5
~/projects/web-app (main)</div>
<div id="e-term">
 <div class="win" id="e-win">{tabs("e", "infra")}
  <div class="body" id="e-work">✻ Thinking…

<span class="dim">esc to interrupt</span></div>
  <div class="body h" id="e-prompt">{PROMPT.format(p="e")}</div>
  <div class="body h" id="e-done">⏺ Bash(npm run deploy)

✻ Working…

<span class="dim">esc to interrupt</span></div>
 </div>
 <div class="bar"></div><div class="clock">14:47</div>
 {row("f", 96, 12, "left:1064px;top:972px;", red=True)}
</div>
{CURSOR.format(id="e-cur")}""",
"""tl.set("#e-cur",{opacity:1,scale:1.5,x:1500,y:1000},0);
tl.to("#e-cur",{x:600,y:620,duration:.6,ease:"power2.inOut"},.1);
tl.fromTo("#e-tip",{opacity:0,filter:"blur(6px)"},{opacity:1,filter:"blur(0px)",duration:.15},.85);
tl.fromTo("#e-term",{clipPath:"circle(0px at 600px 620px)"},{clipPath:"circle(2100px at 600px 620px)",duration:.3,ease:"power3.in"},3.90);
tl.set("#e-row,#e-tip",{opacity:0},4.21);
tl.to("#e-cur",{x:505,y:62,duration:.45,ease:"power2.inOut"},4.15);
tl.set(".tab",{background:"#26292E",color:"#A9AEB5"},4.62);
tl.set("#e-tab-wa",{background:"#16181C",color:"#fff"},4.62);
tl.set("#e-work",{opacity:0},4.62);tl.set("#e-prompt",{opacity:1},4.62);
tl.set("#e-yes",{backgroundColor:"#2F6FBF"},5.10);
tl.set("#e-prompt",{opacity:0},5.25);tl.set("#e-done",{opacity:1},5.25);
tl.to("#f-wa-disc",{attr:{fill:"#1C8C4D"},duration:.1},5.25);""")

# ---- 6. Claim and end card
stack = "".join(f'tl.to("#g-{s[1].lower()}",{{x:{(2.5-i)*108:.0f},duration:.4,ease:"power3.in"}},3.5);\n' for i, s in enumerate(SESSIONS))
scene("end", """#root{background:#16181C}
#h-win{left:0;top:0;width:1920px;height:960px}
#g-ground{position:absolute;inset:0;background:#F4F5F2;clip-path:circle(0px at 1220px 1020px)}
#g-claim{left:96px;top:300px;font-size:190px;width:1700px;color:#16181C;line-height:1.05}
#g-claim span{display:inline-block}
#g-red{color:#E62921}
#g-row{left:636px;top:492px;opacity:0}
#g-mark{position:absolute;left:330px;top:445px;opacity:0}
#g-name{left:560px;top:430px;font-size:110px;color:#16181C;clip-path:inset(0 100% 0 0);white-space:nowrap}
#g-link{left:565px;top:575px;font-family:'JetBrains Mono';font-weight:500;font-size:40px;letter-spacing:0;color:#16181C}
#g-sub{left:565px;top:640px;font-size:34px;font-weight:500;letter-spacing:0;color:#5A6068}""",
f"""<div class="win" id="h-win">{tabs("h", "web-app")}<div class="body">⏺ Bash(npm run deploy)

✻ Working…

<span class="dim">esc to interrupt</span></div></div>
<div class="bar"></div><div class="clock">14:47</div>
{row("h", 96, 12, "left:1064px;top:972px;")}
<div id="g-ground"></div>
<div class="t" id="g-claim"><span class="w h">Look</span> <span class="w h">up</span> <span class="w h">only</span><br><span class="w h">when</span> <span class="w h">it's</span> <span class="w h" id="g-red">red.</span></div>
{row("g", 96, 12, "")}
<svg id="g-mark" width="190" height="190" viewBox="0 0 100 100"><circle cx="50" cy="50" r="39" fill="#E62921"/><circle cx="50" cy="50" r="45" fill="none" stroke="#16181C" stroke-opacity=".15" stroke-width="10"/><circle cx="50" cy="50" r="45" fill="none" stroke="#16181C" stroke-width="10" stroke-dasharray="82 282.74" transform="rotate(-90 50 50)"/></svg>
<div class="t" id="g-name">Claude Session Dots</div>
<div class="t h" id="g-link">github.com/cufelix/claude-session-dots</div>
<div class="t h" id="g-sub">Cinnamon panel applet · MIT</div>""",
f"""tl.fromTo("#g-ground",{{clipPath:"circle(40px at 1220px 1020px)"}},{{clipPath:"circle(2300px at 1220px 1020px)",duration:.6,ease:"power2.inOut"}},0);
tl.set("#h-win,#h-row,.bar,.clock",{{opacity:0}},.61);
tl.fromTo(".w",{{opacity:0,filter:"blur(6px)"}},{{opacity:1,filter:"blur(0px)",duration:.13,stagger:.1}},.5);
tl.to("#g-claim",{{opacity:0,filter:"blur(8px)",duration:.18}},2.9);
tl.set("#g-row",{{opacity:1}},3.0);
tl.fromTo("#g-row svg",{{scale:0}},{{scale:1,duration:.3,ease:"back.out(1.6)",transformOrigin:"50% 50%",stagger:.04,immediateRender:false}},3.0);
{stack}tl.set("#g-row",{{opacity:0}},3.9);
tl.set("#g-mark",{{opacity:1,x:529,y:-2,scale:.5,transformOrigin:"50% 50%"}},3.9);
tl.to("#g-mark",{{x:0,y:0,scale:1,duration:.5,ease:"expo.out"}},3.92);
tl.to("#g-name",{{clipPath:"inset(0 0% 0 0)",duration:.5,ease:"power2.inOut"}},4.1);
tl.fromTo("#g-link",{{opacity:0,filter:"blur(6px)"}},{{opacity:1,filter:"blur(0px)",duration:.15}},4.55);
tl.fromTo("#g-sub",{{opacity:0,filter:"blur(6px)"}},{{opacity:1,filter:"blur(0px)",duration:.15}},4.7);""")

TIMES = [("prompt", 0, 4.2), ("tabs", 4.2, 4), ("panel", 8.2, 7.4), ("red", 15.6, 5), ("answer", 20.6, 5.9), ("end", 26.5, 6.8)]
hosts = "\n".join(f'<div id="{n}" data-composition-id="{n}" data-composition-src="compositions/{n}.html" data-start="{s}" data-duration="{d}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>' for n, s, d in TIMES)
open("index.html", "w").write(f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;overflow:hidden;background:#16181C}}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="33.3" data-width="1920" data-height="1080">
{hosts}
</div><script>window.__timelines=window.__timelines||{{}};window.__timelines["main"]=gsap.timeline({{paused:true}});</script></body></html>
""")
