docker run -it \
  -e PBF_URL=https://download.geofabrik.de/north-america/us/indiana-latest.osm.pbf \
  -e REPLICATION_URL=https://download.geofabrik.de/north-america/us/indiana-updates/ \
  -e IMPORT_TIGER_ADDRESSES=/nominatim/tiger-nominatim-preprocessed.csv.tar.gz \
  -e IMPORT_US_POSTCODES=true \
  -p 8080:8080 \
  -v /indiana_tiger:/nominatim/ \
  --name nominatim \
  mediagis/nominatim:4.5