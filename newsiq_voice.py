"""NewsIQ Tamil voice note (lightweight - no PyTorch).

Usage:  python3 newsiq_voice.py script_ta.txt NewsIQ_Tamil_Voice.mp3 [male|female] [speed]

Voice: AI4Bharat (IIT Madras) Indic-TTS Tamil FastPitch + HiFiGAN, converted to ONNX.
Needs:  pip install onnxruntime numpy soundfile --break-system-packages ; ffmpeg on PATH.
Model files are looked for in ./voice_models next to this script (or $NEWSIQ_VOICE_DIR):
  tokens_ta.json + for each of ta_encoder, ta_decoder, hifigan_ta either <name>.onnx (full) or the compact
  pack <name>.graph.onnx + <name>.weights16.npz (130 MB total; needs `pip install onnx`).

Script rules (the model only knows Tamil letters and , . ! ? ' ( ) -):
  - write numbers, dates, % and Rs amounts as Tamil words
  - write English names in Tamil script (Sensex -> சென்செக்ஸ்); one paragraph per story
Default: male voice at 1.2x speed (user-approved), pitch preserved.
"""
import json, os, re, subprocess, sys, tempfile, unicodedata
import numpy as np, soundfile as sf, onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.environ.get("NEWSIQ_VOICE_DIR", os.path.join(HERE, "voice_models"))

def _model_bytes(model_dir, name):
    """Full .onnx if present; else the compact pack (<name>.graph.onnx + <name>.weights16.npz,
    weights stored half-precision, expanded back to float32 so the maths is unchanged)."""
    full = os.path.join(model_dir, name + ".onnx")
    if os.path.exists(full):
        return full
    import onnx
    from onnx import numpy_helper
    m = onnx.load(os.path.join(model_dir, name + ".graph.onnx"))
    z = np.load(os.path.join(model_dir, name + ".weights16.npz"))
    w = {n: z[f"w{i}"] for i, n in enumerate(z["__names__"])}
    for k, init in enumerate(m.graph.initializer):
        if init.name in w:
            init.CopyFrom(numpy_helper.from_array(w[init.name].astype(np.float32), init.name))
    return m.SerializeToString()

class TamilTTS:
    def __init__(self, model_dir=MD):
        meta = json.load(open(os.path.join(model_dir, "tokens_ta.json"), encoding="utf-8"))
        self.ids = {c: i for i, c in enumerate(meta["vocab"])}
        self.spk = meta["speakers"]; self.sr = meta["sample_rate"]
        so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 2
        load = lambda name: ort.InferenceSession(_model_bytes(model_dir, name), so, providers=["CPUExecutionProvider"])
        self.enc, self.dec, self.vo = load("ta_encoder"), load("ta_decoder"), load("hifigan_ta")

    @staticmethod
    def clean(t):  # same as Coqui multilingual_cleaners
        t = unicodedata.normalize("NFC", t).lower()
        t = t.replace(";", ",").replace("-", " ").replace(":", ",")
        t = re.sub(r"[\<\>\(\)\[\]\"]+", "", t)
        return re.sub(r"\s+", " ", t).strip()

    def say(self, sentence, speaker="male"):
        tok = [self.ids[c] for c in self.clean(sentence) if c in self.ids]
        if not tok:
            return np.zeros(0, dtype=np.float32)
        h, dur = self.enc.run(None, {"x": np.array([tok], dtype=np.int64), "sid": np.array([self.spk[speaker]], dtype=np.int64)})
        dur = np.round(np.maximum(dur.reshape(-1), 1.0)).astype(np.int64)   # frames per letter (FastPitch rule)
        h = np.repeat(h, dur, axis=2)                                         # length regulator
        mel = self.dec.run(None, {"h": h.astype(np.float32)})[0]
        return self.vo.run(None, {"mel": mel})[0].reshape(-1)

def split_sentences(para):
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+", para) if s.strip()]

def make_voice(text, out_mp3, speaker="male", speed=1.2):
    tts = TamilTTS()
    gap_s, gap_p = np.zeros(int(tts.sr * 0.35)), np.zeros(int(tts.sr * 0.7))
    parts = []
    for para in [p.strip() for p in text.split("\n") if p.strip()]:
        for s in split_sentences(para):
            parts += [tts.say(s, speaker), gap_s]
        parts.append(gap_p)
    wav = np.concatenate(parts).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wav, tts.sr)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f.name, "-af",
                    f"atempo={speed},loudnorm=I=-16:TP=-1.5", "-ac", "1", "-b:a", "96k", out_mp3], check=True)
    os.unlink(f.name)
    return len(wav) / tts.sr / speed

if __name__ == "__main__":
    spk = sys.argv[3] if len(sys.argv) > 3 else "male"
    spd = float(sys.argv[4]) if len(sys.argv) > 4 else 1.2
    secs = make_voice(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2], spk, spd)
    print(f"ok {sys.argv[2]} ~{secs/60:.1f} min")
