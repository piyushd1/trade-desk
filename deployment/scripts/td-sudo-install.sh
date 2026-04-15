#!/bin/bash
# td-sudo-install.sh — install the td-sudo-on/off toggle scripts + sudoers template
# from the repo into system locations.
#
# Run as root (use sudo). Installs:
#   /etc/trade-desk/sudoers           — canonical sudoers template (mode 0640)
#   /usr/local/bin/td-sudo-on         — enable script (mode 0755)
#   /usr/local/bin/td-sudo-off        — disable script (mode 0755)
#
# Source of truth for all three files lives in the repo alongside this
# installer at deployment/scripts/ and deployment/sudoers/.
#
# Usage:
#   sudo bash /home/piyushdev/trade-desk/deployment/scripts/td-sudo-install.sh
#
# After installing, use td-sudo-on / td-sudo-off from any shell to toggle
# the live sudoers drop-in at /etc/sudoers.d/trade-desk.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Error: must run as root (use sudo)" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SUDOERS_SRC="${REPO_ROOT}/deployment/sudoers/trade-desk"
ON_SRC="${SCRIPT_DIR}/td-sudo-on"
OFF_SRC="${SCRIPT_DIR}/td-sudo-off"

for src in "$SUDOERS_SRC" "$ON_SRC" "$OFF_SRC"; do
  if [[ ! -f "$src" ]]; then
    echo "Error: source file not found: $src" >&2
    exit 1
  fi
done

# Create the template directory and install the sudoers file (NOT in
# /etc/sudoers.d/ — inactive until td-sudo-on copies it there).
install -d -m 0755 -o root -g root /etc/trade-desk
install -m 0640 -o root -g root "$SUDOERS_SRC" /etc/trade-desk/sudoers

# Syntax-check the installed template before going further
if ! visudo -c -f /etc/trade-desk/sudoers >/dev/null; then
  echo "Error: installed sudoers template has syntax errors, rolling back" >&2
  rm -f /etc/trade-desk/sudoers
  exit 1
fi

# Install the toggle scripts
install -m 0755 -o root -g root "$ON_SRC"  /usr/local/bin/td-sudo-on
install -m 0755 -o root -g root "$OFF_SRC" /usr/local/bin/td-sudo-off

echo "Installed:"
echo "  /etc/trade-desk/sudoers"
echo "  /usr/local/bin/td-sudo-on"
echo "  /usr/local/bin/td-sudo-off"
echo
echo "Usage:"
echo "  td-sudo-on [MINUTES]   # enable (default indefinite; optional 1-240 min auto-off)"
echo "  td-sudo-off            # disable immediately"
