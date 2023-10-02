import ee
import geemap
# https://developers.google.com/earth-engine/datasets/catalog/USDOS_LSIB_SIMPLE_2017#table-schema
# continents
#     oceania not included due to number of polygons required
africa = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('wld_rgn', 'equals', 'Africa').set('aoi_label', 'africa')
europe = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('wld_rgn', 'equals', 'Europe').set('aoi_label', 'europe')
northAmerica = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('wld_rgn', 'equals', 'North America').set('aoi_label', 'north_america')
southAmerica = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('wld_rgn', 'equals', 'South America').set('aoi_label', 'south_america')

# specific countries of interest
argentina = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'AR').set('aoi_label', 'argentina')
australia = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'AS').set('aoi_label', 'australia')
brazil = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'BR').set('aoi_label', 'brazil')
chile = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'CI').set('aoi_label', 'chile')
new_zealand = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'NZ').set('aoi_label', 'new_zealand')
united_states = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'US').set('aoi_label', 'usa')
ne_usa = ee.FeatureCollection(united_states.toList(10).slice(2,3,1)).set('aoi_label', 'ne_usa')
se_usa = ee.FeatureCollection(united_states.toList(10).slice(1,2,1)).set('aoi_label', 'se_usa')
nw_usa = ee.FeatureCollection(united_states.toList(10).slice(4,5,1)).set('aoi_label', 'nw_usa')
sw_usa = ee.FeatureCollection(united_states.toList(10).slice(5,6,1)).set('aoi_label', 'sw_usa')
spain = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filterMetadata('country_co', 'equals', 'SP').set('aoi_label', 'spain')

# specific areas of interest
#!wget https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_20m.json
try:
    california = geemap.geojson_to_ee('./pipeline/gz_2010_us_040_00_20m.json') \
                        .filterMetadata('NAME', 'equals', 'California') \
                        .set('aoi_label', 'california')
except:
    california = geemap.geojson_to_ee('gz_2010_us_040_00_20m.json') \
                        .filterMetadata('NAME', 'equals', 'California') \
                        .set('aoi_label', 'california')

# these are custom-files made by copying geometries created on https://code.earthengine.google.com and printed to the console

central_valley_california_g = ee.Geometry({
  "type": "Polygon",
  "coordinates": [
    [
      [
        -122.2286422366599,
        40.28233810975918
      ],
      [
        -122.38310075342639,
        39.842682484273325
      ],
      [
        -122.3824508304099,
        39.11587403235935
      ],
      [
        -121.8331344241599,
        38.12017202382117
      ],
      [
        -121.6024215335349,
        37.704124178806325
      ],
      [
        -119.4930465335349,
        35.21273370921282
      ],
      [
        -119.25906417616741,
        35.01075684633611
      ],
      [
        -118.8393600100974,
        34.94300718912039
      ],
      [
        -118.70477749056614,
        35.23741399555778
      ],
      [
        -119.0535934085349,
        36.335797909177614
      ],
      [
        -120.3499801272849,
        37.49521901385896
      ],
      [
        -120.91302944369114,
        38.13529595072468
      ],
      [
        -121.3717086429099,
        39.16274032694631
      ],
      [
        -121.76373799407064,
        39.774008125791156
      ],
      [
        -122.2286422366599,
        40.28233810975918
      ]
    ]
  ]
})

bakersfield_g = ee.Geometry({
  "type": "Polygon",
  "coordinates": [
    [
      [
        -119.44268257679244,
        35.42757659340908
      ],
      [
        -119.03893501819869,
        35.42757659340908
      ],
      [
        -119.03893501819869,
        35.5382838100466
      ],
      [
        -119.44268257679244,
        35.5382838100466
      ],
      [
        -119.44268257679244,
        35.42757659340908
      ]
    ]
  ]
})

central_kansas_g = ee.Geometry({
  "type": "Polygon",
  "coordinates": [
    [
      [
        -101.39418477864311,
        37.13889997760407
      ],
      [
        -100.12526388020561,
        37.13889997760407
      ],
      [
        -100.12526388020561,
        38.36043236071481
      ],
      [
        -101.39418477864311,
        38.36043236071481
      ],
      [
        -101.39418477864311,
        37.13889997760407
      ]
    ]
  ]
})

southern_idaho_g = ee.Geometry({
  "type": "Polygon",
  "coordinates": [
    [
      [
        -115.1437807047337,
        42.064591353386916
      ],
      [
        -113.1662416422337,
        42.064591353386916
      ],
      [
        -113.1662416422337,
        43.099984199862824
      ],
      [
        -115.1437807047337,
        43.099984199862824
      ],
      [
        -115.1437807047337,
        42.064591353386916
      ]
    ]
  ]
})

central_ca = ee.FeatureCollection(central_valley_california_g)\
                .set('aoi_label', 'central_valley_california')

bakersfield = ee.FeatureCollection(bakersfield_g)\
                .set('aoi_label', 'bakersfield')

southern_idaho = ee.FeatureCollection(southern_idaho_g)\
                .set('aoi_label', 'southern_idaho')

central_kansas = ee.FeatureCollection(central_kansas_g)\
                .set('aoi_label', 'central_kansas')
