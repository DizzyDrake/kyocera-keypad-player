#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only verification of Dumbplayer DEV16 full source. No SDK/network/device needed."""
import hashlib, json, pathlib, sys
root = pathlib.Path(__file__).resolve().parent
manifest = json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
full = json.loads((root/'WQ439_FULL_PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
errors=[]
for ent in manifest['entries']:
    rel=ent['path']; p=pathlib.PurePosixPath(rel)
    if rel.startswith(('/', '\\')) or '\\' in rel or '..' in p.parts or p.is_absolute():
        errors.append('unsafe path: '+rel);continue
    file=root.joinpath(*p.parts)
    if not file.is_file():errors.append('missing: '+rel);continue
    data=file.read_bytes()
    if len(data)!=ent['size'] or hashlib.sha256(data).hexdigest()!=ent['sha256']:
        errors.append('mismatch: '+rel)
for name in ['SOURCE_MANIFEST.json','WQ439_READ_FIRST_FULL_SOURCE.md','WQ439_VERIFY_FULL_SOURCE.py']:
    file=root/name;expected=full['supplemental_files_sha256'][name]
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected:
        errors.append('supplementary mismatch: '+name)
if errors:
    print('FAILED:', *errors, sep='\n  ');sys.exit(1)
print('PASS:',len(manifest['entries']),'DEV16 source hashes + 3 full-package supplemental hashes')
