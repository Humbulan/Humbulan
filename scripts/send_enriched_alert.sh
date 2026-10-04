#!/bin/bash
MSG="$1"
ENRICHED=$(echo "$MSG" | python3 -c "
import sys, requests, json
msg = sys.stdin.read()
if len(msg) < 50:
    print(msg); sys.exit(0)
prompt = f\"Enrich the following alert with context and possible causes, keep it concise:\n{msg}\"
try:
    r = requests.post('http://localhost:3002/v1/chat/completions',
        headers={'Content-Type':'application/json','Authorization':'Bearer freellmapi-fbc1b7fc53a2e9e1f78616c804557cb2ac7c4e4b9599d986'},
        json={'model':'auto','messages':[{'role':'user','content':prompt}]}, timeout=10)
    if r.status_code == 200:
        print(r.json()['choices'][0]['message']['content'])
    else:
        print(msg)
except:
    print(msg)
")
~/imperial_network/scripts/send_alert.sh "$ENRICHED"
