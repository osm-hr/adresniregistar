#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d`
echo $current_date
tar -czf data/report$current_date.tar.gz -C data/report/ .
scp data/report$current_date.tar.gz kokanovic:/home/branko/ar/report$current_date.tar.gz
ssh kokanovic "tar -xzf /home/branko/ar/report$current_date.tar.gz -C /var/www/sites/openstreetmap.rs/download/ar/"
ssh kokanovic "rm -f /home/branko/ar/report$current_date.tar.gz"

