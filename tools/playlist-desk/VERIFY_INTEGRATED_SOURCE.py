#!/usr/bin/env python3
"""Read-only SHA256 verification for the extracted source files. Python stdlib only."""
from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parent
rows=(root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines()
seen=set()
for row in rows:
    digest, sep, name=row.partition('  ')
    if not sep or len(digest)!=64 or name in seen or Path(name).is_absolute() or '..' in Path(name).parts:
        raise SystemExit('Invalid manifest row: '+row)
    seen.add(name)
    path=root/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise SystemExit('FAILED: '+name)
print(f'PASS: {len(seen)} file SHA-256 hashes match')
