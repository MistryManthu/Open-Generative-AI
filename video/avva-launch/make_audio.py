"""Generates voiceover (Kokoro TTS) and a synthesized music bed for the 15s launch video.
Usage: <venv>/bin/python make_audio.py <kokoro.onnx> <voices.bin>
"""
import sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SR = 24000
LINES = [  # (text, start second in video)
    ("Introducing Avva Signage.", 0.4),
    ("Where your brand lights up.", 3.4),
    ("Neon. L E D. Custom signs, made just for you.", 5.7),
    ("Now live at avva signage dot com.", 10.7),
]
k = Kokoro(sys.argv[1], sys.argv[2])
vo = np.zeros(SR * 15, dtype=np.float32)
for text, t0 in LINES:
    s, sr = k.create(text, voice="hf_beta", speed=0.98, lang="en-us")
    i = int(t0 * SR); n = min(len(s), len(vo) - i)
    print(f"{t0:5.1f}s +{len(s)/sr:.2f}s  {text}")
    vo[i:i+n] += s[:n]
sf.write("audio/voice.wav", vo, SR)

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
