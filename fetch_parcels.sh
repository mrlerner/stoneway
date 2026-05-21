#!/usr/bin/env bash
# Pull parcels (lot sizes + geometry) for both corridor segments from the King
# County parcel_address_area feature service. Geometry is requested in WA State
# Plane North (EPSG 2926, US feet) so frontage/depth can be measured directly.
set -euo pipefail
URL="https://gisdata.kingcounty.gov/arcgis/rest/services/OpenDataPortal/property__parcel_address_area/MapServer/1722/query"
OUT="PIN,ADDR_FULL,ADDR_NUM,LOTSQFT,PROPTYPE,PRIMARY_ADDR"

echo "Stone Way N (#3400-4499)..."
curl -s --max-time 90 -G "$URL" \
  --data-urlencode "where=ADDR_FULL LIKE '%STONE WAY N%' AND ADDR_NUM>=3400 AND ADDR_NUM<=4499 AND PRIMARY_ADDR=1" \
  --data-urlencode "outFields=$OUT" \
  --data-urlencode "returnGeometry=true" --data-urlencode "outSR=2926" \
  --data-urlencode "f=json" -o parcels_stoneway.json

echo "N/NE 45th St (I-5 .. Stone Way envelope)..."
curl -s --max-time 90 -G "$URL" \
  --data-urlencode "where=ADDR_FULL LIKE '%45TH ST%' AND PRIMARY_ADDR=1" \
  --data-urlencode "geometry=-122.343,47.659,-122.3235,47.663" \
  --data-urlencode "geometryType=esriGeometryEnvelope" --data-urlencode "inSR=4326" \
  --data-urlencode "spatialRel=esriSpatialRelIntersects" \
  --data-urlencode "outFields=$OUT" \
  --data-urlencode "returnGeometry=true" --data-urlencode "outSR=2926" \
  --data-urlencode "f=json" -o parcels_45th.json

echo "Stone Way parcels: $(grep -o PIN parcels_stoneway.json | wc -l)"
echo "45th parcels:      $(grep -o PIN parcels_45th.json | wc -l)"
