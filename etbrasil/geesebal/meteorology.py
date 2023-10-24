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
#   - retrieve precipitation data
#   - check for existence of weather data
#   - Converted to run all code on GEE Server instead of Client
#
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------#

#PYTHON PACKAGES
#Call EE
import ee
from .constants import Constants

#GLOBAL LAND DATA ASSIMILATION SYSTEM (GLDAS)
#1984 TO 1999-12-31 - GLDAS 2.0
#2000 TO PRESENT - GLDAS 2.1
#3h, 6h, 9h, 12h, 15h, 18h, 21h, 00h

def verifyMeteoAvail(image):
    DATASET = ee.ImageCollection(Constants.WEATHER_COLLECTION)

    time_start = image.get('system:time_start')
    TIME_START_NUM=ee.Number(time_start)
    PREVIOUS_TIME=TIME_START_NUM.subtract(3*60*60*1000)
    # NEXT_TIME=TIME_START_NUM.add(3*60*60*1000)

    PREVIOUS_IMAGE=(DATASET.filter(ee.Filter.date(PREVIOUS_TIME,TIME_START_NUM))
                          .limit(1, 'system:time_start', False)) #.first())

    return image.set('meteo_count', PREVIOUS_IMAGE.aggregate_count('system:time_start'))

def get_meteorology(image, scale=None):
    DATASET = ee.ImageCollection(Constants.WEATHER_COLLECTION)

    #LINEAR INTERPOLATION
    time_start = image.get('system:time_start')
    TIME_START_NUM=ee.Number(time_start)
    PREVIOUS_TIME=TIME_START_NUM.subtract(3*60*60*1000)
    NEXT_TIME=TIME_START_NUM.add(3*60*60*1000)

    PREVIOUS_IMAGE=(DATASET.filter(ee.Filter.date(PREVIOUS_TIME,TIME_START_NUM))
                          .limit(1, 'system:time_start', False).first())

    NEXT_IMAGE=(DATASET.filter(ee.Filter.date(TIME_START_NUM,NEXT_TIME))
                          .limit(1, 'system:time_start', False).first())

    IMAGE_PREVIOUS_TIME= ee.Number(PREVIOUS_IMAGE.get('system:time_start'))

    IMAGE_NEXT_TIME=ee.Number(NEXT_IMAGE.get('system:time_start'))

    DELTA_TIME=(TIME_START_NUM.subtract(IMAGE_PREVIOUS_TIME)).divide(IMAGE_NEXT_TIME.subtract(IMAGE_PREVIOUS_TIME))

    #DAY OF THE YEAR
    dateStr = ee.Date(time_start)
    doy = dateStr.getRelative('day', 'year')
    Pi=ee.Number(3.14)

    #INVERSE RELATIVE DISTANCE EARTH-SUN
    #ALLEN ET AL.(1998)
    d1 =  ee.Number(2).multiply(ee.Number(Pi)).divide(ee.Number(365))
    d2 = d1.multiply(doy)
    d3 = d2.cos()
    dr = ee.Number(1).add(ee.Number(0.033).multiply(d3))

    #SOLAR DECLINATION [RADIANS]
    #ASCE REPORT (2005)
    e1 =  ee.Number(2).multiply(ee.Number(Pi)).multiply(doy)
    e2 = e1.divide(ee.Number(365))
    e3 = e2.subtract(ee.Number(1.39))
    e4 = e3.sin()
    solar_dec = ee.Number(0.409).multiply(e4)

    #GET COORDINATES
    i_Rn24_coord =DATASET.first().addBands([ee.Image.pixelLonLat()])

    #SUNSET  HOUR ANGLE [RADIANS]
    #ASCE REPORT (2005)
    i_lat_rad = (i_Rn24_coord.select('latitude').multiply(ee.Number(Pi))).divide(ee.Number(180))
    i_sun_hour = i_lat_rad.expression(
    'acos(- tan(lat)* tan(solar_dec))', {
          'lat' : i_lat_rad,
          'solar_dec' : solar_dec}).rename('sun_hour')

    #SOLAR CONSTANT
    gsc = ee.Number(4.92) #[MJ M-2 H-1]

    #EXTRATERRESTRIAL RADIATION 24H  [MJ M-2 D-1]
    #ASCE REPORT (2005)
    i_Ra_24h = i_sun_hour.expression(
    '(24/pi)*Gcs * dr * ( (omega * sin(lat_rad)* sin(solar_dec)) +  (cos(lat_rad) * cos(solar_dec) * sin(omega)))*11.5740',{
          'pi' : ee.Number(Pi),
          'Gcs' : gsc,
          'dr': dr,
          'omega': i_sun_hour,
          'solar_dec': solar_dec,
          'lat_rad': i_lat_rad}).rename('Ra_24h')

    i_Ra_24h=i_Ra_24h.select('Ra_24h').reduce(ee.Reducer.mean())

    #INCOMING SHORT-WAVE RADIATION DAILY EAN [W M-2]
    i_Rs_24h = ee.ImageCollection(Constants.WEATHER_COLLECTION)\
                .filterDate(ee.Date(time_start).advance(-11,'hour'),ee.Date(time_start).advance(13,'hour'))\
                .select("surface_solar_radiation_downwards_hourly")\
                .sum()\
                .divide(86400).rename('SW_Down')

    # TASUMI
    i_albedo_ls =image.select('ALFA')

    #NET RADIATION 24H [W M-2]
    #BRUIN (1982)
    i_Rn_24h = i_Ra_24h.expression(
    '((1 - albedo) * i_Rs_24h) - (Cs * (i_Rs_24h / i_Ra_24h))',{
           'albedo' : i_albedo_ls,
           'i_Rs_24h' : i_Rs_24h,
           'Cs': ee.Number(110), #CONSTANT
           'i_Ra_24h': i_Ra_24h}).rename('Rn24h_G')

    # AIR TEMPERATURE [K]
    tair_c = NEXT_IMAGE.select('temperature_2m')\
        .subtract(PREVIOUS_IMAGE.select('temperature_2m'))\
        .multiply(DELTA_TIME).add(PREVIOUS_IMAGE.select('temperature_2m'))\
        .rename('AirT_G')

    # WIND SPEED [M S-1]
    wind_u = NEXT_IMAGE.select('u_component_of_wind_10m')\
        .subtract(PREVIOUS_IMAGE.select('u_component_of_wind_10m'))\
        .multiply(DELTA_TIME).add(PREVIOUS_IMAGE.select('u_component_of_wind_10m'))

    wind_v = NEXT_IMAGE.select('v_component_of_wind_10m')\
        .subtract(PREVIOUS_IMAGE.select('v_component_of_wind_10m'))\
        .multiply(DELTA_TIME).add(PREVIOUS_IMAGE.select('v_component_of_wind_10m'))

    # TODO: CGM check if the select calls are needed
    wind_med = wind_u.expression(
        'sqrt(ux_u ** 2 + ux_v ** 2)', {'ux_u': wind_u, 'ux_v': wind_v},
    ).rename('ux_G')

    wind_med = wind_med.expression(
        'ux * (4.87) / log(67.8 * z - 5.42)', {'ux': wind_med, 'z': 10.0}).rename('ux_G')

    # PRESSURE [PA] CONVERTED TO KPA
    # tdp = NEXT_IMAGE.select('dewpoint_temperature_2m')\
    #     .subtract(PREVIOUS_IMAGE.select('dewpoint_temperature_2m'))\
    #     .multiply(DELTA_TIME).add(PREVIOUS_IMAGE.select('dewpoint_temperature_2m'))\
    #     .rename('tdp')

    # ACTUAL VAPOR PRESSURE [KPA]
    #PRESSURE [PA] CONVERTED TO KPA
    i_P_med= NEXT_IMAGE.select('surface_pressure').subtract(PREVIOUS_IMAGE.select('surface_pressure')).multiply(DELTA_TIME).add(PREVIOUS_IMAGE.select('surface_pressure')).divide(ee.Number(1000))

    # SPECIFIC HUMIDITY [KG KG-1]
    i_q_med =ee.ImageCollection(Constants.WEATHER_NASA_GLDAS_V021_NOAH_G025_T3H).select(['Qair_f_inst'],["specific_humidity"]).filterBounds(image.geometry()).filter(ee.Filter.date(ee.Date(time_start),ee.Date(time_start).advance(1,'day'))).first()
    ea = i_P_med.expression('(1/0.622)*Q*P',{
            'Q': i_q_med,
            'P':i_P_med}).rename('i_ea')
    
    # SATURATED VAPOR PRESSURE [KPA]
    esat = tair_c.expression(
        '0.6108 * (exp((17.27 * T_air) / (T_air + 237.3)))', {'T_air': tair_c.subtract(273.15)})

    # RELATIVE HUMIDITY (%)
    rh = ea.divide(esat).multiply(100).rename('RH_G')

    # Resample
    tair_c = tair_c.subtract(273.15).resample('bilinear')
    wind_med = wind_med.resample('bilinear')
    rh = rh.resample('bilinear')
    swdown24h = i_Rs_24h.resample('bilinear')
    rn24h = i_Rn_24h.resample('bilinear')

    #CONCATENATES IMAGES
    crs = image.projection()
    target_scale = scale if scale else crs.nominalScale()
    col_meteorology = ee.Image.cat(rn24h, tair_c, rh, wind_med, swdown24h)
    col_meteorology = col_meteorology.reproject(crs, scale=target_scale)

    out = image.addBands(col_meteorology)

    return out

