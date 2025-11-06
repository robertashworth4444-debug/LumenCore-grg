#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
BASE=/opt/lumen-core
OUTDIR="$BASE/reports"
YMD=$(date -u +%F)
LOCK="$OUTDIR/.rollup_${YMD}.lock"
mkdir -p "$OUTDIR"
exec 9>"$LOCK"
flock -n 9 || exit 0
START_TS=$(date -u -d "yesterday 00:00:00" +%s)
END_TS=$(date -u -d "yesterday 23:59:59" +%s)
rollup_one () {
  local cdir="$1"; local cname="$(basename "$cdir")"
  local p="$cdir/trials.log"; local gz=( "$cdir"/trials.log*.gz )
  [ -f "$p" ] || { shopt -s nullglob; [ ${#gz[@]} -gt 0 ] || return 0; shopt -u nullglob; }
  awk -v s="$START_TS" -v e="$END_TS" '
    function bump(line,   t){
      if (match(line,/"ts"[[:space:]]*:[[:space:]]*([0-9]+)/,m)){
        t=m[1]+0; if (t<s||t>e) return
        total++; if (first==0||t<first) first=t; if (t>last) last=t
        if (line ~ /"path_ok"[[:space:]]*:[[:space:]]*true/) ok++
        if (line ~ /[Pp][Rr][Oo][Mm][Oo][Tt][Ee][Dd]/) champs++
      }
    }
    { bump($0) }
    END{
      if (!total){ print "0,0,0,0" > "/dev/stderr"; exit 0 }
      dt=(last>first)?(last-first):0; ratio=(total?ok/total:0.0)
      printf("%d,%f,%d,%d\n",total,ratio,champs,dt)
    }
  ' < <( [ -f "$p" ] && cat "$p"; shopt -s nullglob; for z in "$cdir"/trials.log*.gz; do zcat -- "$z"; done ) \
    >"$OUTDIR/.roll_${cname}.stats" 2>/dev/null || true
  [ -s "$OUTDIR/.roll_${cname}.stats" ] || return 0
  IFS=',' read -r total ratio champs dt <"$OUTDIR/.roll_${cname}.stats"
  local out="$OUTDIR/${YMD}_${cname}.csv"
  echo "date,colony,trials,ok_ratio,champions,window_s" > "$out"
  printf "%s,%s,%s,%.6f,%s,%s\n" "$YMD" "$cname" "$total" "$ratio" "$champs" "$dt" >> "$out"
  rm -f "$OUTDIR/.roll_${cname}.stats"
}
for c in "$BASE"/storage/colony-*; do [ -d "$c" ] && rollup_one "$c"; done
summary="$OUTDIR/${YMD}_summary.csv"
echo "date,colony,trials,ok_ratio,champions,window_s" > "$summary"
cat "$OUTDIR"/${YMD}_colony-*.csv >> "$summary" 2>/dev/null || true
chmod 0644 "$summary" "$OUTDIR"/${YMD}_colony-*.csv 2>/dev/null || true
