#!/usr/bin/env bash
# Demo driver — feeds the tailed log on a timer so you can narrate instead of typing.
# Run in Terminal 3 AFTER the agent is up.  Usage: bash drive.sh [logfile]
set -u
LOG="${1:-demo_logs/Fix.log}"
mkdir -p "$(dirname "$LOG")"; : >> "$LOG"

say() { printf '\n\033[1;36m>>> %s\033[0m\n' "$1"; }

say "BEAT 1  (idle)  — heartbeats keep coming with no log activity. Watch ~10s."
sleep 10

say "BEAT 2  — a real FIX order arrives.  readLagMs appears, state -> reading"
printf '8=FIX.4.2|9=61|35=D|49=CLIENT|56=BROKER|11=ORD-1001|55=ABC|54=1|38=100|44=50.00|10=072|\n' >> "$LOG"
sleep 6

say "BEAT 3  — nothing written for >5s.  status -> degraded, reason names the file"
sleep 8

say "BEAT 4  — a line the parser cannot classify (MsgType ZZ).  parseErrorCountLast5Min -> 1, status -> unhealthy"
printf '8=FIX.4.2|9=61|35=ZZ|11=ORD-9999|10=072|\n' >> "$LOG"
sleep 8

say "BEAT 5  — clean traffic resumes.  the rate decays, status recovers"
for i in 1 2 3 4 5 6 7 8 9 10; do
  printf '8=FIX.4.2|9=61|35=D|49=CLIENT|56=BROKER|11=ORD-20%02d|55=ABC|54=1|38=100|44=50.00|10=072|\n' "$i" >> "$LOG"
done
sleep 8

say "done — Ctrl-C the agent when you're ready"
