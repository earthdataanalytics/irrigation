import unittest
import sys
import os
import ee
# add the path to the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../geesebal')))
from geesebal import TimeSeries_bcj


# sebalTS = TimeSeries_bcj(start_yr+yr_inc, start_mo, start_dy,
#                                         start_yr+yr_inc, end_mo, end_dy,
#                                         max_cloud_cover, single_location,
#                                         buffersize=buffsize,
#                                         calcRegionalET=calc_ET_region
#                                      )

# sebalTS = sebalTS.ETandMeteo.map(lambda x: x.set('loc_type', loc_type))

# evapotranspirationAndMeteo = sebalTS.ETandMeteo

# create a test class
class TestTimeSeries_bcj(unittest.TestCase):
    ## class to run code on the top
    def setUp(self):
        self.year_i = 2018
        self.month_i = 1
        self.day_i = 1
        self.year_e = 2018
        self.month_e = 4
        self.day_e = 1
        self.cloud_cover = 20
        self.buffersize = 90
        self.NDVI_cold = 5
        self.Ts_cold = 20
        self.NDVI_hot = 10
        self.Ts_hot = 20
        self.calcRegionalET = False
        
        self.geometry = ee.Geometry.Polygon(
        [[[-121.81384438900623, 38.542182094500255],
        [-121.81384438900623, 38.524994136128704],
        [-121.78534860043202, 38.524994136128704],
        [-121.78534860043202, 38.542182094500255]]], None, False)
        
        self.coordinates = ee.Geometry.Point([-121.79909699471962, 38.53358811531448])
       
    
    def test_TimeSeries_bcj(self):
        self.setUp()
        idx = 0
        aoi = ee.FeatureCollection(self.geometry)
        max_points = 10000 # set arbitrarily high to capture all values

        # ensure there is a defined buffer zone around each location
        locs_list = aoi.toList(max_points)
        loc_type = ee.Feature(locs_list.get(idx)).get('POINT_TYPE')
        
        sebalTS =  TimeSeries_bcj(
            year_i=self.year_i,
            month_i=self.month_i,
            day_i=self.day_i,
            year_e=self.year_e,
            month_e=self.month_e,
            day_e=self.day_e,
            cloud_cover=self.cloud_cover,
            coordinate=self.coordinates,
            buffersize=self.buffersize,
            NDVI_cold=self.NDVI_cold,
            Ts_cold=self.Ts_cold,
            NDVI_hot=self.NDVI_hot,
            Ts_hot=self.Ts_hot,
            calcRegionalET=self.calcRegionalET
                                        )
        
        etFeature = sebalTS.ETandMeteo.map(lambda x: x.set('loc_type', loc_type))
        
        # print(sebalTS.getInfo())
        # # print max LST_NW value
        # print("Firts = ")
        
        etFeatureInfo = etFeature.getInfo()["features"]
        et_values = []
        for feature in etFeatureInfo:
       
       
            image = feature["properties"]["image"]["properties"]
            image_id = image["id"]
            date = image["date"]
            version = image["version"]
            image_bands_max = image["image_bands_max"]
            properties = feature["properties"]['msg']["properties"]
            print("")
            print("============ BANDS CHECK ==================")
            print(f"Image ID = {image_id}")
            print(f"Date = {date}")
            print(image_bands_max)
            print("============ BANDS CHECK ==================")
            print("")
            print("")
            print("============= SUMMARY ====================")
            print(f"Image ID = {image_id}")
            print(f"status = {properties['status']}")
            print(f"Date = {properties['date']}")
            print(f"ET_24H = {properties['ET_24h']}")
            print(f"AirT_G = {properties['AirT_G']}")
            print(f"NDVI = {properties['NDVI']}")
            print("============= SUMMARY ====================")
            
            et_values.append([properties['date'],properties['ET_24h']])
            
            
        # order et_values by date
        et_values.sort(key=lambda x: x[0])

        # Print the ET values
        print("ET Values = ")
        print(et_values)
if __name__ == '__main__':
    unittest.main()