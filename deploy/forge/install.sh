#!/usr/bin/env bash
#
# install.sh: install or update the public aiml-calc web UI inside the forge machine.
#
# Why it exists: aiml.dannypenrose.com needs a Linux user, a clone of this (public) repo, a
# Python virtual environment, a hardened systemd unit and an Nginx site, made the same way every
# time and safe to run twice.
#
# Runs in: the forge machine (Ubuntu 24.04, arm64, Bash 5), as root. Do not run it directly:
# deploy/forge-setup.sh on the server Mac copies this folder into forge and runs it through orb.
#
# Usage (through the wrapper):
#   deploy/forge-setup.sh             plan only: checks everything and prints what it would do
#   deploy/forge-setup.sh --apply     install (or repair) everything, then smoke test
#   deploy/forge-setup.sh --update    pull main, reinstall dependencies, restart, smoke test
#
# What it makes (each only when missing or different):
#   - system user and group aiml (no login shell), home /var/www/aiml-calc/home
#   - /var/www/aiml-calc/app: a shallow clone of https://github.com/dannypenrose/aiml-calc (main)
#   - /var/www/aiml-calc/venv: Python venv with requirements.txt installed
#   - /etc/systemd/system/aiml-calc.service (Streamlit on 127.0.0.1:3090, AIML_CALC_PUBLIC=1)
#   - /etc/nginx/sites-available/aiml-calc, linked from sites-enabled, checked with nginx -t
#
# Safety rails:
#   - The default is a plan that changes nothing.
#   - Refuses if port 3090 is used by anything other than aiml-calc, or another Nginx site already
#     answers for aiml.dannypenrose.com.
#   - Replaces a config file only when its content differs, and keeps a .bak of the old one.
#   - Nginx is reloaded only after nginx -t passes; a failing test restores the old site file.
#   - No secrets: the repo is public and the app needs no keys.
#
# Exit codes: 0 success, 1 failure or refused, 2 usage error.

set -Eeuo pipefail

APP="aiml-calc"
APP_USER="aiml"
HOSTNAME_PUBLIC="aiml.dannypenrose.com"
PORT="3090"
REPO_URL="https://github.com/dannypenrose/aiml-calc.git"
BRANCH="main"
BASE="/var/www/aiml-calc"
APP_DIR="$BASE/app"
VENV="$BASE/venv"
HOME_DIR="$BASE/home"
UNIT_DEST="/etc/systemd/system/$APP.service"
NGINX_AVAILABLE="/etc/nginx/sites-available/$APP"
NGINX_ENABLED="/etc/nginx/sites-enabled/$APP"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

info() { printf '  %s\n' "$*"; }
ok()   { printf '  ok   %s\n' "$*"; }
plan() { printf '  plan %s\n' "$*"; }
warn() { printf '  warn %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
trap 'die "failed at line $LINENO: $BASH_COMMAND"' ERR

MODE="plan"
case "${1:-}" in
  "") ;;
  --apply) MODE="apply" ;;
  --update) MODE="update" ;;
  -h|--help) sed -n '12,15p' "$0"; exit 0 ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; sed -n '12,15p' "$0" >&2; exit 2 ;;
esac

as_app() { runuser -u "$APP_USER" -- env HOME="$HOME_DIR" "$@"; }

# install_file <source> <dest> <mode>: replace dest only when different; prints what happened.
# Returns 0 when it changed the file, 1 when it was already current.
install_file() {
  local src="$1" dest="$2" mode="$3"
  if [[ -f "$dest" ]] && cmp -s "$src" "$dest"; then
    ok "$dest is current"
    return 1
  fi
  if [[ "$MODE" == "plan" ]]; then
    plan "write $dest"
    return 1
  fi
  if [[ -f "$dest" ]]; then
    cp -p "$dest" "$dest.bak"
    info "kept the old file as $dest.bak"
  fi
  install -m "$mode" -o root -g root "$src" "$dest"
  ok "wrote $dest"
  return 0
}

printf '%s on forge: %s\n' "$APP" "$MODE"

# --- Preflight -----------------------------------------------------------------------------
[[ "$(id -u)" -eq 0 ]] || die "run as root (the wrapper uses orb -m forge -u root)"
[[ -f "$SRC_DIR/aiml-calc.service" && -f "$SRC_DIR/aiml-calc.nginx.conf" ]] \
  || die "aiml-calc.service and aiml-calc.nginx.conf must sit beside this script"
command -v nginx >/dev/null || die "nginx is not installed in this machine"
command -v python3 >/dev/null || die "python3 is not installed in this machine"
py_ok="$(python3 -c 'import sys; print(int(sys.version_info >= (3, 10)))')"
[[ "$py_ok" == "1" ]] || die "python3 is $(python3 -V 2>&1); aiml-calc needs 3.10 or later"
ok "$(python3 -V 2>&1), nginx $(nginx -v 2>&1 | sed 's/.*\///')"

port_owner="$(ss -ltnpH "sport = :$PORT" 2>/dev/null || true)"
if [[ -n "$port_owner" ]]; then
  if systemctl is-active --quiet "$APP" && printf '%s' "$port_owner" | grep -q python; then
    ok "port $PORT is aiml-calc's own"
  else
    die "port $PORT is already in use: $port_owner"
  fi
else
  ok "port $PORT is free"
fi

other_site="$(grep -rlsE "server_name[^;]*aiml\\.dannypenrose\\.com" /etc/nginx/sites-enabled/ | grep -v "/$APP\$" || true)"
[[ -z "$other_site" ]] || die "another Nginx site already answers for $HOSTNAME_PUBLIC: $other_site"

