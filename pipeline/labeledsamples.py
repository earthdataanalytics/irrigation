import ee
import geemap
from pipeline import boundaries as bnd
from pipeline import rainfed_labels as rain_labels
from pipeline import cropmasks

def getRawLabeledData():
    # irrMapper data
    # https://www.mdpi.com/2072-4292/12/14/2328
    #       POINT_TYPE 0 = irrigated agriculture
    #       POINT_TYPE 1 = dryland agriculture
    #       POINT_TYPE 2 = uncultivated land
    #       POINT_TYPE 3 = wetlands
    # verified by manual inspection on GEE
    irr_west = ee.FeatureCollection('projects/ee-dgketchum/assets/bands/IrrMapper_RF_training_data') \
                    .filter(ee.Filter.eq('POINT_TYPE', '0')) \
                    .map(lambda x: x.set('POINT_LOC', 'us_west')) \
                    .map(lambda x: x.set('POINT_TYPE', 1)) \
                   .map(lambda x: x.set('POINT_SRC', 'IrrMapper'))

    rain_west = ee.FeatureCollection('projects/ee-dgketchum/assets/bands/IrrMapper_RF_training_data') \
                    .filter(ee.Filter.eq('POINT_TYPE', '1')) \
                    .map(lambda x: x.set('POINT_LOC', 'us_west')) \
                    .map(lambda x: x.set('POINT_TYPE', 0)) \
                   .map(lambda x: x.set('POINT_SRC', 'IrrMapper'))

    # LANID data
    # https://zenodo.org/record/5548555#.YuVBOC-B30q
    # see Metadata.docx
    #       POINT_TYPE 0 = rainfed
    #       POINT_TYPE 1 = irrigated
    irr_east = geemap.shp_to_ee('./lanid/irrSamples_eastCONUS.shp') \
                        .map(lambda x: x.set('POINT_LOC', 'us_east')) \
                        .map(lambda x: x.set('POINT_TYPE', 1)) \
                        .map(lambda x: x.set('POINT_SRC', 'LANID'))

    rain_east = geemap.shp_to_ee('./lanid/rainfedSamples_eastCONUS.shp') \
                        .map(lambda x: x.set('POINT_LOC', 'us_east')) \
                        .map(lambda x: x.set('POINT_TYPE', 0)) \
                        .map(lambda x: x.set('POINT_SRC', 'LANID'))

    return irr_west, rain_west, irr_east, rain_east

def generateManualLabels(start_yr, end_yr):
    # generate additional points for west using manual labels for rainfed locations
    #       retrieve data that was manually labeled independent of time
    #       and generate temporal samples
    manual_labels = rain_labels.manual_rainfed

    # generate temporal samples (1 sample for each location for each year)
    manual_data = None
    for yr in range(start_yr, end_yr+1):
        tmp = manual_labels.map(lambda x: x.set('YEAR', yr))
        if manual_data:
            manual_data = manual_data.merge(tmp)
        else:
            manual_data = ee.FeatureCollection(tmp)

    return manual_data

def preProcessEastData(irr_east, rain_east, start_yr, end_yr):
    # generate temporal samples (1 sample for each location for each year)
    irr_east_flat = None
    for yr in range(start_yr, end_yr+1):
        fc = irr_east.filter(ee.List([ee.Filter.lte('startYr', yr),
                             ee.Filter.gte('endYr', yr)])) \
                     .map(lambda x: x.set('YEAR', yr))

        if irr_east_flat:
            irr_east_flat = irr_east_flat.merge(fc)
        else:
            irr_east_flat = fc

    # generate temporal samples (1 sample for each location for each year)
    rain_east_flat = None
    for yr in range(start_yr, end_yr+1):
        fc = rain_east.filter(ee.List([ee.Filter.lte('startYr', yr),
                              ee.Filter.gte('endYr', yr)])) \
                      .map(lambda x: x.set('YEAR', yr))

        if rain_east_flat:
            rain_east_flat = rain_east_flat.merge(fc)
        else:
            rain_east_flat = fc

    east_data = irr_east_flat.merge(rain_east_flat)
    return east_data

