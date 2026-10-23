# Kata 14 — Audio Round-Trip Evaluation

## Learning goal

Grade a fixture-based TTS → STT round trip using normalized text, required terms/numbers, locale, metadata, and latency budget. The evaluator deliberately does not demand byte-for-byte audio or character-for-character transcription equality.

## Run

```powershell
python -m unittest discover -s katas/14-audio-round-trip -p "test_*.py" -v
```

## Definition of done

- [ ] Round-trip fixtures are synthetic metadata/transcript records.
- [ ] Text normalizes before comparison; required entities and numbers remain explicit.
- [ ] Locale and latency are graded separately from content.
- [ ] Default tests make no live TTS/STT request.