# --- Packages ------------------------------------------------------------------------------
missing=()
python3 -c 'import ensurepip' 2>/dev/null || missing+=("python3-venv")
command -v git >/dev/null || missing+=("git")
if ((${#missing[@]})); then
  if [[ "$MODE" == "plan" ]]; then
    plan "apt-get install ${missing[*]}"
  else
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}" >/dev/null
    ok "installed ${missing[*]}"
  fi
else
  ok "python3-venv and git are installed"
fi

# --- User and folders ----------------------------------------------------------------------
if id "$APP_USER" &>/dev/null; then
  ok "user $APP_USER exists"
elif [[ "$MODE" == "plan" ]]; then
  plan "create system user $APP_USER (no login shell, home $HOME_DIR)"
else
  useradd --system --user-group --home-dir "$HOME_DIR" --shell /usr/sbin/nologin "$APP_USER"
  ok "created user $APP_USER"
fi

if [[ "$MODE" == "plan" ]]; then
  [[ -d "$BASE" ]] && ok "$BASE exists" || plan "create $BASE/{app,venv,home} owned by $APP_USER"
else
  install -d -m 755 -o "$APP_USER" -g "$APP_USER" "$BASE" "$HOME_DIR"
fi

# --- Code ----------------------------------------------------------------------------------
if [[ -d "$APP_DIR/.git" ]]; then
  if [[ "$MODE" == "plan" ]]; then
    plan "keep $APP_DIR at $(as_app git -C "$APP_DIR" rev-parse --short HEAD) (--update pulls $BRANCH)"
  elif [[ "$MODE" == "update" ]]; then
    before="$(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
    as_app git -C "$APP_DIR" fetch --quiet --depth 1 origin "$BRANCH"
    as_app git -C "$APP_DIR" reset --quiet --hard FETCH_HEAD
    ok "code $before -> $(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
  else
    ok "code at $(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
  fi
elif [[ "$MODE" == "plan" ]]; then
  plan "clone $REPO_URL ($BRANCH) into $APP_DIR"
else
  as_app git clone --quiet --depth 1 --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  ok "cloned $REPO_URL at $(as_app git -C "$APP_DIR" rev-parse --short HEAD)"
fi

# --- Python environment --------------------------------------------------------------------
if [[ "$MODE" == "plan" ]]; then
  [[ -x "$VENV/bin/python" ]] && ok "venv exists" || plan "create venv $VENV"
  plan "pip install -r $APP_DIR/requirements.txt"
else
  [[ -x "$VENV/bin/python" ]] || as_app python3 -m venv "$VENV"
  as_app "$VENV/bin/pip" install --quiet --upgrade pip
  as_app "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
  ok "dependencies installed (streamlit $(as_app "$VENV/bin/python" -c 'import streamlit; print(streamlit.__version__)'))"
fi

# --- systemd -------------------------------------------------------------------------------
unit_changed=0
install_file "$SRC_DIR/aiml-calc.service" "$UNIT_DEST" 644 && unit_changed=1
if [[ "$MODE" != "plan" ]]; then
  ((unit_changed)) && systemctl daemon-reload
  systemctl enable --quiet "$APP"
  systemctl restart "$APP"
  ok "$APP enabled and restarted"
else
  plan "enable and restart $APP"
fi

# --- Nginx ---------------------------------------------------------------------------------
nginx_changed=0
install_file "$SRC_DIR/aiml-calc.nginx.conf" "$NGINX_AVAILABLE" 644 && nginx_changed=1
if [[ -L "$NGINX_ENABLED" ]]; then
  ok "$NGINX_ENABLED is linked"
elif [[ "$MODE" == "plan" ]]; then
  plan "link $NGINX_ENABLED"
else
  ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
  nginx_changed=1
  ok "linked $NGINX_ENABLED"
fi
if ((nginx_changed)); then
  if nginx -t 2>/dev/null; then
    systemctl reload nginx
    ok "nginx -t passed; Nginx reloaded"
  else
    nginx -t || true
    if [[ -f "$NGINX_AVAILABLE.bak" ]]; then
      mv "$NGINX_AVAILABLE.bak" "$NGINX_AVAILABLE"
    else
      rm -f "$NGINX_ENABLED" "$NGINX_AVAILABLE"
    fi
    die "nginx -t failed; the previous Nginx config is back in place and Nginx was not reloaded"
  fi
fi

# --- Smoke test ----------------------------------------------------------------------------
if [[ "$MODE" == "plan" ]]; then
  printf '\nPlan only: nothing was changed. Run with --apply to install.\n'
  exit 0
fi

healthy=0
for _ in $(seq 1 30); do
  if [[ "$(curl -fsS "http://127.0.0.1:$PORT/_stcore/health" 2>/dev/null || true)" == "ok" ]]; then
    healthy=1
    break
  fi
  sleep 1
done
((healthy)) || die "Streamlit did not become healthy on port $PORT: journalctl -u $APP -n 50"
ok "Streamlit is healthy on 127.0.0.1:$PORT"

via_nginx="$(curl -fsS -H "Host: $HOSTNAME_PUBLIC" "http://127.0.0.1/healthz" 2>/dev/null || true)"
[[ "$via_nginx" == "ok" ]] || die "Nginx does not reach the app for $HOSTNAME_PUBLIC (got '${via_nginx:-nothing}')"
ok "Nginx serves $HOSTNAME_PUBLIC"

printf '\nDone: https://%s\n' "$HOSTNAME_PUBLIC"
