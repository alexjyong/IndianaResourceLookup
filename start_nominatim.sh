docker run -it \
  -e PBF_URL=https://download.geofabrik.de/north-america/us/indiana-latest.osm.pbf \
  -e REPLICATION_URL=https://download.geofabrik.de/north-america/us/indiana-updates/ \
  -p 8080:8080 \
  --name nominatim \
  mediagis/nominatim:4.4 