#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d`
echo $current_date
tar -czf data/temp-report$current_date.tar.gz -C data/report/ .
scp data/temp-report$current_date.tar.gz kokanovic:/home/branko/st/report$current_date.tar.gz
ssh kokanovic "tar -xzf /home/branko/st/report$current_date.tar.gz -C /var/www/sites/dina.openstreetmap.rs/st/"
ssh kokanovic "rm -f /home/branko/st/report$current_date.tar.gz"

mv data/temp-report$current_date.tar.gz data/report$current_date.tar.gz

rm -f data/running