# NOTE: only change scale if you know what you're doing. 
# Reducing the scale will increase the number of pixels in the image and the processing time
def retrievePrecip(metadate, location, window_days=10, scale=None):
    startDate = ee.Date(metadate).advance(-window_days, 'day')
    endDate = ee.Date(metadate).advance(-1, 'day')

    collection = ee.ImageCollection(Constants.NOAA_CFSV2_6H)
    
    # print("Target scale = ", ee.Image(collection.first()).select('Precipitation_rate_surface_6_Hour_Average').projection().nominalScale().getInfo())
    print("Image id = ", ee.Image(collection.first()).select('Precipitation_rate_surface_6_Hour_Average').getInfo()['id'])
    # function to sum the values by day
    def sumPrecip(dayOffset, start_):
        start = start_.advance(dayOffset, 'days')
        end = start.advance(1, 'days')
        return collection.select('Precipitation_rate_surface_6_Hour_Average') \
                      .filterDate(start, end) \
                      .sum() \
                      .set('system:time_start', start.millis())

    # function to extract the precipitation values
    def extractPrecip(image):
        # convert from kg/m^2/s to mm/s over 6 hours
        precip_conversion_factor = ee.Number(6 * 60 * 60) # num hours in sample * num mins * num secs

        target_scale = scale if scale else image.projection().nominalScale()
        

        precip_value = image.select('Precipitation_rate_surface_6_Hour_Average').reduceRegion(
          reducer=ee.Reducer.first(),
          geometry=location.centroid(),
          scale=ee.Number(target_scale)
        ).get('Precipitation_rate_surface_6_Hour_Average')
        precip_value = ee.Number(precip_value)

        return ee.Feature(None, {
          'precip_value': precip_value.multiply(precip_conversion_factor),
          'date': image.date().format('yyyy-MM-dd'),
          'system:time_start': image.date().millis()
        })

    # create a list of dates to use to extract precip values
    numberOfDays = endDate.difference(startDate, 'days')
    daily = ee.ImageCollection(
                        ee.List.sequence(0, numberOfDays) \
                            .map(lambda x: sumPrecip(x, startDate))
                    )

    # calculate the total precipitation for each of prior X days
    # extract as features
    precip_ts = ee.FeatureCollection(daily.map(extractPrecip)) \
                  .sort('date', opt_ascending=False)

    return precip_ts.aggregate_array('precip_value')

