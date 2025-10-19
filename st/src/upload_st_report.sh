#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d`
echo $current_date
tar -czf data/temp-report$current_date.tar.gz -C data/report/ .
scp data/temp-report$current_date.tar.gz kokanmain:/home/branko/st/report$current_date.tar.gz
ssh kokanmain "tar -xzf /home/branko/st/report$current_date.tar.gz -C /var/www/sites/dina.openstreetmap.rs/st/"
ssh kokanmain "rm -f /home/branko/st/report$current_date.tar.gz"

mv data/temp-report$current_date.tar.gz data/st-report$current_date.tar.gz

rm -f data/running

echo "Done"
