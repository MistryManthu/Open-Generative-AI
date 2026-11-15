"""Transcribe src/audio16k.wav phrase by phrase (split at silences) -> transcript.json with start/end times."""
import sys, json, re, subprocess, numpy as np, soundfile as sf, sherpa_onnx
M = sys.argv[1]; lang = sys.argv[2] if len(sys.argv) > 2 else ""
out = subprocess.run(["ffmpeg","-i","src/audio16k.wav","-af","silencedetect=noise=-33dB:d=0.3","-f","null","-"],capture_output=True,text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]; se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
a, sr = sf.read("src/audio16k.wav", dtype="float32"); dur = len(a) / sr
# speech spans = gaps between silences
starts = [0.0] + se; ends = ss + [dur]
spans = [(s, e) for s, e in zip(starts, ends) if e - s > 0.25]
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/small-encoder.int8.onnx", decoder=f"{M}/small-decoder.int8.onnx",
        tokens=f"{M}/small-tokens.txt", language=lang, task="transcribe", num_threads=4)
res = []
for s, e in spans:
    st = rec.create_stream(); st.accept_waveform(sr, a[int(max(0, s-0.1)*sr):int(min(dur, e+0.1)*sr)]); rec.decode_stream(st)
    r = st.result; res.append({"start": round(s,2), "end": round(e,2), "text": r.text.strip(), "lang": getattr(r, "lang", "")})
    print(res[-1])
json.dump(res, open("transcript.json", "w"), ensure_ascii=False, indent=1)
