import ee
import geemap
import numpy as np

def createMODISmask(aoi=None):
    sample_img = ee.ImageCollection('MODIS/006/MCD12Q1') \
                        .filterDate('2018-12-01','2020-01-01')

    if aoi:
        sample_img = sample_img.filterBounds(aoi)

    sample_img = sample_img.mosaic()

    if aoi:
        sample_img = sample_img.clip(aoi)

    mask1 = sample_img.select('LC_Type1').eq(12) # croplands
    mask2 = sample_img.select('LC_Type1').eq(14) # croplands
    mask = mask1.Or(mask2)
    return mask

def createGFSADmask(aoi=None):
    # required setting up a bucket on google cloud to host the raster images which were sourced from:
    #        https://www.usgs.gov/centers/western-geographic-science-center/science/global-food-security-support-analysis-data-30-m
    # the data is for the year 2015
    # requires copying credentials to access the bucket
    import os
    from google.cloud import storage

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './pipeline/second-impact-342800-51af159903ca.json'
    client = storage.Client()
    bucket = client.bucket('eda_gfs')
    blobs = list(bucket.list_blobs())
    gfsad_tilelist = list(np.array([x.path.split('/')[-1:] for x in blobs]).squeeze())
    gfsad_tilelist = ['https://storage.googleapis.com/eda_gfs/' + x for x in gfsad_tilelist]

    gfsad_im = geemap.load_GeoTIFFs(gfsad_tilelist)

    if aoi:
        gfsad_im = gfsad_im.filterBounds(aoi)

    gfsad_im = gfsad_im.mosaic()

    if aoi:
        gfsad_im = gfsad_im.clip(aoi)

    mask = gfsad_im.select('B0').eq(2) # croplands
    return mask

def createGLADmask(aoi=None):
    glad_im = ee.Image('users/potapovpeter/Global_cropland_2019/Global_cropland_2019_NW')

    if aoi:
        glad_im = glad_im.clip(aoi)

    mask = glad_im.select('b1').eq(1) # croplands
    return mask
