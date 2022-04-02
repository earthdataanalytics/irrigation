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
# Customized by bjonesneu@berkeley.edu, bjonesneu@gmail.com in March 2022
#   - Added additional output variables
#   - Converted to run all code on GEE Server instead of Client
#
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#

#PYTHON PACKAGES
#Call EE
import ee
#ee.Initialize()

#FOLDERS
from .masks import (
f_cloudMaskL457_SR,f_cloudMaskL8_SR,
 f_albedoL5L7,f_albedoL8)
from .meteorology import get_meteorology, retrievePrecipImage
from .tools import (fexp_spec_ind, fexp_lst_export,fexp_radlong_up, LST_DEM_correction,
fexp_radshort_down, fexp_radlong_down, fexp_radbalance, fexp_soil_heat, fexp_sensible_heat_flux,
fexp_sensible_heat_flux_bcj)
from .endmembers import fexp_cold_pixel, fexp_hot_pixel
from .evapotranspiration import fexp_et


#IMAGE FUNCTION
class Image_bcj():

    #ENDMEMBERS DEFAULT
    #ALLEN ET AL. (2013)
    def __init__(self,
                 #image,
                 NDVI_cold=5,
                 Ts_cold=20,
                 NDVI_hot=10,
                 Ts_hot=20,
                 et_var='ET_24h',
                 precip_window=10,
                 cum_precip_window=3,
                 window_start=None,
                 window_end=None,
                 aoi=None,
                 cloud_max=10
              ):

        #COLLECTIONS
        collection_l5=fexp_landsat_5Coordinate(window_start, window_end, aoi, cloud_max)
        collection_l7=fexp_landsat_7Coordinate(window_start, window_end, aoi, cloud_max)
        collection_l8=fexp_landsat_8Coordinate(window_start, window_end, aoi, cloud_max)

        def retrieveETandMeteo(image):
            #GET INFORMATIONS FROM IMAGE
            image = ee.Image(image)
            _index=image.get('system:index')
            cloud_cover=image.get('CLOUD_COVER')
            LANDSAT_ID=image.get('LANDSAT_ID').getInfo()
            landsat_version=image.get('SATELLITE').getInfo()
            azimuth_angle=image.get('SOLAR_ZENITH_ANGLE')
            time_start=image.get('system:time_start')
            _date=ee.Date(time_start)
            _year=ee.Number(_date.get('year'))
            _month=ee.Number(_date.get('month'))
            _day=ee.Number(_date.get('day'))
            _hour=ee.Number(_date.get('hour'))
            _minuts = ee.Number(_date.get('minutes'))
            crs = image.projection().crs()
            transform = ee.List(ee.Dictionary(ee.Algorithms.Describe(image.projection())).get('transform'))
            date_string=_date.format('YYYY-MM-dd').getInfo()

            #ENDMEMBERS
            p_top_NDVI=ee.Number(NDVI_cold)
            p_coldest_Ts=ee.Number(Ts_cold)
            p_lowest_NDVI=ee.Number(NDVI_hot)
            p_hottest_Ts=ee.Number(Ts_hot)

            #GEOMETRY
            geometryReducer=image.geometry().bounds()
            camada_clip=image.select('BRT').first()

            sun_elevation=ee.Number(90).subtract(azimuth_angle)

            #AIR TEMPERATURE [C]
            T_air = image.select('AirT_G');

            #WIND SPEED [M S-1]
            ux= image.select('ux_G');

            #RELATIVE HUMIDITY [%]
            UR = image.select('RH_G');

            #NET RADIATION 24H [W M-2]
            Rn24hobs = image.select('Rn24h_G');

            #SRTM DATA ELEVATION
            SRTM_ELEVATION ='USGS/SRTMGL1_003'
            srtm = ee.Image(SRTM_ELEVATION).clip(geometryReducer);
            z_alt = srtm.select('elevation');
            slope = ee.Terrain.slope('elevation');

            #GET IMAGE
            #image=image.first()

            #SPECTRAL IMAGES (NDVI, EVI, SAVI, LAI, T_LST, e_0, e_NB, long, lat)
            image=fexp_spec_ind(image)

            #LAND SURFACE TEMPERATURE
            image=LST_DEM_correction(image, z_alt, T_air, UR,sun_elevation,_hour,_minuts)
            LandT_G = image.select('T_LST_DEM').rename('LandT_G')

            #COLD PIXEL
            d_cold_pixel=fexp_cold_pixel(image, geometryReducer, p_top_NDVI, p_coldest_Ts)

            #COLD PIXEL NUMBER
            n_Ts_cold = ee.Number(d_cold_pixel.get('temp'))#.getInfo())

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
            image=fexp_sensible_heat_flux(image, ux, UR,Rn24hobs,n_Ts_cold,
                                               d_hot_pixel, date_string,geometryReducer)

            #DAILY EVAPOTRANSPIRATION (ET_24H) [MM DAY-1]
            image=fexp_et(image,Rn24hobs)

            #PRECIPITATION RETRIEVAL AND CALCULATIONS
            last_rain, cum_precip = retrievePrecipImage(date_string,
                                                        image,
                                                        precip_window=precip_window,
                                                        cum_precip_window=cum_precip_window)

            # Date bands
            mm = ee.Image(ee.Number.parse(_date.format('MM'))).rename('mm')
            dd = ee.Image(ee.Number.parse(_date.format('dd'))).rename('dd')
            yyyy = ee.Image(ee.Number.parse(_date.format('YYYY'))).rename('yyyy')

            #PREPARE OUTPUT IMAGE
            image=image.addBands([image.select('ET_24h').rename(et_var),
                                  image.select('NDVI'), LandT_G,
                                  last_rain, cum_precip,
                                  mm, dd, yyyy
              ])

            cols = [et_var, 'NDVI', 'LandT_G',
                    'last_rain', 'sum_precip_priorX',
                    'mm', 'dd', 'yyyy']
            return image.select(cols)


        ic5 = collection_l5.map(f_cloudMaskL457_SR) \
                            .map(f_albedoL5L7) \
                            .map(verifyMeteoAvail) \
                            .filter(ee.Filter.gt('meteo_count', 0)) \
                            .map(get_meteorology) \
                            .map(retrieveETandMeteo)
        imgcol = ic5

        ic7 = collection_l7.map(f_cloudMaskL457_SR) \
                            .map(f_albedoL5L7) \
                            .map(verifyMeteoAvail) \
                            .filter(ee.Filter.gt('meteo_count', 0)) \
                            .map(get_meteorology) \
                            .map(retrieveETandMeteo)
        imgcol = imgcol.merge(ic7)

        ic8 = collection_l8.map(f_cloudMaskL8_SR) \
                            .map(f_albedoL8) \
                            .map(verifyMeteoAvail) \
                            .filter(ee.Filter.gt('meteo_count', 0)) \
                            .map(get_meteorology) \
                            .map(retrieveETandMeteo)
        imgcol = imgcol.merge(ic8)

        return imagecol
