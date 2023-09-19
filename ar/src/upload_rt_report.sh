#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d%H%M`
echo $current_date
tar -czf data/rt-report$current_date.tar.gz -C data/report/rt/ .
scp -l 5000 data/rt-report$current_date.tar.gz kokanovic:/home/branko/ar/rt-report$current_date.tar.gz
ssh kokanovic "tar -xzf /home/branko/ar/rt-report$current_date.tar.gz -C /var/www/sites/dina.openstreetmap.rs/ar/rt/"
ssh kokanovic "rm -f /home/branko/ar/rt-report$current_date.tar.gz"

rm -f data/rt-report$current_date.tar.gz

rm -f data/running

echo "Done"
