import ee

def getRawLabeledData():
    # irrMapper data
    irr_west = ee.FeatureCollection('projects/ee-dgketchum/assets/bands/IrrMapper_RF_training_data') \
                    .filter(ee.Filter.eq('POINT_TYPE', '0')) \
                    .map(lambda x: x.set('POINT_LOC', 'us_west'))

    rain_west = ee.FeatureCollection('projects/ee-dgketchum/assets/bands/IrrMapper_RF_training_data') \
                    .filter(ee.Filter.eq('POINT_TYPE', '1')) \
                    .map(lambda x: x.set('POINT_LOC', 'us_west'))

    # LANID data
    irr_east = geemap.shp_to_ee('./lanid/irrSamples_eastCONUS.shp') \
                        .map(lambda x: x.set('POINT_LOC', 'us_east'))

    rain_east = geemap.shp_to_ee('./lanid/rainfedSamples_eastCONUS.shp') \
                        .map(lambda x: x.set('POINT_LOC', 'us_east'))

    return irr_west, rain_west, irr_east, rain_east

def retrieveSampleDatasetImageWest(start_yr, end_yr):
    # retrieve irrMapper data (western USA) for both Train and Val, then merge together
    # POINT_TYPE 0 = irrigated
    # POINT_TYPE 1 = rainfed

    train = ee.FeatureCollection('projects/ee-dgketchum/assets/bands/IrrMapper_RF_training_data') \
        .filter(ee.Filter.lt('POINT_TYPE', '2'))
    val = ee.FeatureCollection('projects/ee-dgketchum/assets/validation/IrrMapper_RF_validation_points') \
        .filter(ee.Filter.lt('POINT_TYPE', 2))

    # type conversions
    train = train.map(lambda x: x.set('POINT_TYPE', ee.Number.parse(
                                                          x.get('POINT_TYPE')
                                                      )))
    train = train.map(lambda x: x.set('YEAR', ee.Number.parse(
                                                    ee.Date(
                                                        ee.Number.parse(
                                                            x.get('YEAR')
                                                        )
                                                    ).format('YYYY')
                                                )
                                        ))

    sample_data = train.merge(val) \
                       .select(['YEAR', 'POINT_TYPE', 'coordinates']) \
                       .map(lambda x: x.set('POINT_SRC', 'IrrMapper'))

    # retrieve data that was manually labeled independent of time and generate temporal samples
    manual_labels = miscellaneous_aois.ca_rainfed.geometries().cat(
                      miscellaneous_aois.or_rainfed.geometries()) \
                       .map(lambda x: x.set('POINT_SRC', 'Manual'))

    # generate temporal samples (1 sample for each location for each year)
    manual_data = None
    for yr in range(start_yr, end_yr+1):
        tmp = manual_labels.map(lambda x: ee.Feature(ee.Geometry(x)) \
                                            .set('YEAR', yr) \
                                            .set('POINT_TYPE', 1) \
                                            .set('POINT_SRC', 'Manual'))
        if manual_data:
            manual_data = manual_data.merge(tmp)
        else:
            manual_data = ee.FeatureCollection(tmp)

    # combine the irrMapper data with the manually labeled data
    sample_data = sample_data.merge(manual_data)

    return sample_data

def retrieveSampleDatasetImageEast(start_yr, end_yr):
    # retrieve LANID data (eastern USA) for both irrigated and rainfed, then merge together
    # POINT_TYPE 0 = irrigated
    # POINT_TYPE 1 = rainfed

    # generate temporal samples (1 sample for each location for each year)
    irr_east = geemap.shp_to_ee('./lanid/irrSamples_eastCONUS.shp')
    irr_east_flat = None
    for yr in range(start_yr, end_yr+1):
        fc = irr_east.filter(ee.List([ee.Filter.lte('startYr', yr),
                      ee.Filter.gte('endYr', yr)])) \
              .map(lambda x: x.set('YEAR', yr) \
                              .set('POINT_TYPE', 0))
        if irr_east_flat:
            irr_east_flat = irr_east_flat.merge(fc)
        else:
            irr_east_flat = fc

    # generate temporal samples (1 sample for each location for each year)
    rain_east = geemap.shp_to_ee('./lanid/rainfedSamples_eastCONUS.shp')
    rain_east_flat = None
    for yr in range(start_yr, end_yr+1):
        fc = rain_east.filter(ee.List([ee.Filter.lte('startYr', yr),
                      ee.Filter.gte('endYr', yr)])) \
              .map(lambda x: x.set('YEAR', yr) \
                              .set('POINT_TYPE', 1))
        if rain_east_flat:
            rain_east_flat = rain_east_flat.merge(fc)
        else:
            rain_east_flat = fc

    train = irr_east_flat.merge(rain_east_flat)

    # downselect only relevant properties
    sample_data = train.select(['YEAR', 'POINT_TYPE', 'coordinates'])

    return sample_data

def generateSampleLocations(aoi=None, aoi_label='', num_samples=10, start_yr=2015, end_yr=2021):
    sample_img_west = retrieveSampleDatasetImageWest(start_yr, end_yr)
    sample_img_east = retrieveSampleDatasetImageEast(start_yr, end_yr)
    sample_locations = sample_img_west.merge(sample_img_east)

    # filters
    if aoi:
        sample_locations = sample_locations.filterBounds(aoi)
    if year:
        sample_locations = sample_locations.filter(ee.Filter.gte('YEAR', start_yr))

    # randomize
    sample_locations = sample_locations \
                            .randomColumn('rando', seed=159) \
                            .sort('rando')

    sample_locations_irr = sample_locations \
                            .filter(ee.Filter.eq('POINT_TYPE', 0)) \
                            .limit(num_samples)

    sample_locations_rain = sample_locations \
                            .filter(ee.Filter.eq('POINT_TYPE', 1)) \
                            .limit(num_samples)

    sample_locations = sample_locations_irr.merge(sample_locations_rain)

    return sample_locations
