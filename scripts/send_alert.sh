#!/bin/bash
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: send_alert.sh \"Your alert message\""
    exit 1
fi

# 1) Send to webhook (Slack/Discord) via existing notify.sh
if [ -x ~/imperial_network/scripts/notify.sh ]; then
    ~/imperial_network/scripts/notify.sh "$MESSAGE"
fi

# 2) Send WhatsApp via imperial-whatsapp.sh
if [ -x ~/imperial-whatsapp.sh ]; then
    ~/imperial-whatsapp.sh send 27794658481 "$MESSAGE"
fi

# (Optional) Add other channels here if needed
echo "✅ Alert sent via all channels."
