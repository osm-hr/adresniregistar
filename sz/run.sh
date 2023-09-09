#!/bin/bash

set -euo pipefail

rm -f output/*
rm -f sz_analysis.csv

python3 src/sz_analysis.py --data-path $1
python3 src/report.py

current_date=`date +%Y%m%d`
echo $current_date
tar -czf temp-report$current_date.tar.gz -C output/ .
scp temp-report$current_date.tar.gz kokanovic:/home/branko/dina/sz-report$current_date.tar.gz
ssh kokanovic "tar -xzf /home/branko/dina/sz-report$current_date.tar.gz -C /var/www/sites/dina.openstreetmap.rs/sz/"
ssh kokanovic "rm -f /home/branko/dina/sz-report$current_date.tar.gz"

mv temp-report$current_date.tar.gz sz-report$current_date.tar.gz

curl -X POST \
        -H 'Content-Type: application/json' \
        -d '{"chat_id": '$TELEGRAM_CHAT_ID', "text": "SZ report uploaded"}' \
        https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage
echo