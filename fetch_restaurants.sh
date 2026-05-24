#!/usr/bin/env bash
# Pull raw food-establishment inspection records for both corridors from King
# County Public Health's "Food Establishment Inspection Data" open dataset
# (Socrata f29f-zza5). Re-run to refresh the snapshots that
# analyze_restaurants.py reads. No API key needed.
#
# Why inspection data? Every operating restaurant in King County must hold a
# food-service permit and is inspected ~1-2x/year. The span of inspection dates
# for an establishment is a close proxy for the years it was open -- which lets
# us count restaurants OPEN per year (a stock), not just new openings.
set -euo pipefail

BASE="https://data.kingcounty.gov/resource/f29f-zza5.json"
FIELDS="name,program_identifier,business_id,inspection_date,description,address,city,zip_code,longitude,latitude,inspection_closed_business,inspection_result,inspection_type"

echo "Fetching Stone Way N food establishments..."
curl -s --max-time 90 "${BASE}?\$select=${FIELDS}&\$where=upper(address)%20like%20'%25STONE%20WAY%20N%25'&\$order=inspection_date&\$limit=5000" -o rest_stoneway.json

echo "Fetching 45th St food establishments..."
curl -s --max-time 90 "${BASE}?\$select=${FIELDS}&\$where=upper(address)%20like%20'%2545TH%20ST%25'&\$order=inspection_date&\$limit=5000" -o rest_45th.json

echo "Stone Way rows: $(grep -o business_id rest_stoneway.json | wc -l)"
echo "45th St rows:   $(grep -o business_id rest_45th.json | wc -l)"
