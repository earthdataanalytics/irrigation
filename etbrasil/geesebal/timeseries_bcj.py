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

#----------------------------------------------------------------------------------------#
#
# Customized by bjonesneu@berkeley.edu, bjonesneu@gmail.com in February 2022
#   - Added additional output variables
#   - Converted to run all code on GEE Server instead of Client
#
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#

#PYTHON PACKAGES
#Call EE
import ee
ee.Initialize()
from datetime import date
import datetime

import sys

#FOLDERS
from .landsatcollection import fexp_landsat_5Coordinate, fexp_landsat_7Coordinate, fexp_landsat_8Coordinate
from .masks import (f_cloudMaskL457_SR,f_cloudMaskL8_SR,f_albedoL5L7,f_albedoL8)
from .meteorology import get_meteorology, retrievePrecip
from .tools import (fexp_spec_ind, fexp_lst_export,fexp_radlong_up, LST_DEM_correction,
fexp_radshort_down, fexp_radlong_down, fexp_radbalance, fexp_soil_heat,fexp_sensible_heat_flux_bcj)
from .endmembers import fexp_cold_pixel, fexp_hot_pixel
from .evapotranspiration import fexp_et

#TIMESRIES FUNCTION
class TimeSeries_bcj():

    #ENDMEMBERS DEFAULT
    #ALLEN ET AL. (2013)
    def __init__(self,
                 year_i,
                 month_i,
                 day_i,
                 year_e,
                 month_e,
                 day_e,
                 cloud_cover,
                 coordinate,
                 buffersize=90,
                 NDVI_cold=5,
                 Ts_cold=20,
                 NDVI_hot=10,
                 Ts_hot=20):

        #output variable
        self.ETandMeteo = None

        #INFORMATIONS
        self.coordinate=coordinate
        #self.buffer=self.coordinate.buffer(buffersize)
        self.cloud_cover=cloud_cover
        self.start_date = ee.Date.fromYMD(year_i,month_i,day_i)
        self.i_date=date(year_i,month_i,day_i)
        self.end_date=date(year_e,month_e,day_e)
        self.n_search_days=self.end_date - self.i_date
        self.n_search_days=self.n_search_days.days
        self.end_date = self.start_date.advance(self.n_search_days, 'day')

        #COLLECTIONS
        self.collection_l5=fexp_landsat_5Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)
        self.collection_l7=fexp_landsat_7Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)
        self.collection_l8=fexp_landsat_8Coordinate(self.start_date, self.end_date, self.coordinate, self.cloud_cover)

        #LIST OF IMAGES
        #self.sceneListL5 = self.collection_l5.aggregate_array('system:index').getInfo()
        #self.sceneListL7 = self.collection_l7.aggregate_array('system:index').getInfo()
        #self.sceneListL8 = self.collection_l8.aggregate_array('system:index').getInfo()

        #self.collection = self.collection_l5.merge(self.collection_l7).merge(self.collection_l8)
        #self.count = self.collection.size().getInfo()
        #print('number of images', self.count)
        #FOR EACH IMAGE IN THE COLLECTION
        #ESTIMATE ET DAILY IMAGE AND EXTRACT
        #ET VALUE AT THE COORDINATE

        def retrieveETandMeteo(image, landsat_version):
            image=ee.Image(image) # just used to ensure correct type casting

            #PRINT ID
            img_id = image.get('LANDSAT_ID')
            #print(img_id)

            #GET INFORMATIONS FROM IMAGE
            _index=image.get('system:index')
            cloud_cover=image.get('CLOUD_COVER')
            LANDSAT_ID=image.get('LANDSAT_ID')
            #landsat_version=ee.String(image.get('SATELLITE'))
            zenith_angle=image.get('SOLAR_ZENITH_ANGLE')
            azimuth_angle=image.get('SOLAR_AZIMUTH_ANGLE')
            time_start=image.get('system:time_start')
            _date=ee.Date(time_start)
            _year=ee.Number(_date.get('year'))
            _month=ee.Number(_date.get('month'))
            _day=ee.Number(_date.get('month'))
            _hour=ee.Number(_date.get('hour'))
            _minuts = ee.Number(_date.get('minutes'))
            crs = image.projection().crs()
            transform = ee.List(ee.Dictionary(ee.Algorithms.Describe(image.projection())).get('transform'))
            date_string=_date.format('YYYY-MM-dd')

            #ENDMEMBERS
            p_top_NDVI=ee.Number(NDVI_cold)
            p_coldest_Ts=ee.Number(Ts_cold)
            p_lowest_NDVI=ee.Number(NDVI_hot)
            p_hottest_Ts=ee.Number(Ts_hot)

            etFeature = ee.Feature(self.coordinate.centroid(), {
              'date': date_string,
              'version': landsat_version,
              'status': 'no status'
            })
            errmsg = None
            #TO AVOID ERRORS DURING THE PROCESS
            try:

                #MASK
                if landsat_version == 'LANDSAT_5':
                    image_toa=ee.Image(ee.String('LANDSAT/LT05/C01/T1/').cat(ee.String(image.get('system:index')).slice(4)))

                    #GET CALIBRATED RADIANCE
                    col_rad = ee.Algorithms.Landsat.calibratedRadiance(image_toa);
                    col_rad = image.addBands(col_rad.select([5],["T_RAD"]))

                    #CLOUD REMOTION
                    image=ee.ImageCollection(image).map(f_cloudMaskL457_SR)

                    #ALBEDO TASUMI ET AL. (2008)
                    image=ee.ImageCollection(image).map(f_albedoL5L7)

                elif landsat_version == 'LANDSAT_7':
                    image_toa=ee.Image(ee.String('LANDSAT/LE07/C01/T1/').cat(ee.String(image.get('system:index')).slice(4)))

                    #GET CALIBRATED RADIANCE
                    col_rad = ee.Algorithms.Landsat.calibratedRadiance(image_toa);
                    col_rad = image.addBands(col_rad.select([5],["T_RAD"]))

                    #CLOUD REMOTION
                    image=ee.ImageCollection(image).map(f_cloudMaskL457_SR)

                    #ALBEDO TASUMI ET AL. (2008)
                    image=ee.ImageCollection(image).map(f_albedoL5L7)

                else:
                    image_toa=ee.Image(ee.String('LANDSAT/LC08/C01/T1/').cat(ee.String(image.get('system:index')).slice(2)))

                    #GET CALIBRATED RADIANCE
                    col_rad = ee.Algorithms.Landsat.calibratedRadiance(image_toa)
                    col_rad = image.addBands(col_rad.select([9],["T_RAD"]))

                    #CLOUD REMOTION
                    image=ee.ImageCollection(image).map(f_cloudMaskL8_SR)

                    #ALBEDO TASUMI ET AL. (2008) METHOD WITH KE ET AL. (2016) COEFFICIENTS
                    image=ee.ImageCollection(image).map(f_albedoL8)

                errmsg = '1'
                #GEOMETRY
                geometryReducer=image.geometry().bounds()
                camada_clip=image.select('BRT').first()

                sun_elevation=ee.Number(90).subtract(zenith_angle)

                col_meteorology= get_meteorology(image, time_start)

                errmsg = '2'
                #AIR TEMPERATURE [C]
                T_air = col_meteorology.select('AirT_G')

                #WIND SPEED [M S-1]
                ux= col_meteorology.select('ux_G')

                #RELATIVE HUMIDITY (%)
                UR = col_meteorology.select('RH_G')

                #NET RADIATION 24H [W M-2]
                Rn24hobs = col_meteorology.select('Rn24h_G')

                errmsg = '3'
                #SRTM DATA ELEVATION
                SRTM_ELEVATION ='USGS/SRTMGL1_003'
                srtm = ee.Image(SRTM_ELEVATION).clip(geometryReducer)
                z_alt = srtm.select('elevation')
                slope = ee.Terrain.slope(z_alt)

                errmsg = '4'
                #GET IMAGE
                image=image.first()

                errmsg = '5'
                #SPECTRAL IMAGES (NDVI, EVI, SAVI, LAI, T_LST, e_0, e_NB, long, lat)
                image=fexp_spec_ind(image)

                #LAND SURFACE TEMPERATURE
                image=LST_DEM_correction(image, z_alt, T_air, UR,sun_elevation,_hour,_minuts)
                T_land = image.select('T_LST_DEM').rename('LandT_G')

                #COLD PIXEL
                d_cold_pixel=fexp_cold_pixel(image, geometryReducer, p_top_NDVI, p_coldest_Ts)

                #COLD PIXEL NUMBER
                n_Ts_cold = ee.Number(d_cold_pixel.get('temp'))

                errmsg = '6'
                #INSTANTANEOUS OUTGOING LONG-WAVE RADIATION [W M-2]
                image=fexp_radlong_up(image)

                #INSTANTANEOUS INCOMING SHORT-WAVE RADIATION [W M-2]
                image=fexp_radshort_down(image,z_alt,T_air,UR, sun_elevation)

                #INSTANTANEOUS INCOMING LONGWAVE RADIATION [W M-2]
                image=fexp_radlong_down(image, n_Ts_cold)

                #INSTANTANEOUS NET RADIATON BALANCE [W M-2]
                image=fexp_radbalance(image)

                #SOIL HEAT FLUX (G) [W M-2]
                image=fexp_soil_heat(image)

                #HOT PIXEL
                d_hot_pixel=fexp_hot_pixel(image, geometryReducer,p_lowest_NDVI, p_hottest_Ts)

                #SENSIBLE HEAT FLUX (H) [W M-2]
                image=fexp_sensible_heat_flux_bcj(image, ux, UR,Rn24hobs,n_Ts_cold,
                                            d_hot_pixel, date_string, geometryReducer)

                errmsg = '7'
                #DAILY EVAPOTRANSPIRATION (ET_24H) [MM DAY-1]
                image=fexp_et(image,Rn24hobs)

                NAME_FINAL=ee.String(LANDSAT_ID).slice(0,5).cat(ee.String(LANDSAT_ID).slice(10,17)).cat(ee.String(LANDSAT_ID).slice(17,25))

                #EXTRACT VALUES
                def extractValue(var):
                    return var.reduceRegion(
                        reducer=ee.Reducer.first(),
                        geometry=self.coordinate,
                        scale=30,
                        maxPixels=1e14)
                def extractMinValue(var):
                    return var.reduceRegion(
                        reducer=ee.Reducer.min(),
                        geometry=self.coordinate,
                        scale=30,
                        maxPixels=1e14)
                def extractMaxValue(var):
                    return var.reduceRegion(
                        reducer=ee.Reducer.max(),
                        geometry=self.coordinate,
                        scale=30,
                        maxPixels=1e14)

                ET_daily=image.select(['ET_24h'],[NAME_FINAL])
                ET_point = extractValue(ET_daily)

                ET_min_daily=image.select(['ET_24h'],[NAME_FINAL])
                ET_min_point = extractMinValue(ET_min_daily)

                ET_max_daily=image.select(['ET_24h'],[NAME_FINAL])
                ET_max_point = extractMaxValue(ET_max_daily)

                NDVI_daily=image.select(['NDVI'],[NAME_FINAL])
                NDVI_point = extractValue(NDVI_daily)

                T_air_daily=T_air.select(['AirT_G'],[NAME_FINAL])
                T_air_point = extractValue(T_air_daily)

                T_land_daily=T_land.select(['LandT_G'],[NAME_FINAL])
                T_land_point = extractValue(T_land_daily)

                ux_daily=ux.select(['ux_G'],[NAME_FINAL])
                ux_point = extractValue(ux_daily)

                UR_daily=UR.select(['RH_G'],[NAME_FINAL])
                UR_point = extractValue(UR_daily)

                z_alt_daily=srtm.select(['elevation'],[NAME_FINAL])
                z_alt_point = extractValue(z_alt_daily)

                slope_daily=slope.select(['slope'],[NAME_FINAL])
                slope_point = extractValue(slope_daily)

                #GET DATE AND DAILY ET
                ET_point_get = ee.Number(ET_point.get(NAME_FINAL))
                ET_min_point_get = ee.Number(ET_min_point.get(NAME_FINAL))
                ET_max_point_get = ee.Number(ET_max_point.get(NAME_FINAL))
                NDVI_point_get = ee.Number(NDVI_point.get(NAME_FINAL))
                T_air_point_get = ee.Number(T_air_point.get(NAME_FINAL))
                T_land_point_get = ee.Number(T_land_point.get(NAME_FINAL))
                ux_point_get = ee.Number(ux_point.get(NAME_FINAL))
                UR_point_get = ee.Number(UR_point.get(NAME_FINAL))
                z_alt_point_get = ee.Number(z_alt_point.get(NAME_FINAL))
                slope_point_get = ee.Number(slope_point.get(NAME_FINAL))

                precip = retrievePrecip(date_string, self.coordinate)

                etFeature = ee.Feature(self.coordinate.centroid(), {
                    'date': date_string,
                    'version': landsat_version,
                    'status': 'ok',
                    'ET_24h': ET_point_get,
                    'ET_R_min': ET_min_point_get,
                    'ET_R_max': ET_max_point_get,
                    'NDVI': NDVI_point_get,
                    'AirT_G': T_air_point_get,
                    'LandT_G': T_land_point_get,
                    'ux': ux_point_get,
                    'UR': UR_point_get,
                    'z_alt': z_alt_point_get,
                    'slope': slope_point_get,
                    'precip': precip
                })

            except ee.EEException as e:
                # ERRORS CAN OCCUR WHEN:
                # - THERE IS NO METEOROLOGICAL INFORMATION.
                # - ET RETURN NULL IF AT THE POINT WAS APPLIED MASK CLOUD.
                # - CONEECTION ISSUES.
                # - SEBAL DOESN'T FIND A REASONABLE LINEAR RELATIONSHIP (dT).
                etFeature = ee.Feature(self.coordinate.centroid(), {
                    'date': date_string,
                    'version': landsat_version,
                    'status': time_start,#e,
                    'ET_24h': None,
                    'ET_R_min': None,
                    'ET_R_max': None,
                    'NDVI': None,
                    'AirT_G': None,
                    'LandT_G': None,
                    'ux': None,
                    'UR': None,
                    'z_alt': None,
                    'slope': None,
                    'precip': None
                })

            return etFeature

        #self.ETandMeteo = ee.FeatureCollection()
        #self.ETandMeteo = self.collection.map(retrieveETandMeteo)
        self.ETandMeteo = self.collection_l5.map(lambda x: retrieveETandMeteo(x, 'LANDSAT_5'))
        self.ETandMeteo = self.ETandMeteo.merge(self.collection_l7.map(lambda x: retrieveETandMeteo(x, 'LANDSAT_7')))
        self.ETandMeteo = self.ETandMeteo.merge(self.collection_l8.map(lambda x: retrieveETandMeteo(x, 'LANDSAT_8')))
