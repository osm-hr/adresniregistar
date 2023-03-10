#!/bin/bash

set -euo pipefail

curl -X POST \
        -H 'Content-Type: application/json' \
        -d '{"chat_id": '$TELEGRAM_CHAT_ID', "text": "AR report uploaded"}' \
        https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage
echo