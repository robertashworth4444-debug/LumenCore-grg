#!/usr/bin/env bash
set -euo pipefail
SRC=/root/uploads
PUB_DOCS=/var/www/lumen-core/docs
PUB_INV=/var/www/lumen-core/investors
PUB_REL=/var/www/lumen-core.ai/research/complete
LOG=/var/log/lumencore_publish.log

ts(){ date -u +"%Y-%m-%d %H:%M:%S UTC"; }

echo "[$(ts)] --- LumenCore publish cycle ---" >> "$LOG"

# 1) Move new uploads to public destinations by type
shopt -s nullglob
moved=0

# Research docs to /docs
for f in "$SRC"/*.{pdf,doc,docx,ppt,pptx,xls,xlsx,csv,txt,png,jpg,jpeg,svg,webp}; do
  mv -f "$f" "$PUB_DOCS/" && echo "[$(ts)] -> docs: $(basename "$f")" >> "$LOG" && moved=1
done

# Investor assets to /investors (if operator drops them in uploads)
for f in "$SRC"/{product.html,LumenCore_Product_Sheet.pdf,LumenCore_Deck*.pdf,LumenCore_Dossier*.pdf}; do
  [ -e "$f" ] || continue
  mv -f "$f" "$PUB_INV/" && echo "[$(ts)] -> investors: $(basename "$f")" >> "$LOG" && moved=1
done

# Archives (zip/tar) directly to /research/complete
for f in "$SRC"/*.{zip,tar,tgz,gz}; do
  mv -f "$f" "$PUB_REL/" && echo "[$(ts)] -> releases: $(basename "$f")" >> "$LOG" && moved=1
done
shopt -u nullglob

# 2) Build a timestamped release ZIP of the current /docs set (if anything moved)
if [ "$moved" = 1 ]; then
  rel="$PUB_REL/lumencore_release_$(date -u +%Y%m%d_%H%M).zip"
  (cd "$PUB_DOCS" && zip -qr "$rel" .) || true
  echo "[$(ts)] + release: $(basename "$rel")" >> "$LOG"
fi

# 3) Clean zero-byte files (mobile uploads sometimes create these)
find "$PUB_REL" -type f -size 0 -delete
find "$PUB_DOCS" -type f -size 0 -delete

# 4) Fix permissions
chown -R www-data:www-data "$PUB_DOCS" "$PUB_INV" "$PUB_REL"
chmod -R 755 "$PUB_DOCS" "$PUB_INV" "$PUB_REL"

# 5) Rebuild docs gallery if present
if [ -x /usr/local/bin/build_docs_gallery.sh ]; then
  /usr/local/bin/build_docs_gallery.sh >> "$LOG" 2>&1 || true
fi

# 6) Reload nginx if installed
if command -v nginx >/dev/null 2>&1; then
  nginx -t && systemctl reload nginx && echo "[$(ts)] nginx reloaded" >> "$LOG" || echo "[$(ts)] nginx test failed" >> "$LOG"
fi

echo "[$(ts)] ✓ publish cycle complete" >> "$LOG"
