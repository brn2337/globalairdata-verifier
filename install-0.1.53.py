#!/usr/bin/env python3
"""Standalone signed installer and shared updater verifier (Python 3.9+).

The release public key is embedded, never downloaded or read from environment.
This file is published byte-for-byte as the versioned public installer.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAnib/OnvLEWIgW6Tb/JlN
v4ukgzYLC5wBsILWJkFK8LLSlcW54UxQtjcO5WUOz5oOMJVBFVqWYRRpBEBMJY7w
L86Z5rnK+zf1nzOCaVfjs3FS1duz5ln2LnSftAmy799rImOvM4Q0a7qXOF27+swd
0JVMV8CSILSyr3Rlz8/whBjFvs7aEa09luglqkrOdRHSZ0RiHOndmJTuVflvrtBc
i8r47oGTNQbimLWWjk7kMtBR/sOvdGesoeAHw7Bq2ClUi/yld+MAMPc5mjQ7HMLH
8zmqMTRE7HR1c4mqQGI/5CE4xEpWyXGT6gGkYubJOAk8K5o2DOhmvFg8v093Wr7U
G88AlB3TUNJDQK3SAKTaWMsk8e+kcuEunrtb0pXEsjp8GLgLyDGvGNO+yCKSsnGv
08pJW6+VIpkQpjlzIfbMUG+1G18dOKfWrSWlx6H2a4aEV76m34fiKiGsWn0kpdnk
1O4EJBETfoc1IHZvqH5fmFNY0OpCQWgiwGCrFbYqzGnfAgMBAAE=
-----END PUBLIC KEY-----
"""
MINIMUM_VERSION = '0.1.53'
MANIFEST_URL = 'https://install.globalairdata.com/releases/globalairdata-feeder-latest.json'
MAX_ARCHIVE = 30 * 1024 * 1024


