#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d`
echo $current_date
tar -czf data/temp-report$current_date.tar.gz -C data/report/ .
scp data/temp-report$current_date.tar.gz kokanmain:/home/branko/ar/report$current_date.tar.gz
ssh kokanmain "tar -xzf /home/branko/ar/report$current_date.tar.gz -C /var/www/sites/dina.openstreetmap.rs/ar/"
ssh kokanmain "rm -f /home/branko/ar/report$current_date.tar.gz"

if [ "${AR_INCREMENTAL_UPDATE:-}" = "1" ]; then
  rm data/temp-report$current_date.tar.gz
else
  mv data/temp-report$current_date.tar.gz data/report$current_date.tar.gz
fi

rm -f data/running

echo "Done"
