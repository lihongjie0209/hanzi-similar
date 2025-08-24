#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="hanzi-similar"
ENV_FILE="/etc/${SERVICE_NAME}.env"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Resolve repo root (script dir/..)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "[i] Elevating privileges with sudo..."
    exec sudo -E bash "$0" "$@"
  fi
}

usage() {
  cat <<EOF
Usage: $0 [install|uninstall|status]

install   Install and start ${SERVICE_NAME} systemd service
uninstall Stop, disable and remove the service and env file
status    Show systemd status
EOF
}

install_service() {
  echo "[i] Installing ${SERVICE_NAME} from: $REPO_DIR"

  # Create env file if missing; use absolute paths for reliability
  if [[ ! -f "$ENV_FILE" ]]; then
    cat <<EOF > "$ENV_FILE"
# ${SERVICE_NAME} environment configuration
# Adjust and systemctl restart ${SERVICE_NAME} after changes.
HOST=0.0.0.0
PORT=8000
IMAGES_DIR=${REPO_DIR}/images
CHROMA_DB_PATH=${REPO_DIR}/chroma_db
FONTS_DIR=${REPO_DIR}/fonts
MODEL_NAME=google/vit-base-patch16-224
TOP_K=10
BUILD_DB=0
# Avoid uv cache under /root in systemd; start.sh will fall back to python
USE_UV=0
EOF
    chmod 0644 "$ENV_FILE"
    echo "[i] Created $ENV_FILE"
  else
    echo "[i] Using existing $ENV_FILE"
  fi

  # Create systemd unit
  cat <<EOF > "$UNIT_FILE"
[Unit]
Description=Hanzi Similar Search (FastAPI + ChromaDB)
After=network-online.target
Wants=network-online.target
[Service]

User=root
Type=simple
WorkingDirectory=${REPO_DIR}
EnvironmentFile=${ENV_FILE}
Environment=PYTHONUNBUFFERED=1
# Provide writable HOME/cache so tools won't hit /root when ProtectHome=true
Environment=HOME=/var/lib/${SERVICE_NAME}
Environment=XDG_CACHE_HOME=/var/lib/${SERVICE_NAME}/.cache
Environment=UV_CACHE_DIR=/var/lib/${SERVICE_NAME}/.cache/uv
ExecStart=/usr/bin/env sh ${REPO_DIR}/scripts/start.sh
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
# Let systemd create persistent writable dirs under /var
StateDirectory=${SERVICE_NAME}
CacheDirectory=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

  chmod 0644 "$UNIT_FILE"
  echo "[i] Wrote unit: $UNIT_FILE"

  # Reload and enable
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"
  systemctl --no-pager --full status "$SERVICE_NAME" || true

  echo
  echo "[✓] Installed and started ${SERVICE_NAME}."
  echo "[i] Logs: journalctl -u ${SERVICE_NAME} -f"
}

uninstall_service() {
  echo "[i] Uninstalling ${SERVICE_NAME}..."
  systemctl stop "$SERVICE_NAME" || true
  systemctl disable "$SERVICE_NAME" || true
  rm -f "$UNIT_FILE"
  systemctl daemon-reload
  echo "[i] Removed unit file: $UNIT_FILE"
  if [[ -f "$ENV_FILE" ]]; then
    rm -f "$ENV_FILE"
    echo "[i] Removed env file: $ENV_FILE"
  fi
  echo "[✓] Uninstalled."
}

show_status() {
  systemctl --no-pager --full status "$SERVICE_NAME" || true
}

main() {
  local action="${1:-install}"
  case "$action" in
    install)
      require_root "$@"; install_service ;;
    uninstall)
      require_root "$@"; uninstall_service ;;
    status)
      show_status ;;
    *)
      usage; exit 1 ;;
  esac
}

main "$@"
