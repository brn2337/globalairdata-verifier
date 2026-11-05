# Global Air Data release verifier

Installer source, checksums, and public signing key for [Global Air Data](https://www.globalairdata.com/).

**Installer: 0.1.53. Released October 31, 2026.**

[Setup guide](https://www.globalairdata.com/install#existing-feeder) ·
[Release manifest](https://install.globalairdata.com/releases/globalairdata-feeder-latest.json) ·
[Signature](https://install.globalairdata.com/releases/globalairdata-feeder-latest.json.sig)

## Install

Requires Python 3.9+, OpenSSL, curl, and sha256sum on your Raspberry Pi or Linux feeder.
Paste this block into your SSH terminal:

```sh
cd "$(mktemp -d)" &&
curl -fsS https://install.globalairdata.com/releases/install-0.1.53.py -o install.py &&
echo '4b26e8f5c208f813db67d2ee21f6b7207a397024e76f1610ed297ba9a0d8e175  install.py' | sha256sum -c - &&
python3 -I install.py
```

Enter your sudo password if prompted. Then open `http://<feeder-ip>:8750`,
copy the claim code, and claim your feeder in the
[iPhone/iPad app](https://apps.apple.com/us/app/globalairdata/id6765583716)
or [web dashboard](https://app.globalairdata.com/app.html#feeders).

## Verification

The command checks the installer's SHA-256 checksum before running it. The installer
checks the release signature and bundle checksum before requesting sudo, then
verifies the files again before installation.

Signed updates use the same checks. Unsigned, altered, expired, or older releases
are rejected. Failed updates use the existing rollback process.

Get the install command from a source you trust. Signatures confirm who authorized
a release; they don't guarantee bug-free or harmless software. This repository
contains the verifier, not the full feeder source or an independent security audit.

## Updates and controls

New installs enable daily updates and remote dashboard commands. Existing
preferences are preserved. Add these options to the final command as needed:

- `--updates off`: disable automatic updates.
- `--remote-commands off`: disable remote dashboard commands.
- `--verify-only`: check the release without installing it.

## Files

- [`install-0.1.53.py`](install-0.1.53.py): installer and verifier with the public key built in.
- [`release-public.pem`](release-public.pem): public signing key.
- [`SHA256SUMS`](SHA256SUMS): file checksums.

Tested on Raspberry Pi 3B and Zero, including rejection of unsigned or altered
releases. Recovery from a deliberately failed installation was also tested on the Pi 3B.
