# Global Air Data release verifier

Public source and trust material for the Global Air Data signed feeder installer.

**Status: 0.1.53 is a canary candidate. General rollout has not been approved.**
The normal fleet update channel has not been switched to this version. This
repository is published for inspection; installation instructions will be added
when the release is approved for general use.

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
feeder. Device clocks must be reasonably correct.

Project: [Global Air Data](https://www.globalairdata.com/)
