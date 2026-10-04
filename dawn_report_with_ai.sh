#!/bin/bash
REPORT=$(~/imperial_network/dawn_report_enhanced.sh 2>&1)
echo "$REPORT"
# The original script already sends WhatsApp alert. Now send AI summary as extra.
SUMMARY=$(echo "$REPORT" | python3 ~/imperial_network/llm_summarise.py)
~/imperial_network/scripts/send_alert.sh "🤖 AI Executive Summary:\n$SUMMARY"
