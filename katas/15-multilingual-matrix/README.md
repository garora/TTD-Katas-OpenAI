# Kata 15 — Multilingual Language Matrix

## Learning goal

Evaluate multilingual fixture outputs using versioned locale tags, script expectations, required terms, and number preservation. The matrix is representative—not a claim of a fixed provider-language count or a general translation-quality benchmark.

## Run

```powershell
python -m unittest discover -s katas/15-multilingual-matrix -p "test_*.py" -v
```

## Definition of done

- [ ] Matrix uses versioned BCP 47-style tags and representative scripts.
- [ ] Locale, script, terms, and numbers are deterministic offline invariants.
- [ ] Unknown or malformed locales fail explicitly.
- [ ] Translation quality is outside this fixture-contract kata.
