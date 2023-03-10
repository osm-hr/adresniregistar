#!/bin/bash

set -euo pipefail

current_date=`date +%Y%m%d`
echo $current_date
tar -czf data/report$current_date.tar.gz -C data/report/ .
scp data/report$current_date.tar.gz kokanovic:/home/branko/ar
ssh kokanovic "tar -xzf ar/report$current_date.tar.gz -C /var/www/sites/openstreetmap.rs/download/ar/"

