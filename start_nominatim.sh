docker run -it \
  -e PBF_URL=https://download.geofabrik.de/north-america/us/indiana-latest.osm.pbf \
  -e REPLICATION_URL=https://download.geofabrik.de/north-america/us/indiana-updates/ \
  -e IMPORT_TIGER_ADDRESSES=/nominatim/data/indiana.tar.gz \
  -e IMPORT_US_POSTCODES=true \
  -p 8080:8080 \
  -v /indiana_tiger:/nominatim/data \
  --name nominatim \
  mediagis/nominatim:4.5 