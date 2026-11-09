#!/usr/bin/env bash
# UAES U02 / S1 host admission: strictly read-only preflight.
# Run only from an already authorized session. Never copy full output
# (host topology, usernames, port details) to a public GitHub issue.
# No sudo, Docker writes, service restart, package install or file creation.
set -u
export LC_ALL=C

section() { printf '\n=== %s ===\n' "$1"; }
try_read() {
  if command -v "$1" >/dev/null 2>&1; then
    "$@" || printf 'CHECK_UNAVAILABLE: %s\n' "$1"
  else
    printf 'TOOL_NOT_INSTALLED: %s\n' "$1"
  fi
}

section "Identity, OS, kernel"
try_read id
try_read uname -srm
if [[ -r /etc/os-release ]]; then
  grep -E '^(ID|VERSION_ID|PRETTY_NAME)=' /etc/os-release || true
else
  printf 'OS_RELEASE_UNAVAILABLE\n'
fi

section "CPU and memory: admission depends on these values"
try_read nproc
if [[ -r /proc/meminfo ]]; then
  grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo || true
else
  printf 'MEMINFO_UNAVAILABLE\n'
fi
try_read uptime

section "Storage: bytes, inodes and filesystem"
try_read df -hP / /opt /var/lib/docker
try_read df -iP / /opt /var/lib/docker
try_read findmnt -no SOURCE,FSTYPE,OPTIONS /

section "Existing runtime (inspect only)"
try_read docker --version
try_read docker compose version
try_read systemctl is-active docker
try_read docker info --format 'Server={{.ServerVersion}} Cgroup={{.CgroupDriver}} Rootless={{.SecurityOptions}}'
try_read docker ps --format 'name={{.Names}} status={{.Status}} ports={{.Ports}}'

section "Port admission: 8080 is used only inside the UAES container"
if command -v ss >/dev/null 2>&1; then
  ss -ltnH | awk '$4 ~ /:(8080|8787)$/ {print $4}' || true
else
  printf 'PORT_INSPECT_UNAVAILABLE\n'
fi

section "Dedicated UAES path and user (do not create)"
if [[ -L /opt/uaes ]]; then
  printf 'BLOCKED: /opt/uaes is a symlink\n'
elif [[ -e /opt/uaes ]]; then
  printf 'PATH_PRESENT: /opt/uaes (must verify owner and contents before any use)\n'
else
  printf 'PATH_ABSENT: /opt/uaes\n'
fi
try_read stat -c '%n owner=%U group=%G mode=%a' /opt /var/lib/docker
if command -v getent >/dev/null 2>&1; then
  getent passwd uaes | cut -d: -f1,3,4,6,7 || true
  getent group docker | cut -d: -f1,3 || true
fi

section "Read-only preflight finished; no deployment attempted"
