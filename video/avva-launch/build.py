#!/usr/bin/env python3
"""Builds the 15s Avva Signage launch videos (landscape + vertical) with captions and
scene cuts driven by audio/timing.json (from make_audio.py), so picture follows the voice."""
import json, subprocess, os
os.chdir(os.path.dirname(os.path.abspath(__file__))); os.makedirs("tmp", exist_ok=True)
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; CREAM = "0xFDF4E3"; X = 0.15  # half crossfade
tm = json.load(open("audio/timing.json"))
# scene boundaries (cut lands on the first word of the phrase)
cuts = [tm[2]["start"], tm[3]["start"], tm[4]["start"], tm[5]["start"]]   # Neon, LED, Custom, Now live
T = [0] + [c - X for c in cuts]; E = [c + X for c in cuts] + [15.0]
dur = [E[i] - T[i] for i in range(5)]
def run(*a): subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)

def build(N, W, H, BW, BH, CY, ELH, NY, UY, US, CS, out):
    for i, f in enumerate(["src/2-sign.png", "src/3-birthday.jpg", "src/4-beautybar.jpg", "src/5-treat.jpg"], 1):
        run("-i", f, "-filter_complex",
            f"[0]split[a][b];[a]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},boxblur=40:5,eq=brightness=-0.15[bg];"
            f"[b]scale={BW}:{BH}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", f"tmp/{N}-{i}.png")
    zoom = ["1.12-0.08*t/{d}", "1+0.08*t/{d}", "1+0.08*t/{d}", "1.1-0.06*t/{d}"]
    for i in range(4):
        d = dur[i]; z = zoom[i].format(d=f"{d:.3f}").replace("t/", "on/30/")
        run("-loop", "1", "-framerate", "30", "-i", f"tmp/{N}-{i+1}.png", "-t", f"{d:.3f}", "-vf",
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30", "-pix_fmt", "yuv420p", "-r", "30", f"tmp/{N}-c{i+1}.mp4")
    run("-f", "lavfi", "-i", f"color=c={CREAM}:s={W}x{H}:r=30", "-i", "src/1-logo.png", "-filter_complex",
        f"[1]scale=-2:{ELH}[l];[0][l]overlay=(W-w)/2:{H//20},"
        f"drawtext=fontfile={B}:text='NOW LIVE':fontcolor=0x6B1F1F:fontsize={US//2}:x=(w-text_w)/2:y={NY},"
        f"drawtext=fontfile={B}:text='avvasignage.com':fontcolor=0x6B1F1F:fontsize={US}:x=(w-text_w)/2:y={UY}",
        "-t", f"{dur[4]:.3f}", "-pix_fmt", "yuv420p", f"tmp/{N}-c5.mp4")
    # captions: one per phrase, shown exactly while it is spoken (end card shows its own text)
    caps = []
    for j, p in enumerate(tm[:5]):
        open(f"tmp/cap{j}.txt", "w").write(p["caption"])
        caps.append(f"drawtext=fontfile={B}:textfile=tmp/cap{j}.txt:fontcolor=white:fontsize={CS}:x=(w-text_w)/2:y=h-{CY}"
                    f":box=1:boxcolor=0x3A0D0Dcc:boxborderw=24:enable='between(t,{p['start']-0.05},{p['end']+0.15})'")
    trans = ["fade", "slideleft", "slideleft", "fade"]
    v = "[0][1]xfade={0}:{1}:{2}[a];[a][2]xfade={3}:{1}:{4}[b];[b][3]xfade={5}:{1}:{6}[c];[c][4]xfade={7}:{1}:{8}[d];".format(
        trans[0], 2 * X, f"{T[1]:.3f}", trans[1], f"{T[2]:.3f}", trans[2], f"{T[3]:.3f}", trans[3], f"{T[4]:.3f}")
    v += "[d]" + ",".join(caps) + ",fade=t=out:st=14.5:d=0.5[v];"
    a = ("[5]asplit[vo1][vo2];[6][vo1]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=500[duck];"
         "[duck]volume=0.55[mu];[vo2]volume=1.6[vo];[mu][vo]amix=inputs=2:duration=first:normalize=0,afade=t=out:st=13.8:d=1.2,alimiter=limit=0.95[a]")
    run(*sum([["-i", f"tmp/{N}-c{i}.mp4"] for i in range(1, 6)], []), "-i", "audio/voice.wav", "-i", "audio/music.wav",
        "-filter_complex", v + a, "-map", "[v]", "-map", "[a]", "-t", "15", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-r", "30", "-c:a", "aac", "-b:a", "192k", out)

#     name W    H    boxW boxH capY endLogoH noteY urlY urlSize capSize out
build("land", 1920, 1080, 3600, 2000, 130, 760, 830, 900, 96, 64, "avva-launch.mp4")
build("vert", 1080, 1920, 2100, 3000, 340, 900, 1130, 1230, 80, 56, "avva-launch-vertical.mp4")
for f in ["avva-launch.mp4", "avva-launch-vertical.mp4"]:
    print(f, subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip())
