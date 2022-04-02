import ee
from tqdm import tqdm

from etbrasil.geesebal import TimeSeries_bcj
from pipeline import cropmasks as msk

def exportETdata(etFC, lbl, loc, folder='irrigation'):
    filename = 'et_TS_' + lbl + '_' + loc
    task = ee.batch.Export.table.toDrive(
      collection = etFC,
      description = filename,
      folder = folder,
    )
    task.start()

def extractData(aoi, aoi_label,
                start_yr=2015, start_mo=6, start_dy=1,
                end_yr=2021, end_mo=8, end_dy=31,
                max_cloud_cover=30,
                buffer_range=50,
                calc_ET_region=False):

    # buffer_range is in meters, max 7000 for GEE limits.
    # must be set tight around sample locations to limit zone from
    # which data is retrievedfor the sample location itself.

    # region size for ET_24_R calculation is handled with
    # buffersize parameter below

    out = []
    max_points = 10000 # set arbitrarily high to capture all values
    num_sample_years = end_yr - start_yr

    # ensure there is a defined buffer zone around each location
    locs_list = aoi.toList(max_points)
    locations_buffered = ee.FeatureCollection(locs_list) \
                            .geometry() \
                            .coordinates() \
                            .map(lambda p: ee.Geometry.Point(p) \
                                             .buffer(buffer_range))

    num_locations = locations_buffered.size().getInfo()
    print('Number of locations to extract =', num_locations)

    cnt = 0
    for yr_inc in tqdm(range(num_sample_years)):
        for idx in tqdm(range(num_locations), leave=False):
            location = locations_buffered.get(idx)
            single_location = ee.Geometry(location)

            loc_type = ee.Feature(locs_list.get(idx)).get('POINT_TYPE')

            # use buffersize=5000 and calcRegionalET=True for ET_24h_R regionalization calculations
            buffsize = 50
            if calc_ET_region:
                buffsize = 5000

            sebalTS = TimeSeries_bcj(start_yr+yr_inc, start_mo, start_dy,
                                        start_yr+yr_inc, end_mo, end_dy,
                                        max_cloud_cover, single_location,
                                        buffersize=buffsize,
                                        calcRegionalET=calc_ET_region
                                     )

            sebalTS.ETandMeteo = sebalTS.ETandMeteo \
                                    .map(lambda x: x.set('loc_type', loc_type))

            exportETdata(etFC=sebalTS.ETandMeteo,
                         lbl=aoi_label,
                         loc=str(idx)+'_'+str(start_yr+yr_inc))
            out.append(sebalTS.ETandMeteo)
            cnt+=1

    print('Number of tasks launched =', cnt)
    return out

def buildImageCollection(aoi, start, end, max_cloud=10, ls5=False, ls7=False, ls_all=False):
    # always returns LS8
    cropmask = msk.createGFSADmask(aoi)
    def getImages(dataset):
        return ee.ImageCollection(dataset) \
                  .filterDate(start, end) \
                  .filter(ee.Filter.lt('CLOUD_COVER', max_cloud)) \
                  .map(lambda x: x.updateMask(cropmask)) \
                  .filterBounds(aoi)

    imgcol8 = getImages('LANDSAT/LC08/C01/T1_SR')
    imgcol7 = getImages('LANDSAT/LE07/C01/T1_SR')
    imgcol5 = getImages('LANDSAT/LT05/C01/T1_SR')

    if ls_all or (ls5 and ls7):
        return imgcol8.merge(imgcol7).merge(imgcol5)
    if ls7:
        return imgcol8.merge(imgcol7)
    if ls7:
        return imgcol8.merge(imgcol5)
    return imgcol8

def exportRaster(classified_image, type='unknown', region=aoi, scale=30):
    snapshot_path_prefix = 'projects/eda-bjonesneu-proto/assets/irrigation/'
    date = classified_image.get('custom:date').getInfo()
    asset_description = f'{type}_{date}'
    asset_name = f'{snapshot_path_prefix}_{asset_description}'

    task = ee.batch.Export.image.toAsset(
        image=classified_image,
        description=asset_description,
        assetId=asset_name,
        scale=scale,
        region=aoi,
        maxPixels=1e13,
    )
    task.start()
    return task
