#!/usr/bin/env python3
"""Deterministically pseudonymize common PII in text artifacts.

The script is intentionally conservative: it replaces strong identifiers
such as IBAN and Italian codice fiscale automatically, and replaces person
names only when they appear in common labeled fields or in a provided mapping.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path


TEXT_EXTENSIONS = {
    ".cbl",
    ".cpy",
    ".txt",
    ".csv",
    ".json",
    ".xml",
    ".md",
    ".log",
    ".sql",
    ".dat",
}

IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
CODICE_FISCALE_RE = re.compile(
    r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b",
    re.IGNORECASE,
)

COBOL_NAME_MOVE_RE = re.compile(
    r"(?P<prefix>\bMOVE\s+')(?P<value>[^']{2,80})(?P<suffix>'\s+TO\s+"
    r"[\w-]*(?:NOME|COGNOME|NOMINATIVO|OPER-NOME)[\w-]*\b)",
    re.IGNORECASE,
)
KEY_VALUE_NAME_RE = re.compile(
    r"(?P<prefix>\b(?:nome|cognome|nominativo|first[_ -]?name|last[_ -]?name)"
    r"\b\s*[:=]\s*[\"']?)(?P<value>[^\r\n,'\"]{2,79})(?P<suffix>[\"']?)",
    re.IGNORECASE,
)


FIRST_NAMES = [
    "Mario",
    "Luca",
    "Anna",
    "Giulia",
    "Marco",
    "Sara",
    "Paolo",
    "Laura",
    "Andrea",
    "Elena",
]
LAST_NAMES = [
    "Rossi",
    "Bianchi",
    "Ferrari",
    "Romano",
    "Gallo",
    "Costa",
    "Conti",
    "Ricci",
    "Marino",
    "Greco",
]


def digest(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value.upper()}".encode("utf-8")).hexdigest()


def digits_from_hash(value: str, salt: str, length: int) -> str:
    raw = str(int(digest(value, salt), 16))
    while len(raw) < length:
        raw += raw
    return raw[:length]


def letters_from_hash(value: str, salt: str, length: int) -> str:
    number = int(digest(value, salt), 16)
    chars = []
    for _ in range(length):
        chars.append(chr(ord("A") + (number % 26)))
        number //= 26
    return "".join(chars)


def iban_mod97(value: str) -> int:
    converted = []
    for char in value:
        if char.isdigit():
            converted.append(char)
        elif "A" <= char <= "Z":
            converted.append(str(ord(char) - ord("A") + 10))
    remainder = 0
    for char in "".join(converted):
        remainder = (remainder * 10 + int(char)) % 97
    return remainder


def iban_check_digits(country: str, bban: str) -> str:
    check = 98 - iban_mod97(bban + country + "00")
    return f"{check:02d}"


def pseudonymize_iban(value: str, salt: str) -> str:
    compact = re.sub(r"\s+", "", value.upper())
    country = compact[:2]
    body_len = max(len(compact) - 4, 0)
    if country == "IT" and body_len == 23:
        bban = (
            letters_from_hash(compact, salt + ":iban-cin", 1)
            + digits_from_hash(compact, salt + ":iban-bank", 10)
            + digits_from_hash(compact, salt + ":iban-account", 12)
        )
    else:
        bban = letters_from_hash(compact, salt, body_len)
    return country + iban_check_digits(country, bban) + bban


CF_ODD = {
    **{str(index): value for index, value in enumerate([1, 0, 5, 7, 9, 13, 15, 17, 19, 21])},
    **dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23])),
}
CF_EVEN = {
    **{str(index): index for index in range(10)},
    **{char: index for index, char in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")},
}


def codice_fiscale_check_char(first_15: str) -> str:
    total = 0
    for index, char in enumerate(first_15):
        total += CF_ODD[char] if index % 2 == 0 else CF_EVEN[char]
    return chr(ord("A") + total % 26)


def pseudonymize_codice_fiscale(value: str, salt: str) -> str:
    compact = value.upper()
    first_15 = (
        letters_from_hash(compact, salt + ":cf1", 6)
        + digits_from_hash(compact, salt + ":cf2", 2)
        + letters_from_hash(compact, salt + ":cf3", 1)
        + digits_from_hash(compact, salt + ":cf4", 2)
        + letters_from_hash(compact, salt + ":cf5", 1)
        + digits_from_hash(compact, salt + ":cf6", 3)
    )
    return first_15 + codice_fiscale_check_char(first_15)


def pseudonymize_person_name(value: str, salt: str) -> str:
    cleaned = value.strip()
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    number = int(digest(cleaned, salt + ":name"), 16)
    first = FIRST_NAMES[number % len(FIRST_NAMES)]
    last = LAST_NAMES[(number // len(FIRST_NAMES)) % len(LAST_NAMES)]
    if len(parts) <= 1:
        return first
    return f"{first} {last}"


def load_mapping(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    mapping: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2 or not row[0].strip():
                continue
            mapping[row[0].strip()] = row[1].strip()
    return mapping


def apply_literal_mapping(text: str, mapping: dict[str, str]) -> str:
    for original, replacement in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"\b{re.escape(original)}\b", replacement, text)
    return text


def pseudonymize_text(text: str, salt: str, name_mapping: dict[str, str]) -> tuple[str, int]:
    count = 0

    def replace_iban(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return pseudonymize_iban(match.group(0), salt)

    def replace_cf(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return pseudonymize_codice_fiscale(match.group(0), salt)

    def replace_name(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return match.group("prefix") + pseudonymize_person_name(match.group("value"), salt) + match.group("suffix")

    before = text
    text = apply_literal_mapping(text, name_mapping)
    if text != before:
        count += 1

    text = IBAN_RE.sub(replace_iban, text)
    text = CODICE_FISCALE_RE.sub(replace_cf, text)
    text = COBOL_NAME_MOVE_RE.sub(replace_name, text)
    text = KEY_VALUE_NAME_RE.sub(replace_name, text)
    return text, count


def iter_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return [
        path
        for path in input_path.rglob("*")
        if path.is_file() and (path.suffix.lower() in TEXT_EXTENSIONS or not path.suffix)
    ]


def output_path_for(source: Path, input_root: Path, output_root: Path) -> Path:
    if input_root.is_file():
        return output_root / source.name
    return output_root / source.relative_to(input_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input file or folder.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Folder for pseudonymized output.")
    parser.add_argument("--salt", required=True, help="Stable secret salt for deterministic pseudonyms.")
    parser.add_argument(
        "--name-map",
        type=Path,
        help="Optional CSV with original,replacement entries for known names.",
    )
    args = parser.parse_args()

    name_mapping = load_mapping(args.name_map)
    files = iter_files(args.input)
    changed_files = 0
    replacements = 0

    for source in files:
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = source.read_text(encoding="latin-1")
        pseudonymized, count = pseudonymize_text(text, args.salt, name_mapping)
        target = output_path_for(source, args.input, args.out_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(pseudonymized, encoding="utf-8", newline="")
        if count:
            changed_files += 1
            replacements += count

    print(f"Processed {len(files)} files; changed {changed_files}; replacements {replacements}.")
    print(f"Wrote pseudonymized output to: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
