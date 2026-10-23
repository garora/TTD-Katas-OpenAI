# Kata 12 — Speech-to-Text Contracts

## Learning goal

Validate transcription input/output contracts with synthetic fixture metadata—never a microphone, network call, or real recording. The kata models supported local audio metadata, BCP 47-style language hints, normalized transcript segments, and privacy-safe failures.

## Public API

`normalize_transcription(AudioInput, response) -> Transcript` validates fixture metadata and creates structured transcript segments. Language hints are validated locally; they are not a claim of a fixed provider-language list.

## Run

```powershell
python -m unittest discover -s katas/12-stt-contracts -p "test_*.py" -v
```

## Definition of done

- [ ] Fixture-only audio metadata and transcript segments validate offline.
- [ ] Language hints use valid BCP 47-style tags.
- [ ] Segment times and transcript structure are explicit.
- [ ] No recording bytes, microphone, API key, or network call is used.
