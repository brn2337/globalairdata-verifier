# Global Air Data release verifier

Installer source, checksums, and public signing key for [Global Air Data](https://www.globalairdata.com/).

**Installer: 0.1.55. Released November 19, 2026.**

[Setup guide](https://www.globalairdata.com/install#existing-feeder) ·
[Release manifest](https://install.globalairdata.com/releases/globalairdata-feeder-0.1.55.json) ·
[Signature](https://install.globalairdata.com/releases/globalairdata-feeder-0.1.55.json.sig)

## Install

Requires systemd, Python 3.9+, OpenSSL, curl, sha256sum, and rsync on your Raspberry Pi or Linux feeder.
Paste this block into your SSH terminal:

```sh
cd "$(mktemp -d)" &&
curl -fsS https://install.globalairdata.com/releases/install-0.1.55.py -o install.py &&
echo 'a5af1a174d345f23c628baab7b207d9a480a8bdc5ecc5ef60a246023d4892099  install.py' | sha256sum -c - &&
python3 -I install.py
```

Enter your sudo password if prompted. Then open `http://<feeder-ip>:8750`,
select **Claim this feeder**, and enter the code in the
[iPhone/iPad app](https://apps.apple.com/us/app/globalairdata/id6765583716)
or [web dashboard](https://app.globalairdata.com/app.html#feeders).

## Verification

The SHA-256 of the signed 0.1.55 feeder archive is `be151f3cb3fa2596839cd07fd9f12cd0c8d713dab7bdb98e7a32b0827e3c4521`.

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

- [`install-0.1.55.py`](install-0.1.55.py): installer and verifier with the public key built in.
- [`release-public.pem`](release-public.pem): public signing key.
- [`SHA256SUMS`](SHA256SUMS): file checksums.

Release 0.1.55 fixes first installs on existing PiAware and readsb stations. It also includes owner-authorized Wi-Fi management for enabled pilot devices. A standard overlay leaves the station’s existing Wi-Fi configuration in place. The release test covers a clean Debian 12 ARM installation, local claiming, and reinstalling with an owner-disabled timer.
