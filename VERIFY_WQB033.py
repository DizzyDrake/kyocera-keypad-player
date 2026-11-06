#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify WQB033 additive package; optional independent original-source comparison."""
import argparse,hashlib,json,zipfile,pathlib,sys
H=lambda b:hashlib.sha256(b).hexdigest()
ORIGINAL_SHA='0c81e75ed298d76d157e4c27c21d17509bf79214bfb70a0893794a206ee04cfd'
LICENSE_SHA='cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30'
def verify(package,source=None):
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None, 'ZIP CRC failure'
        names=z.namelist()
        assert len(names)==len(set(names)), 'duplicate ZIP entry'
        manifest=json.loads(z.read('WQB033_PACKAGE_MANIFEST.json'))
        assert manifest['original_archive_sha256']==ORIGINAL_SHA
        assert len(manifest['original_members'])==96
        assert len(manifest['payload_sha256'])==100
        assert set(names)==set(manifest['payload_sha256'])|{'WQB033_PACKAGE_MANIFEST.json'},'member set mismatch'
        for n,sha in manifest['payload_sha256'].items():
            assert H(z.read(n))==sha, 'payload hash mismatch: '+n
        assert H(z.read('LICENSE'))==LICENSE_SHA, 'official LICENSE mismatch'
        for n,sha in manifest['original_members'].items():
            assert H(z.read(n))==sha,'original member changed: '+n
        old=json.loads(z.read('SOURCE_MANIFEST.json'))
        assert len(old['files'])==95,'historical source manifest count'
        for n,sha in old['files'].items():
            assert H(z.read(n))==sha,'historical source manifest hash: '+n
        if source:
            source=pathlib.Path(source)
            assert H(source.read_bytes())==ORIGINAL_SHA,'original source archive SHA mismatch'
            with zipfile.ZipFile(source) as s:
                assert s.testzip() is None
                assert set(s.namelist())==set(manifest['original_members'])
                for n in s.namelist():
                    assert s.read(n)==z.read(n),'source byte difference: '+n
    return True
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package');p.add_argument('--source');a=p.parse_args()
    verify(a.package,a.source);print('PASS: CRC, original 96, payload 100, historical manifest 95, LICENSE SHA, optional source parity')
