#!/usr/bin/env python3
"""Movie-review edit: enhance face video, jump-cut zooms, synced captions, title/rating/CTA graphics, music ducked under voice.
Inputs: src/raw.mp4, src/music.wav (make_music.py), captions.json ([start,end,text]). Outputs: review-vertical.mp4, review-landscape.mp4"""
import json, subprocess, os, textwrap
os.chdir(os.path.dirname(os.path.abspath(__file__))); os.makedirs("tmp", exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
caps = json.load(open("captions.json")); DUR = 35.3
def run(*a): subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)

# 1) enhanced core with zoom jump-cuts on phrase boundaries (video only, 1080x1920)
B = [0, 2.3, 6.5, 10.2, 15.5, 19.8, 24.0, 26.7, 30.2, DUR]; Z = [1.0, 1.12, 1.0, 1.14, 1.0, 1.12, 1.0, 1.14, 1.0]
enh = "hqdn3d=2.5:2:4:4,eq=gamma=1.15:contrast=1.07:saturation=1.12:brightness=0.01"
fc = f"[0:v]{enh},split={len(Z)}" + "".join(f"[s{i}]" for i in range(len(Z))) + ";"
for i, z in enumerate(Z):
    fc += (f"[s{i}]trim={B[i]}:{B[i+1]},setpts=PTS-STARTPTS,scale=iw*{z}:ih*{z}:flags=lanczos,"
           f"crop=1080:1920:(iw-1080)*0.45:(ih-1920)*0.30,unsharp=5:5:0.9:3:3:0.4[p{i}];")
fc += "".join(f"[p{i}]" for i in range(len(Z))) + f"concat=n={len(Z)}:v=1:a=0[v]"
run("-i", "src/raw.mp4", "-filter_complex", fc, "-map", "[v]", "-r", "30", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "tmp/core.mp4")

# 1b) poster cutaways (full-screen, synced to the phrase being spoken): (poster, start, end, zoom_in?)
CUT = [("p3", 2.55, 6.17, True), ("p4", 6.97, 9.78, False), ("p2", 13.55, 15.5, True), ("p1", 20.03, 24.3, False)]
for k, (p, s, e, zin) in enumerate(CUT):
    d = e - s; z = f"1+0.10*on/30/{d:.3f}" if zin else f"1.10-0.10*on/30/{d:.3f}"
    run("-i", f"src/posters/{p}.jpg", "-filter_complex",
        "[0]split[a][b];[a]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,boxblur=40:5,eq=brightness=-0.2[bg];"
        "[b]scale=2000:-2:flags=lanczos,unsharp=5:5:0.8[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", f"tmp/{p}_comp.png")
# (cutaway streams are built inside one filtergraph below; -t on the input limits each poster clip's length)
fc2 = "[0:v]null[b0];"
for k, (p, s, e, zin) in enumerate(CUT):
    d = e - s; z = f"1+0.10*on/30/{d:.3f}" if zin else f"1.10-0.10*on/30/{d:.3f}"
    fc2 += (f"[{k+1}:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuva420p,"
            f"fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st={d-0.15:.3f}:d=0.15:alpha=1,setpts=PTS+{s}/TB[c{k}];"
            f"[b{k}][c{k}]overlay=0:0:eof_action=pass[b{k+1}];")
run("-i", "tmp/core.mp4", *sum([["-loop", "1", "-framerate", "30", "-t", f"{e-s:.3f}", "-i", f"tmp/{p}_comp.png"] for p, s, e, z in CUT], []),
    "-filter_complex", fc2.rstrip(";"), "-map", f"[b{len(CUT)}]", "-r", "30", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "tmp/core2.mp4")

# 2) audio: clean voice, music ducked under it
af = ("[0:a]highpass=f=90,afftdn=nr=12:nf=-30,acompressor=threshold=0.1:ratio=3:attack=10:release=150,"
      "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,asplit[vo1][vo2];"
      "[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.6[m];"
      "[m][vo1]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=500[duck];"
      f"[duck][vo2]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={DUR-1.2}:d=1.2,alimiter=limit=0.95[a]")
run("-i", "src/raw.mp4", "-i", "src/music.wav", "-filter_complex", af, "-map", "[a]", "-t", str(DUR), "tmp/audio.wav")

# 3) overlays per orientation
def overlay(name, W, H, capFont, wrapW, capBottom, topY, topFont, ratingFont, landscape, out):
    chain = []
    if landscape:
        chain.append(f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=-0.1[bg];"
                     f"[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0[base]")
    else:
        chain.append("[0:v]null[base]")
    d = []
    def txt(file_or_text, size, color, x, y, enable, box="0x000000a0", bw=22, is_file=True, extra=""):
        src = f"textfile={file_or_text}" if is_file else f"text='{file_or_text}'"
        return (f"drawtext=fontfile={F}:{src}:fontcolor={color}:fontsize={size}:x={x}:y={y}:line_spacing=10:"
                f"box=1:boxcolor={box}:boxborderw={bw}:enable='{enable}'{extra}")
    for i, (s, e, t) in enumerate(caps):
        open(f"tmp/{name}_cap{i}.txt", "w").write(t)
        d.append(txt(f"tmp/{name}_cap{i}.txt", capFont, "white", "(w-text_w)/2", f"h-{capBottom}-text_h", f"between(t,{s-0.03},{e+0.12})",
                     extra=":borderw=2:bordercolor=black"))
    open(f"tmp/{name}_t1.txt", "w").write("MOVIE REVIEW"); open(f"tmp/{name}_t2.txt", "w").write("O.M: OPERATION MOLE")
    d.append(txt(f"tmp/{name}_t1.txt", topFont, "0xFFD54A", "(w-text_w)/2", topY, "between(t,0.3,9.9)", box="0x6B1F1Fe6", bw=18))
    d.append(txt(f"tmp/{name}_t2.txt", int(topFont*1.35), "white", "(w-text_w)/2", topY + int(topFont*2.0), "between(t,0.3,9.9)", box="0x3A0D0De6", bw=18))
    open(f"tmp/{name}_r.txt", "w").write("3 / 5"); open(f"tmp/{name}_s.txt", "w").write("★★★☆☆")
    d.append(txt(f"tmp/{name}_r.txt", ratingFont, "0xFFD54A", "(w-text_w)/2", topY + int(topFont*2.0) + 40, "between(t,20.0,24.3)", box="0x000000b0", bw=30))
    d.append(txt(f"tmp/{name}_s.txt", int(ratingFont*0.45), "0xFFD54A", "(w-text_w)/2", topY + int(topFont*2.0) + 40 + int(ratingFont*1.5), "between(t,20.0,24.3)", box="0x000000b0", bw=16))
    open(f"tmp/{name}_c.txt", "w").write("LIKE  •  FOLLOW  •  SHARE")
    d.append(txt(f"tmp/{name}_c.txt", topFont, "white", "(w-text_w)/2", topY, "between(t,28.8,34.6)", box="0x6B1F1Fe6", bw=18))
    chain.append("[base]" + ",".join(d) + ",fade=t=out:st=34.8:d=0.5[v]")
    run("-i", "tmp/core2.mp4", "-i", "tmp/audio.wav", "-filter_complex", ";".join(chain), "-map", "[v]", "-map", "1:a", "-t", str(DUR),
        "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out)

overlay("v", 1080, 1920, 58, 24, 380, 150, 48, 200, False, "review-vertical.mp4")
overlay("l", 1920, 1080, 50, 34, 110, 70, 40, 150, True, "review-landscape.mp4")
for f in ["review-vertical.mp4", "review-landscape.mp4"]:
    print(f, subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
