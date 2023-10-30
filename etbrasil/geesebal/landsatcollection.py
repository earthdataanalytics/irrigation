# ----------------------------------------------------------------------------------------#
# ---------------------------------------//GEESEBAL//-------------------------------------#
# GEESEBAL - GOOGLE EARTH ENGINE APP FOR SURFACE ENERGY BALANCE ALGORITHM FOR LAND (SEBAL)
# CREATE BY: LEONARDO LAIPELT, RAFAEL KAYSER, ANDERSON RUHOFF AND AYAN FLEISCHMANN
# PROJECT - ET BRASIL https://etbrasil.org/
# LAB - HIDROLOGIA DE GRANDE ESCALA [HGE] website: https://www.ufrgs.br/hge/author/hge/
# UNIVERSITY - UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL - UFRGS
# RIO GRANDE DO SUL, BRAZIL

# DOI
# VERSION 0.1.1
# CONTACT US: leonardo.laipelt@ufrgs.br

# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------------------#

# PYTHON PACKAGES
# Call EE
import ee
from .constants import Constants
from .landsat_utils import prepSrLandsat5and7, prepSrLandsat8and9
# SURFACE REFLECTANCE
# ATMOSPHERICALLY CORRECTED


# GET LANDSAT 9 COLLECTIONS BY PATH ROW
def fexp_landsat_9PathRow(start_date, end_date, n_path, n_row, th_cloud_cover):
    col_SR_L9 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_9)
        .filterDate(start_date, end_date)
        .filterMetadata("WRS_PATH", "equals", n_path)
        .filterMetadata("WRS_ROW", "equals", n_row)
        .map(prepSrLandsat8and9)
        .select(Constants.LANDSAT_9_BANDS["OFFICIAL"], Constants.LANDSAT_9_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L9


# GET LANDSAT 8 COLLECTIONS BY PATH ROW
def fexp_landsat_8PathRow(start_date, end_date, n_path, n_row, th_cloud_cover):
    col_SR_L8 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_8)
        .filterDate(start_date, end_date)
        .filterMetadata("WRS_PATH", "equals", n_path)
        .filterMetadata("WRS_ROW", "equals", n_row)
        .map(prepSrLandsat8and9)
        .select(Constants.LANDSAT_8_BANDS["OFFICIAL"], Constants.LANDSAT_8_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L8


# GET LANDSAT 7 COLLECTIONS BY PATH ROW
def fexp_landsat_7PathRow(start_date, end_date, n_path, n_row, th_cloud_cover):
    col_SR_L7 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_7)
        .filterDate(start_date, end_date)
        .filterMetadata("WRS_PATH", "equals", n_path)
        .filterMetadata("WRS_ROW", "equals", n_row)
        .map(prepSrLandsat5and7)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"], Constants.LANDSAT_5_7_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L7


# GET LANDSAT 5 COLLECTIONS BY PATH ROW
def fexp_landsat_5PathRow(start_date, end_date, n_path, n_row, th_cloud_cover):
    col_SR_L5 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_5)
        .filterDate(start_date, end_date)
        .filterMetadata("WRS_PATH", "equals", n_path)
        .filterMetadata("WRS_ROW", "equals", n_row)
        .map(prepSrLandsat5and7)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"], Constants.LANDSAT_5_7_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L5


# GET LANDSAT 5 COLLECTIONS BY COORDINATE
def fexp_landsat_5Coordinate(start_date, end_date, coordinate, th_cloud_cover):
    col_SR_L5 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_5) #APPEND LIST Constants.LANDSAT_ADDITIONAL_BANDS
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"] + Constants.LANDSAT_ADDITIONAL_BANDS)
        .filterBounds(coordinate)
        .filterDate(start_date, end_date)
        .map(prepSrLandsat5and7)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"], Constants.LANDSAT_5_7_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
        # .filterMetadata("CLOUD_COVER", "less_than", th_cloud_cover) TODO: Be careful with this code. It is commented out in the original code, but in prepSrLandsat5and7 there is a filter for cloud cover
    )
    return col_SR_L5


# GET LANDSAT 7 COLLECTIONS BY COORDINATE
def fexp_landsat_7Coordinate(start_date, end_date, coordinate, th_cloud_cover):
    col_SR_L7 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_7)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"] + Constants.LANDSAT_ADDITIONAL_BANDS)
        .filterBounds(coordinate)
        .filterDate(start_date, end_date)
        .map(prepSrLandsat5and7)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"], Constants.LANDSAT_5_7_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L7


# GET LANDSAT 8 COLLECTIONS BY COORDINATE
def fexp_landsat_8Coordinate(start_date, end_date, coordinate, th_cloud_cover):
    col_SR_L8 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_8)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"] + Constants.LANDSAT_ADDITIONAL_BANDS)
        .filterBounds(coordinate)
        .filterDate(start_date, end_date)
        .map(prepSrLandsat8and9)
        .select(Constants.LANDSAT_8_BANDS["OFFICIAL"], Constants.LANDSAT_8_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L8


# GET LANDSAT 9 COLLECTIONS BY COORDINATE
def fexp_landsat_9Coordinate(start_date, end_date, coordinate, th_cloud_cover):
    col_SR_L9 = (
        ee.ImageCollection(Constants.LANDSAT_COLLECTION_9)
        .select(Constants.LANDSAT_5_7_BANDS["OFFICIAL"] + Constants.LANDSAT_ADDITIONAL_BANDS)
        .filterBounds(coordinate)
        .filterDate(start_date, end_date)
        .map(prepSrLandsat8and9)
        .select(Constants.LANDSAT_9_BANDS["OFFICIAL"], Constants.LANDSAT_9_BANDS["CUSTOM"])
        .filterMetadata("CLOUD_COVER_LAND", "less_than", th_cloud_cover)
    )
    return col_SR_L9
