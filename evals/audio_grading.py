"""Offline deterministic audio/multilingual evaluation helpers."""
from __future__ import annotations
import re, unicodedata

def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

def language_tag_is_valid(tag: str) -> bool:
    return bool(re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", tag))

def numbers_in_text(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\d+", unicodedata.normalize("NFKC", value)))

def contains_script(value: str, script: str) -> bool:
    ranges={"latin":((0x0041,0x024F),),"devanagari":((0x0900,0x097F),),"han":((0x4E00,0x9FFF),),"arabic":((0x0600,0x06FF),)}
    return any(any(start<=ord(char)<=end for start,end in ranges[script]) for char in value)
