# Global Air Data release verifier

Public source and trust material for the Global Air Data signed feeder installer.

**Current release: 0.1.53 — deployed October 31, 2026.**
Signed installation and updates are live on the public release channel.
Feeders with automatic updates enabled receive the release on their normal daily
schedule. Offline feeders update after reconnecting and running their updater;
feeders with automatic updates disabled require owner action. Publishing the
release does not mean every feeder has already upgraded.

The release passed signed installation and update checks on Raspberry Pi 3B and
Zero test feeders. Both rejected unsigned manifests, altered manifests and altered
bundles before installation. A deliberately failed installation on the Pi 3B
successfully restored the previous installation and configuration. These are
project-run tests, not an independent security audit.

[Main setup guide](https://www.globalairdata.com/install#existing-feeder) ·
[Installer site](https://install.globalairdata.com/#existing-feeder) ·
[Current signed manifest](https://install.globalairdata.com/releases/globalairdata-feeder-latest.json) ·
[Detached signature](https://install.globalairdata.com/releases/globalairdata-feeder-latest.json.sig)

## Install

On your Raspberry Pi or Linux feeder (Python 3.9+, OpenSSL, curl and sha256sum),
copy and paste this entire block into your SSH terminal:

```sh
cd "$(mktemp -d)" &&
curl -fsS https://install.globalairdata.com/releases/install-0.1.53.py -o install.py &&
echo '4b26e8f5c208f813db67d2ee21f6b7207a397024e76f1610ed297ba9a0d8e175  install.py' | sha256sum -c - &&
python3 -I install.py
```

Enter your sudo password if prompted after verification. Follow the
[feeder setup instructions](https://www.globalairdata.com/install#existing-feeder)
to confirm the receiver is online, copy its claim code, and finish setup in the
[Global Air Data iPhone/iPad app](https://apps.apple.com/us/app/globalairdata/id6765583716)
or [web dashboard](https://app.globalairdata.com/app.html#feeders).
The old `curl | sudo bash` entry point has been retired and directs users to these
verified instructions. The verifier source and checksums can be inspected here
before running the command; no GitHub account is required.

## Files

- [`install-0.1.53.py`](install-0.1.53.py): standalone Python 3.9+ installer and
  verifier. Its release public key is embedded in the source.
- [`release-public.pem`](release-public.pem): the public verification key.
- [`SHA256SUMS`](SHA256SUMS): SHA-256 digests of those exact files.

No private signing key is included. GitHub is an independent distribution and
review location, not a third-party certification or signing service.

## What is verified

The installation command pins the standalone installer's SHA-256 before execution.
The installer then authenticates the exact release manifest using an RSA/SHA-256
signature, checks expiry and version, and verifies the bundle checksum. Downloads
must use HTTPS, including redirects. Unsafe archive members are rejected.

Administrator privileges are requested only after download verification. The
installation phase copies the inputs into a private directory and verifies them
again before extracting or executing any bundle code.

Automatic and explicitly requested updates use the same verification logic.
Unsigned, altered, expired or downgraded releases are rejected. There is no
unsigned fallback. The existing maintenance transaction handles health checks
and restores the previous installation after a failed update.

## Trust and user control

The initial installer/checksum must come from instructions you trust. Publishing
them independently of the download server reduces reliance on that server alone;
compromise of the GitHub account or signing key is still significant.

A valid signature establishes that the release was authorized by the holder of
the signing key. It does not prove that the software is harmless or bug-free.
This repository contains the verifier, not the complete feeder application's
source repository or an independent security audit.

The feeder runs its agent under a dedicated account; installation and maintenance
need administrator privileges. Fresh installs enable automatic updates and remote
dashboard commands. Existing maintenance opt-outs are preserved. Installer options
`--updates off` and `--remote-commands off` provide separate controls, and
`--verify-only` checks a release without installation.

An older feeder's first automatic migration still relies on its previous update
mechanism. Signed verification is enforced after migration. Signed metadata must
be refreshed before it expires; an expired manifest stops updates, not the running
feeder. The currently published manifest expires on **April 29, 2027**; the project
must publish valid signed metadata before then. Device clocks must be reasonably
correct. The downloadable Pi disk image was not rebuilt as part of this release;
this release covers the existing-feeder installer and update channel.

Project: [Global Air Data](https://www.globalairdata.com/)
