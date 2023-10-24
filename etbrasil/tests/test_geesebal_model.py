import unittest
import sys
import os
import ee

# add the path to the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../geesebal')))
from geesebal import TimeSeries
from utils.time_controller import TimeController

time_controller = TimeController()


# sebalTS = TimeSeries(start_yr+yr_inc, start_mo, start_dy,
#                                         start_yr+yr_inc, end_mo, end_dy,
#                                         max_cloud_cover, single_location,
#                                         buffersize=buffsize,
#                                         calcRegionalET=calc_ET_region
#                                      )

# sebalTS = sebalTS.ETandMeteo.map(lambda x: x.set('loc_type', loc_type))

# evapotranspirationAndMeteo = sebalTS.ETandMeteo

# create a test class
class TestTimeSeries(unittest.TestCase):
    ## class to run code on the top
    def setUp(self):
        self.year_i = 2023
        self.month_i = 5
        self.day_i = 1
        self.year_e = 2023
        self.month_e = 6
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
       
    @time_controller.timeit
    def test_TimeSeries(self):
        self.setUp()
        debug = True
        idx = 0
        aoi = ee.FeatureCollection(self.geometry)
        max_points = 10000 # set arbitrarily high to capture all values

        # ensure there is a defined buffer zone around each location
        locs_list = aoi.toList(max_points)
        loc_type = ee.Feature(locs_list.get(idx)).get('POINT_TYPE')
        
        sebalTS =  TimeSeries(
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
            calcRegionalET=self.calcRegionalET,
            debug=debug
                                        )
        if(debug):
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
            
            # NOTE: Current values for the test are:
            # --- from 2019-01-01 to 2019-04-01 ---
            # 2019-01-27: 1.53 (Time: scale 30: 2 minutes 120 seconds, scale 40: 45 seconds)
            # 2019-03-06: 0.89 (CONSIDER: There is an empty square near the plot that we are studying in the test
            # so when we increase the resolution of the reducer, we get a different value)
            # --------------------------------------
            # --- from 2023-05-01 to 2023-06-01 --- 5.445317766717414 5.804835841711025 5.92412042834145 4.888227670106112
            # 2023-05-11: (30 - 6.520  100 - 6.28)
            # 2023-05-14: (30 - 5.21 100 - 5.44)
            # 2023-05-16: (30 - 5.52 100 - 5.80)
            # 2023-05-22: (30 - 5.71 100 - 5.92)
            # 2023-05-30: (30 - 4.44 100 - 4.88)
            # 30 --> 2 min 134 secs
            # 20000 --> 1 min 102 secs 
            # --------------------------------------
            
            print("Actual ET Values = ")
            print("2019-01-27: 1.53")
            print("2019-03-06: 0.89")
            print("2023-05-11: 6.520")
if __name__ == '__main__':
    unittest.main()