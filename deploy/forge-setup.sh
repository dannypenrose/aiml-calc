#!/usr/bin/env bash
#
# forge-setup.sh: install or update aiml-calc's public web UI (https://aiml.dannypenrose.com) in
# the forge machine.
#
# Why it exists: forge (the live-apps machine) runs in OrbStack on the home server Mac and is
# reached with `orb -m forge -u root`. This copies deploy/forge/ into it and runs install.sh
# there, so the whole set-up is one command that is safe to repeat.
#
# Runs on: the home server Mac (Bash 3.2), as you. Run it yourself.
#
# Usage:
#   deploy/forge-setup.sh             plan only: checks and prints what would change
#   deploy/forge-setup.sh --apply     install or repair, then smoke test
#   deploy/forge-setup.sh --update    pull main in forge, reinstall dependencies, restart
#
# The public side (the tunnel rule and the DNS record for aiml.dannypenrose.com) lives in
# Cloudflare and is not touched here; see docs/deployment.md.
#
# Exit codes: 0 success, 1 failure or refused, 2 usage error.

set -Eeuo pipefail

MACHINE="${FORGE_MACHINE:-forge}"   # FORGE_MACHINE: only for testing in a throwaway machine
HERE="$(cd "$(dirname "$0")" && pwd -P)"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

case "${1:-}" in
  ""|--apply|--update) ;;
  -h|--help) sed -n '12,15p' "$0"; exit 0 ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; sed -n '12,15p' "$0" >&2; exit 2 ;;
esac

command -v orb >/dev/null || die "orb (OrbStack) is not on PATH; run this on the home server Mac"
orb list 2>/dev/null | grep -Eq "^${MACHINE}[[:space:]]+running" || die "the $MACHINE machine is not running (orb list)"
[[ -f "$HERE/forge/install.sh" ]] || die "missing $HERE/forge/install.sh"

REMOTE_DIR="$(orb -m "$MACHINE" -u root mktemp -d /root/aiml-calc-setup.XXXXXX)"
[[ -n "$REMOTE_DIR" ]] || die "could not make a temporary folder in $MACHINE"
cleanup() { orb -m "$MACHINE" -u root rm -rf "${REMOTE_DIR:?}" || true; }
trap cleanup EXIT

COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata -C "$HERE/forge" -cf - . | orb -m "$MACHINE" -u root tar -xf - -C "$REMOTE_DIR"
orb -m "$MACHINE" -u root bash "$REMOTE_DIR/install.sh" "$@"