def require_https(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Release downloads require HTTPS without credentials or fragments')
    return url


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, target, limit):
    require_https(url)
    with build_opener(HTTPSRedirects()).open(url, timeout=60) as response, Path(target).open('wb') as output:
        require_https(response.geturl())
        total = 0
        while True:
            chunk = response.read(min(65536, limit + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ValueError('Release download exceeds size limit')
            output.write(chunk)


def version_tuple(version):
    if not isinstance(version, str) or not re.fullmatch(r'\d{1,6}\.\d{1,6}\.\d{1,6}', version):
        raise ValueError('Invalid release version')
    return tuple(map(int, version.split('.')))


def verify_manifest(directory, minimum=MINIMUM_VERSION):
    directory = Path(directory)
    manifest_path = directory / 'manifest.json'
    signature_path = directory / 'manifest.sig'
    if manifest_path.stat().st_size > 65536 or signature_path.stat().st_size > 4096:
        raise ValueError('Release metadata exceeds size limit')
    # Verify the exact manifest bytes before parsing any release-controlled fields.
    with tempfile.TemporaryDirectory(prefix='gad-key-') as temporary:
        key = Path(temporary) / 'release.pem'
        key.write_bytes(PUBLIC_KEY)
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-verify', str(key), '-signature', str(signature_path), str(manifest_path)],
            capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError('Release signature verification failed; nothing was installed')
    manifest = json.loads(manifest_path.read_bytes())
    version = manifest['version']
    if version_tuple(version) < version_tuple(minimum):
        raise ValueError('Release downgrade rejected')
    if manifest.get('signature_format') != 'rsa-sha256-v1':
        raise ValueError('Unsupported release signature format')
    if manifest['archive'] != 'globalairdata-feeder-' + version + '.tar.gz':
        raise ValueError('Invalid release archive name')
    if not re.fullmatch('[0-9a-f]{64}', manifest['archive_sha256']):
        raise ValueError('Invalid release checksum')
    built = datetime.fromisoformat(manifest['built_at'].replace('Z', '+00:00'))
    expires = datetime.fromisoformat(manifest['expires_at'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    if built.tzinfo is None or expires.tzinfo is None or built > now + timedelta(days=1) or expires <= now or expires <= built:
        raise ValueError('Release metadata expired or clock is incorrect')
    return manifest


def fetch_manifest(url, directory, minimum=MINIMUM_VERSION):
    directory = Path(directory)
    download(url, directory / 'manifest.json', 65536)
    download(url + '.sig', directory / 'manifest.sig', 4096)
    return verify_manifest(directory, minimum)


def verify_archive(directory, manifest):
    archive = Path(directory) / 'bundle.tar.gz'
    if archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError('Release archive exceeds size limit')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != manifest['archive_sha256']:
        raise ValueError('Archive checksum mismatch; nothing was installed')
    return archive


def fetch_archive(url, directory, manifest):
    # A signed manifest names a file, never an arbitrary download URL.
    download(url.rsplit('/', 1)[0] + '/' + manifest['archive'], Path(directory) / 'bundle.tar.gz', MAX_ARCHIVE)
    return verify_archive(directory, manifest)


def extract_archive(archive, destination):
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if len(members) > 10000 or sum(m.size for m in members) > 100 * 1024 * 1024:
            raise ValueError('Bundle exceeds extraction limits')
        seen = set()
        for member in members:
            path = Path(member.name)
            if (path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'feeder-bundle'
                    or not (member.isfile() or member.isdir()) or member.size < 0 or path in seen):
                raise ValueError('Unsafe bundle member')
            seen.add(path)
        # Every member has been checked: no links, devices, traversal or duplicates.
        for member in members:
            member.uid = member.gid = 0
            member.uname = member.gname = ''
            member.mode = 0o755 if member.isdir() else 0o644
        source.extractall(destination, members=members)
    bundle = Path(destination) / 'feeder-bundle'
    return bundle


def installed_version():
    path = Path('/opt/globalairdata/agent/src/globalairdata_agent/__init__.py')
    if path.exists():
        match = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)', path.read_text())
        if match:
            return match[1]
    return MINIMUM_VERSION


def install_local(directory, dry_run=False, updates=None, remote_commands=None):
    # Copy into a new private directory and re-verify after privilege elevation.
    # Only authenticated content is extracted or executed by the root phase.
    with tempfile.TemporaryDirectory(prefix='gad-verified-') as temporary:
        temporary = Path(temporary)
        for name, limit in [('manifest.json', 65536), ('manifest.sig', 4096), ('bundle.tar.gz', MAX_ARCHIVE)]:
            with (Path(directory) / name).open('rb') as source, (temporary / name).open('wb') as target:
                data = source.read(limit + 1)
                if len(data) > limit:
                    raise ValueError('Release file exceeds size limit')
                target.write(data)
        minimum = max((MINIMUM_VERSION, installed_version()), key=version_tuple)
        manifest = verify_manifest(temporary, minimum)
        archive = verify_archive(temporary, manifest)
        bundle = extract_archive(archive, temporary)
        project = (bundle / 'agent/pyproject.toml').read_text()
        match = re.search(r'^version = "([^"]+)"', project, re.MULTILINE)
        if not match or match[1] != manifest['version']:
            raise ValueError('Bundle version differs from signed manifest')
        if not (bundle / 'installer/overlay_install.sh').is_file():
            raise ValueError('Bundle is missing its installer')
        if dry_run:
            print('Signature, checksum, archive and version verified. No system changes made.')
            return
        if os.geteuid() != 0:
            raise RuntimeError('The installation phase requires sudo')
        env = dict(os.environ)
        for option, flag in [(updates, 'GAD_ENABLE_UPDATER'), (remote_commands, 'GAD_ENABLE_COMMAND_RUNNER')]:
            if option is not None:
                env[flag] = '1' if option == 'on' else '0'
        subprocess.run(['bash', str(bundle / 'installer/overlay_install.sh')], env=env, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Verify and install Global Air Data. Daily updates remain automatic.')
    parser.add_argument('--manifest-url', default=MANIFEST_URL)
    parser.add_argument('--verify-only', action='store_true', help='verify the release without changing the system')
    parser.add_argument('--install-local', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--updates', choices=('on', 'off'), help='explicitly enable/disable scheduled updates')
    parser.add_argument('--remote-commands', choices=('on', 'off'), help='explicitly enable/disable dashboard commands')
    args = parser.parse_args(argv)
    if args.install_local:
        install_local(args.install_local, args.verify_only, args.updates, args.remote_commands)
        return
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or newer is required')
    if not shutil.which('openssl'):
        parser.error('OpenSSL is required')
    minimum = max((MINIMUM_VERSION, installed_version()), key=version_tuple)
    with tempfile.TemporaryDirectory(prefix='gad-download-') as temporary:
        manifest = fetch_manifest(args.manifest_url, temporary, minimum)
        fetch_archive(args.manifest_url, temporary, manifest)
        print('Global Air Data ' + manifest['version'] + ': signature and checksum verified.', flush=True)
        if args.verify_only or os.geteuid() == 0:
            install_local(temporary, args.verify_only, args.updates, args.remote_commands)
            return
        print('Administrator access is needed to install services. Existing maintenance preferences are preserved.', flush=True)
        command = ['sudo', '/usr/bin/python3', '-I', str(Path(__file__).resolve()), '--install-local', temporary]
        for name in ('updates', 'remote_commands'):
            value = getattr(args, name)
            if value is not None:
                command.extend(['--' + name.replace('_', '-'), value])
        subprocess.run(command, check=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('Installation stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