def retrievePrecipImage(metadate, image, precip_window=10, cum_precip_window=3):
    # this method is intended to be used separately from the generalized ETandMeteo method
    # goal being to speed up the data retrieval
    startDate = ee.Date(metadate).advance(-precip_window, 'day')
    endDate = ee.Date(metadate).advance(-1, 'day')

    collection = ee.ImageCollection("NOAA/CFSV2/FOR6H") \
                    .filterBounds(image.geometry().bounds())

    # function to sum the values by day
    def sumPrecip(dayOffset, start_):
        precip_conversion_factor = ee.Image(6 * 60 * 60) # num hours in sample * num mins * num secs
        start = start_.advance(dayOffset, 'days')
        end = start.advance(1, 'days')
        return collection.select('Precipitation_rate_surface_6_Hour_Average') \
                      .filterDate(start, end) \
                      .sum() \
                      .multiply(precip_conversion_factor) \
                      .rename('daily_rain') \
                      .set('system:time_start', start.millis()) \
                      .set('custom:index', (ee.Number(precip_window).subtract(dayOffset)))

    # create a list of dates to use to extract precip values
    numberOfDays = endDate.difference(startDate, 'days')
    daily = ee.ImageCollection(
                        ee.List.sequence(0, numberOfDays) \
                            .map(lambda x: sumPrecip(x, startDate))
                    )

    def maskLowPrecip(img):
        # creates image from difference between retrieval
        # date (metadate) and the daily-precip reading date (img)
        # then creates mask where rain less than threshold
        # outer function then takes minimum # days (since last rain)
        rain_threshold = ee.Number(0.254) # 0.254 mm = 0.01 inches of rainfall in a day, source:  Paolo
        img = ee.Image(img)
        delta = ee.Date(metadate).difference(img.date(), 'day')
        mask = img.gt(rain_threshold)
        out = ee.Image(delta).toFloat().updateMask(mask)
        ten = ee.Image(ee.Number(10))
        return out.unmask(ten) # replace where the image was masked with a 10
                                # so that there is a value for last_rain and
                                # the result is not masked out

    # number of days since last rain
    last_rain = daily \
                    .map(maskLowPrecip) \
                    .min() \
                    .rename('last_rain') \
                    .clip(image.geometry().bounds())

    # cumulative precipation of last 3 days (agreed in team meeting)
    cum_precip = daily \
                    .limit(cum_precip_window, 'custom:index') \
                    .sum() \
                    .rename('sum_precip_priorX') \
                    .clip(image.geometry().bounds())

    return last_rain, cum_precip

if __name__ == "__main__":
    get_meteorology()
