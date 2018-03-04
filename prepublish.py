
import os 

#download data 
os.system("curl -o cb_2016_19_tract_500k.zip https://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_19_tract_500k.zip")

#unzip the data
os.system("unzip -o cb_2016_19_tract_500k.zip")

#use shp2json to convert to GeoJSON
os.system("shp2json cb_2016_19_tract_500k.shp -o iowa.json")

#use projection
os.system("geoproject 'd3.geoConicConformal().parallels([42 + 4 / 60, 43 + 16 / 60]).rotate([93 + 30 / 60, 0]).fitSize([960, 960], d)' < iowa.json > iowa-albers.json")

#create svg
os.system("geo2svg -w 960 -h 960 < iowa-albers.json > iowa-albers.svg")

#To convert a GeoJSON feature collection to a newline-delimited stream of GeoJSON features, use ndjson-split:
os.system("ndjson-split 'd.features' \
  < iowa-albers.json \
  > iowa-albers.ndjson")

os.system("ndjson-map 'd.id = d.properties.GEOID.slice(2), d' \
  < iowa-albers.ndjson \
  > iowa-albers-id.ndjson")

#download
os.system("curl 'https://api.census.gov/data/2016/acs/acs5?get=B01003_001E&for=tract:*&in=state:19' -o cb_2016_19_tract_B01003.json")

#To convert it to an NDJSON stream
os.system("ndjson-cat cb_2016_19_tract_B01003.json \
  | ndjson-split 'd.slice(1)' \
  | ndjson-map '{id: d[2] + d[3], B01003: +d[0]}' \
  > cb_2016_19_tract_B01003.ndjson")

#Join the population data to the geometry using ndjson-join
os.system("ndjson-join 'd.id' \
  iowa-albers-id.ndjson \
  cb_2016_19_tract_B01003.ndjson \
  > iowa-albers-join.ndjson")

#
os.system("ndjson-map 'd[0].properties = {density: Math.floor(d[1].B01003 / d[0].properties.ALAND * 2589975.2356)}, d[0]' \
  < iowa-albers-join.ndjson \
  > iowa-albers-density.ndjson")


os.system("ndjson-reduce 'p.features.push(d), p' '{type: \"FeatureCollection\", features: []}' \
  < iowa-albers-density.ndjson \
  > iowa-albers-density.json")

os.system("ndjson-map -r d3 \
  '(d.properties.fill = d3.scaleSequential(d3.interpolateViridis).domain([0, 4000])(d.properties.density), d)' \
  < iowa-albers-density.ndjson \
  > iowa-albers-color.ndjson")

os.system("geo2svg -n --stroke none -p 1 -w 960 -h 960 \
  < iowa-albers-color.ndjson \
  > iowa-albers-color.svg")

os.system("geo2topo -n \
  tracts=iowa-albers-density.ndjson \
  > iowa-tracts-topo.json")

os.system("toposimplify -p 1 -f \
  < iowa-tracts-topo.json \
  > iowa-simple-topo.json")

os.system("topoquantize 1e5 \
  < iowa-simple-topo.json \
  > iowa-quantized-topo.json")

os.system("topomerge -k 'd.id.slice(0, 3)' counties=tracts \
  < iowa-quantized-topo.json \
  > iowa-merge-topo.json")

os.system("topomerge --mesh -f 'a !== b' counties=counties \
  < iowa-merge-topo.json \
  > iowa-topo.json")