#!/usr/bin/env bash
set -e

echo "========================================"
echo "  KDK Website – Testserver"
echo "  http://localhost:8080/"
echo "  Beenden: Strg+C"
echo "========================================"
echo

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Fehler: Python nicht gefunden. Bitte Python installieren."
  exit 1
fi

# Bundler im Hintergrund mit Dateiüberwachung starten
python3 bundler.py --watch &
BUNDLER_PID=$!

# HTTP-Server starten
python3 -m http.server 8080

# Bundler beenden wenn der Server stoppt
kill "$BUNDLER_PID" 2>/dev/null

read -r -p "Beendet. Enter drücken zum Schließen..." _
