"""Generates voiceover (Kokoro TTS) and a synthesized music bed for the 15s launch video.
Usage: <venv>/bin/python make_audio.py <kokoro.onnx> <voices.bin>
"""
import sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SR = 24000
# (spoken text, on-screen caption, pause after in seconds). Each phrase is synthesized
# separately so captions and scene cuts can follow the exact voice timing.
PHRASES = [
    ("Introducing Avva Signage.", "Introducing Avva Signage", 0.6),
    ("Where your brand lights up.", "Where your brand lights up", 0.9),
    ("Neon.", "Neon", 0.35),
    ("L E D.", "LED", 0.35),
    ("Custom signs, made just for you.", "Custom signs, made just for you", 0.9),
    ("Now live at avva signage dot com.", "Now live at avvasignage.com", 0.0),
]
import json
k = Kokoro(sys.argv[1], sys.argv[2])
vo = np.zeros(SR * 15, dtype=np.float32); t = 0.5; timing = []
for text, cap, gap in PHRASES:
    s, sr = k.create(text, voice="hf_beta", speed=0.98, lang="en-us")
    # trim leading/trailing silence so timings are tight
    nz = np.where(np.abs(s) > 0.01)[0]; s = s[nz[0]:nz[-1] + 1]
    i = int(t * SR); vo[i:i + len(s)] += s[:len(vo) - i]
    timing.append({"text": text, "caption": cap, "start": round(t, 3), "end": round(t + len(s) / SR, 3)})
    print(f"{t:5.2f}-{t + len(s)/SR:5.2f}  {text}")
    t += len(s) / SR + gap
sf.write("audio/voice.wav", vo, SR)
json.dump(timing, open("audio/timing.json", "w"), ensure_ascii=False, indent=1)

# --- music: warm pad + plucked arpeggio + soft pulse, Am-F-C-G at 100 BPM ---
bpm = 100; beat = 60 / bpm; T = np.arange(SR * 15) / SR
def note(f, t0, dur, kind):
    t = T - t0; m = (t >= 0) & (t < dur); y = np.zeros_like(T)
    tt = t[m]
    if kind == "pad":
        w = sum(np.sin(2*np.pi*f*(1+d)*tt) for d in (-0.004, 0, 0.004))/3
        env = np.minimum(tt/0.6, 1) * np.minimum((dur-tt)/0.6, 1)
        y[m] = w * env * 0.10
    else:
        w = np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*2*f*tt)
        y[m] = w * np.exp(-tt*6) * np.minimum(tt/0.005, 1) * 0.12
    return y
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
chords = [(57,60,64),(53,57,60),(48,52,55),(55,59,62)]  # Am F C G
m = np.zeros_like(T); bar = beat * 4
for b in range(4):
    ch = chords[b % 4]; t0 = b * bar
    for n in ch: m += note(hz(n), t0, bar + 0.2, "pad")
    m += note(hz(ch[0]-12), t0, bar, "pad") * 1.2
    for s in range(8):
        m += note(hz(ch[s % 3] + 12), t0 + s * beat/2, beat, "pluck")
# last bar: hold the tonic chord to resolve
m += note(hz(57), 4*bar, 2, "pad") + note(hz(64), 4*bar, 2, "pad")
# soft kick on every beat
for i in range(int(15 / beat)):
    t = T - i * beat; mm = (t >= 0) & (t < 0.25)
    m[mm] += np.sin(2*np.pi*(55 + 70*np.exp(-t[mm]*30))*t[mm]) * np.exp(-t[mm]*14) * 0.28
m *= np.minimum(T/0.5, 1) * np.minimum((15-T)/1.2, 1)
m /= max(1e-6, np.abs(m).max()) / 0.8
sf.write("audio/music.wav", m.astype(np.float32), SR)
