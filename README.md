# NewsIQ Tamil voice pack

Private voice files for the NewsIQ daily news brief (Tamil voice note).

- `voice_models/` – compact ONNX pack of the AI4Bharat (IIT Madras) Indic-TTS **Tamil** voice
  (FastPitch text encoder + decoder, HiFiGAN vocoder). Weights are stored in half precision and
  expanded back to full precision when loaded, so output matches the original model.
- `newsiq_voice.py` – makes an MP3 from a Tamil script. Default: male voice at 1.2x speed.

## Use

```bash
pip install onnx onnxruntime numpy soundfile --break-system-packages   # ffmpeg must be installed
git clone --depth 1 https://github.com/antoraj72-gif/newsiq-voice
python3 newsiq-voice/newsiq_voice.py script_ta.txt NewsIQ_Tamil_Voice.mp3 male 1.2
```

Script rules: Tamil letters only – write numbers, dates, % and rupee amounts as Tamil words, and
English names in Tamil script. One paragraph per story.

## Credits

Voice model: AI4Bharat Indic-TTS (https://github.com/AI4Bharat/Indic-TTS), released under its own
licence (see that repository). Converted to ONNX for lightweight CPU use.

## Other folders

- `fonts/` – NewsIQ Tamil font (Noto Sans Tamil + Noto Sans merged, SIL Open Font Licence) used by the
  Tamil PDF builder.
- `newsiq_thumb.py` – 1280x720 JPEG headline thumbnail (English or Tamil) from a brief JSON, with a topic icon.
- `icons/` – curated Tabler Icons (MIT licence, see icons/LICENSE-tabler-icons.txt).
- `briefs/YYYY-MM-DD/` – each edition's Tamil PDF, Tamil voice note (MP3) and thumbnails, linked from the email.
