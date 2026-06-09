#!/bin/bash

INSTALL_DIR="/opt/${sanitizedProductName}"
EXEC="${executable}"
LAUNCHER="$INSTALL_DIR/$EXEC-launcher"
DESKTOP_FILE="/usr/share/applications/$EXEC.desktop"

# Wrapper ensures sandbox is disabled even when launched via symlink or terminal.
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
export ELECTRON_DISABLE_SANDBOX=1
exec "$(dirname "$(readlink -f "$0")")/EXEC_PLACEHOLDER" --no-sandbox --disable-setuid-sandbox "$@"
LAUNCHER_EOF
sed -i "s/EXEC_PLACEHOLDER/$EXEC/" "$LAUNCHER"
chmod 755 "$LAUNCHER"

# Electron requires chrome-sandbox to be root-owned with the SUID bit on deb installs.
if [ -f "$INSTALL_DIR/chrome-sandbox" ]; then
  chown root:root "$INSTALL_DIR/chrome-sandbox"
  chmod 4755 "$INSTALL_DIR/chrome-sandbox"
fi

if type update-alternatives 2>/dev/null >&1; then
  if [ -L "/usr/bin/$EXEC" ] && [ -e "/usr/bin/$EXEC" ] && [ "$(readlink "/usr/bin/$EXEC")" != "/etc/alternatives/$EXEC" ]; then
    rm -f "/usr/bin/$EXEC"
  fi
  update-alternatives --install "/usr/bin/$EXEC" "$EXEC" "$LAUNCHER" 100 || ln -sf "$LAUNCHER" "/usr/bin/$EXEC"
else
  ln -sf "$LAUNCHER" "/usr/bin/$EXEC"
fi

if [ -f "$DESKTOP_FILE" ]; then
  sed -i "s|^Exec=.*|Exec=$LAUNCHER %U|" "$DESKTOP_FILE"
fi

if hash update-mime-database 2>/dev/null; then
  update-mime-database /usr/share/mime || true
fi

if hash update-desktop-database 2>/dev/null; then
  update-desktop-database /usr/share/applications || true
fi