def retrieveSampleAnnualDatasetImage(start_yr, end_yr):
    irr_west, rain_west, irr_east, rain_east = getRawLabeledData()

    # merge west data
    sample_data = irr_west.merge(rain_west) \
                    .map(lambda x: x.set('YEAR', ee.Number.parse(
                                        ee.Date(
                                            ee.Number.parse(x.get('YEAR'))
                                        ).format('YYYY')
                                    )
                                ))

    # get manually labeled data and combine with the irrMapper data
    manual_data = generateManualLabels(start_yr, end_yr)

    # pre-process east data
    east_data = preProcessEastData(irr_east, rain_east, start_yr, end_yr)

    # merge all data and downselect specific properties
    sample_data = sample_data.merge(manual_data) \
                        .merge(east_data) \
                        .select(['YEAR', 'POINT_TYPE', 'coordinates'])

    return sample_data

def generateAnnualSampleLocations(aoi=None, aoi_label='', num_samples=10, start_yr=2015, end_yr=2021):
    sample_locations_tmp = retrieveSampleAnnualDatasetImage(start_yr, end_yr)

    # filters
    if aoi:
        sample_locations_tmp = sample_locations_tmp.filterBounds(aoi)

    # randomize
    sample_locations_tmp = sample_locations_tmp \
                            .randomColumn('rando', seed=159) \
                            .sort('rando') \

    sample_locations_irr = sample_locations_tmp \
                            .filter(ee.Filter.eq('POINT_TYPE', 1)) \
                            .limit(num_samples)

    sample_locations_rain = sample_locations_tmp \
                            .filter(ee.Filter.eq('POINT_TYPE', 0)) \
                            .limit(num_samples)

    sample_locations = sample_locations_irr.merge(sample_locations_rain)

    return sample_locations

def getRawMonthlyLabeledData():
    def setCoords(item):
        # long is index 0 in coordinates list
        # lat is index 1
        return item.set('coordinates', item.geometry().coordinates())

    folder = 'projects/eda-bjonesneu-proto/assets/irrigation/labels'
    label_files = ee.data.listAssets({'parent': folder})

    label_features = None
    for item in label_files['assets']:
        features = ee.FeatureCollection(item['id'])
        if label_features:
            label_features = label_features.merge(features)
        else:
            label_features = features

    return label_features.map(setCoords)

def generateMonthlySampleLocations(aoi=None, aoi_label='', num_samples=10, start_yr=2015, end_yr=2021, excludeNonCrop=False):
    sample_locations_tmp = getRawMonthlyLabeledData()

    # filters
    if aoi:
        sample_locations_tmp = sample_locations_tmp.filterBounds(aoi)

    if excludeNonCrop: # return sample locations which are not masked
                      #  masked pixels have value of 0 in GEE
        mask = cropmasks.createGFSADmask(aoi)
        #feats = ee.FeatureCollection(sample_locations_tmp.coordinates().map(
        #                lambda p: ee.Feature(ee.Geometry.Point(p), {})
        #            ))
        sample_locations_tmp = mask.reduceRegions(sample_locations_tmp, ee.Reducer.first(), 30) \
                        .filter(ee.Filter.eq('first', 1))

    # randomize
    sample_locations_tmp = sample_locations_tmp \
                            .randomColumn('rando', seed=159) \
                            .sort('rando')

    sample_locations_irr = sample_locations_tmp \
                            .filter(ee.Filter.eq('POINT_TYPE', 1)) \
                            .limit(num_samples)

    sample_locations_rain = sample_locations_tmp \
                            .filter(ee.Filter.eq('POINT_TYPE', 0)) \
                            .limit(num_samples)

    sample_locations = sample_locations_irr.merge(sample_locations_rain)

    return sample_locations
