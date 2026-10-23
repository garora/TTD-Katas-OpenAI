# Kata 13 — Text-to-Speech Contracts

## Learning goal

Validate a TTS request and synthetic audio-output envelope without synthesizing audio. The kata keeps text, voice, locale, speed, format, disclosure, provenance, and output metadata explicit and fixture based.

## Run

```powershell
python -m unittest discover -s katas/13-tts-contracts -p "test_*.py" -v
```

## Definition of done

- [ ] Request text, voice, locale, speed, format, and disclosure validate offline.
- [ ] Output metadata records content type, byte length, duration, model, voice, and synthetic provenance.
- [ ] No real audio generation, speaker output, or API key is required.
