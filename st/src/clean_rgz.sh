#!/bin/bash

set -euo pipefail

read -p "Remove all RGZ data? You will need to re-download them, which is slow? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo "Removing RGZ data"
rm -f data/rgz/download/*
rm -f data/rgz/csv/*
rm -f data/rgz/addresses.csv