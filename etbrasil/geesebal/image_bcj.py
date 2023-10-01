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
from .landsatcollection import fexp_landsat_5Coordinate, fexp_landsat_7Coordinate, fexp_landsat_8Coordinate
from .masks import (f_albedoL5L7,f_albedoL8)
from .meteorology import get_meteorology, retrievePrecipImage, verifyMeteoAvail
from .tools import (fexp_spec_ind, fexp_lst_export,fexp_radlong_up, LST_DEM_correction,
fexp_radshort_down, fexp_radlong_down, fexp_radbalance, fexp_soil_heat, fexp_sensible_heat_flux,
fexp_sensible_heat_flux_bcj)
from .endmembers import fexp_cold_pixel, fexp_hot_pixel
from .evapotranspiration import fexp_et
from .constants import Constants
from .landsat_utils import prepSrLandsat5and7, prepSrLandsat8
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
                 cloud_max=10,
                 scale=30,
              ):

        #output variable
        self.ETandMeteo = None

        #COLLECTIONS
        collection_l5=fexp_landsat_5Coordinate(window_start, window_end, aoi, cloud_max)
        collection_l7=fexp_landsat_7Coordinate(window_start, window_end, aoi, cloud_max)
        collection_l8=fexp_landsat_8Coordinate(window_start, window_end, aoi, cloud_max)

        def retrieveETandMeteo(image):
            #GET INFORMATIONS FROM IMAGE
            image = ee.Image(image)
            zenith_angle=image.get('SOLAR_ZENITH_ANGLE')
            sun_elevation = image.get("SUN_ELEVATION")
            time_start=image.get('system:time_start')
            _date=ee.Date(time_start)
            _hour=ee.Number(_date.get('hour'))
            _minuts = ee.Number(_date.get('minutes'))
            date_string=_date.format('YYYY-MM-dd')

            #ENDMEMBERS
            p_top_NDVI=ee.Number(NDVI_cold)
            p_coldest_Ts=ee.Number(Ts_cold)
            p_lowest_NDVI=ee.Number(NDVI_hot)
            p_hottest_Ts=ee.Number(Ts_hot)

            #GEOMETRY
            geometryReducer=image.geometry().bounds()

            #AIR TEMPERATURE [C]
            T_air = image.select('AirT_G');

            #WIND SPEED [M S-1]
            ux= image.select('ux_G');

            #RELATIVE HUMIDITY [%]
            UR = image.select('RH_G');

            #NET RADIATION 24H [W M-2]
            Rn24hobs = image.select('Rn24h_G');

            #SRTM DATA ELEVATION
            srtm = ee.Image(Constants.SRTM_ELEVATION_COLLECTION).clip(geometryReducer)
            z_alt = srtm.select('elevation')
            slope = ee.Terrain.slope(z_alt)

            #SPECTRAL IMAGES (NDVI, EVI, SAVI, LAI, T_LST, e_0, e_NB, long, lat)
            image=fexp_spec_ind(image, scale=scale)

            #LAND SURFACE TEMPERATURE
            image=LST_DEM_correction(image, z_alt, T_air, UR,sun_elevation,_hour,_minuts)
            LandT_G = image.select('T_LST_DEM').rename('LandT_G')

            #COLD PIXEL
            d_cold_pixel=fexp_cold_pixel(image, geometryReducer, p_top_NDVI, p_coldest_Ts)

            #COLD PIXEL NUMBER
            n_Ts_cold = ee.Number(d_cold_pixel.get('temp'))

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
                                               d_hot_pixel, date_string,geometryReducer, scale=scale)

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
                    'mm', 'dd', 'yyyy',
                    'R', 'GR', 'B',
                ]
            return (
                image
                    .reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=self.coordinate,
                        scale=scale,
                        maxPixels=1e14)
                    .select(cols)
            )


        ic5 = (
            collection_l5
                .map(f_albedoL5L7)
                .map(verifyMeteoAvail)
                .filter(ee.Filter.gt('meteo_count', 0))
                .map(lambda image: get_meteorology(image, scale=scale))
                .map(retrieveETandMeteo)
        )
        self.ETandMeteo = ic5

        ic7 = (
            collection_l7
                .map(f_albedoL5L7)
                .map(verifyMeteoAvail)
                .filter(ee.Filter.gt('meteo_count', 0))
                .map(lambda image: get_meteorology(image, scale=scale))
                .map(retrieveETandMeteo)
        )
        self.ETandMeteo = self.ETandMeteo.merge(ic7)

        ic8 = (
            collection_l8
                .map(f_albedoL8)
                .map(verifyMeteoAvail)
                .filter(ee.Filter.gt('meteo_count', 0))
                .map(lambda image: get_meteorology(image, scale=scale))
                .map(retrieveETandMeteo)
        )
        self.ETandMeteo = self.ETandMeteo.merge(ic8)
