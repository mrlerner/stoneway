#!/usr/bin/env bash
# Pull raw permit data for both corridors from the City of Seattle Building
# Permits open dataset (Socrata 76t5-zqzr). Re-run to refresh the snapshots
# (stoneway2.json, st45_2.json) that analyze.py reads. No API key needed.
set -euo pipefail

BASE="https://data.seattle.gov/resource/76t5-zqzr.json"
FIELDS="permitnum,originaladdress1,issueddate,completeddate,permitclass,permittypedesc,permittypemapped,housingunits,housingunitsadded,housingunitsremoved,statuscurrent,description,latitude,longitude"

echo "Fetching Stone Way N candidates..."
curl -s --max-time 90 "${BASE}?\$select=${FIELDS}&\$where=upper(originaladdress1)%20like%20'%25STONE%20WAY%20N%25'%20and%20(housingunitsadded%3E0%20or%20housingunitsremoved%3E0)&\$order=issueddate&\$limit=2000" -o stoneway2.json

echo "Fetching 45th St candidates..."
curl -s --max-time 90 "${BASE}?\$select=${FIELDS}&\$where=upper(originaladdress1)%20like%20'%2545TH%20ST%25'%20and%20(housingunitsadded%3E0%20or%20housingunitsremoved%3E0)&\$order=issueddate&\$limit=2000" -o st45_2.json

echo "Stone Way rows: $(grep -o permitnum stoneway2.json | wc -l)"
echo "45th St rows:   $(grep -o permitnum st45_2.json | wc -l)"
