#----------------------------------------------------------------------------------------#
#---------------------------------------//GEESEBAL//-------------------------------------#
#GEESEBAL - GOOGLE EARTH ENGINE APP FOR SURFACE ENERGY BALANCE ALGORITHM FOR LAND (SEBAL)
#CREATE BY: LEONARDO LAIPELT, RAFAEL KAYSER, ANDERSON RUHOFF AND AYAN FLEISCHMANN
#PROJECT - ET BRASIL https://etbrasil.org/
#LAB - HIDROLOGIA DE GRANDE ESCALA [HGE] website: https://www.ufrgs.br/hge/author/hge/
#UNIVERSITY - UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL - UFRGS
#RIO GRANDE DO SUL, BRAZIL

#DOI
#VERSION 0.1.1
#CONTACT US: leonardo.laipelt@ufrgs.br

# Modified by Blair Jones on Aug 8, 2022

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#

#PYTHON PACKAGES
#Call EE
import ee

#SURFACE REFLECTANCE
#ATMOSPHERICALLY CORRECTED

def getLScollection(ls_col2=False):
    # Tier 1 provides the highest level of data correctness,
    # with RMSE < 12 meters.  This is considered the minimal
    # threshold needed for timeseries analysis.
    ls_col = {}
    if ls_col2:
        # Collection 2 # replaces Collection 1 during 2022 by USGS
        # Collection improves geospatial location accuracy and reduces striping
        ls_col['LS9'] = 'LANDSAT/LC09/C02/T1_L2' # added by BCJ on TBD
        ls_col['LS8'] = 'LANDSAT/LC08/C02/T1_L2'
        ls_col['LS7'] = 'LANDSAT/LE07/C02/T1_L2'
        ls_col['LS5'] = 'LANDSAT/LT05/C02/T1_L2'
    else:
        # Collection 1 # used in original GEESEBAL algorithm
        ls_col['LS9'] = None # was not used in original GEESEBAL algorithm
        ls_col['LS8'] = 'LANDSAT/LC08/C01/T1_SR'
        ls_col['LS7'] = 'LANDSAT/LE07/C01/T1_SR'
        ls_col['LS5'] = 'LANDSAT/LT05/C01/T1_SR'
    return ls_col

#GET LANDSAT 8 COLLECTIONS BY PATH ROW
def fexp_landsat_8PathRow(start_date,end_date,n_path, n_row,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L8 =(ee.ImageCollection(ls_col['LS8'])
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select([0,1,2,3,4,5,6,7,10],["UB","B","GR","R","NIR","SWIR_1","SWIR_2","BRT","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L8;

#GET LANDSAT 7 COLLECTIONS BY PATH ROW
def fexp_landsat_7PathRow(start_date,end_date,n_path, n_row,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L7 =(ee.ImageCollection(ls_col['LS7'])
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select([0,1,2,3,4,5,6,9], ["B","GR","R","NIR","SWIR_1","BRT","SWIR_2", "pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));


    return col_SR_L7;

#GET LANDSAT 5 COLLECTIONS BY PATH ROW
def fexp_landsat_5PathRow(start_date,end_date,n_path, n_row,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L5 =(ee.ImageCollection(ls_col['LS5'])
                        .filterDate(start_date, end_date)
                        .filterMetadata('WRS_PATH', 'equals', n_path)
                        .filterMetadata('WRS_ROW', 'equals', n_row)
                        .select([0,1,2,3,4,5,6,9], ["B","GR","R","NIR","SWIR_1","BRT","SWIR_2", "pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));

    return col_SR_L5;

#GET LANDSAT 7 COLLECTIONS BY COORDINATE
def fexp_landsat_7Coordinate(start_date,end_date,coordinate,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L7 =(ee.ImageCollection(ls_col['LS7'])
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select([0,1,2,3,4,5,6,9], ["B","GR","R","NIR","SWIR_1","BRT","SWIR_2", "pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));


    return col_SR_L7;

#GET LANDSAT 8 COLLECTIONS BY COORDINATE
def fexp_landsat_8Coordinate(start_date,end_date,coordinate,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L8 =(ee.ImageCollection(ls_col['LS8'])
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select([0,1,2,3,4,5,6,7,10],["UB","B","GR","R","NIR","SWIR_1","SWIR_2","BRT","pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));
    return col_SR_L8;

#GET LANDSAT 5 COLLECTIONS BY COORDINATE
def fexp_landsat_5Coordinate(start_date,end_date,coordinate,th_cloud_cover, ls_col2):
    ls_col = getLScollection(ls_col2)
    col_SR_L5 =(ee.ImageCollection(ls_col['LS5'])
                        .filterDate(start_date, end_date)
                        .filterBounds(coordinate)
                        .select([0,1,2,3,4,5,6,9], ["B","GR","R","NIR","SWIR_1","BRT","SWIR_2", "pixel_qa"])
                        .filterMetadata('CLOUD_COVER', 'less_than', th_cloud_cover));

    return col_SR_L5;
