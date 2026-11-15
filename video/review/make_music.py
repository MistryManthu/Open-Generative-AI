"""Synth music bed (Am-F-C-G, 100 BPM) of a given length. Usage: python make_music.py <seconds> <out.wav>"""
import sys, numpy as np, soundfile as sf
SR = 24000; D = float(sys.argv[1]); T = np.arange(int(SR * D)) / SR
bpm = 100; beat = 60 / bpm; bar = beat * 4
def note(f, t0, dur, kind):
    t = T - t0; m = (t >= 0) & (t < dur); y = np.zeros_like(T); tt = t[m]
    if kind == "pad":
        w = sum(np.sin(2*np.pi*f*(1+d)*tt) for d in (-0.004, 0, 0.004))/3
        y[m] = w * np.minimum(tt/0.6, 1) * np.minimum((dur-tt)/0.6, 1) * 0.10
    else:
        w = np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*2*f*tt)
        y[m] = w * np.exp(-tt*6) * np.minimum(tt/0.005, 1) * 0.12
    return y
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
chords = [(57,60,64),(53,57,60),(48,52,55),(55,59,62)]
m = np.zeros_like(T)
for b in range(int(D / bar) + 1):
    ch = chords[b % 4]; t0 = b * bar
    for n in ch: m += note(hz(n), t0, bar + 0.2, "pad")
    m += note(hz(ch[0]-12), t0, bar, "pad") * 1.2
    for s in range(8): m += note(hz(ch[s % 3] + 12), t0 + s * beat/2, beat, "pluck")
for i in range(int(D / beat)):
    t = T - i * beat; mm = (t >= 0) & (t < 0.25)
    m[mm] += np.sin(2*np.pi*(55 + 70*np.exp(-t[mm]*30))*t[mm]) * np.exp(-t[mm]*14) * 0.28
m *= np.minimum(T/0.5, 1) * np.minimum((D-T)/1.2, 1)
m /= max(1e-6, np.abs(m).max()) / 0.8
sf.write(sys.argv[2], m.astype(np.float32), SR)
