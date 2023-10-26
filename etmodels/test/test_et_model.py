import unittest
import sys
import os
import ee
import datetime
import pandas as pd
from PIL import Image as PILImage
import requests

# add the path to the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ssebop")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../ssebop/refetgee"))
)

from daily import Daily, NASA_ET0, GFS_ET0
from etmodels.test.time_controller import TimeController
from collection import Collection
from IPython.display import Image

time_controller = TimeController()


# create a test class
class TestSsebop(unittest.TestCase):
    ## class to run code on the top

    def setUp(self):
        ee.Initialize()
        self.ndvi_palette = ["#EFE7E1", "#003300"]
        self.et_palette = [
            "DEC29B",
            "E6CDA1",
            "EDD9A6",
            "F5E4A9",
            "FFF4AD",
            "C3E683",
            "6BCC5C",
            "3BB369",
            "20998F",
            "1C8691",
            "16678A",
            "114982",
            "0B2C7A",
        ]

        self.image_size = 768
        self.landsat_cs = 30
        self.start_date = "2023-10-01"
        self.end_date = "2023-10-10"

        # self.et_reference_source = "projects/openet/reference_et/cimis/daily"
        # self.et_reference_band = "etr_asce"
        # self.et_reference_source = "ECMWF/ERA5_LAND/DAILY"
        self.et_reference_band = "etr"
        self.et_reference_factor = 1.0
        self.et_reference_resample = "nearest"
        self.et_reference_date_type = "daily"
        self.own_et_model = "NASA/GLDAS/V021/NOAH/G025/T3H"

        # Only keep images with an average cloud cover less than
        # Cloud cover filter parameter is not being passed in (yet)
        self.cloud_cover = 20

        # Number of extra days (at start and end) to include in interpolation
        self.interp_days = 32

        # Interpolation method - currently only LINEAR is supported
        self.interp_method = "LINEAR"

        self.test_point = ee.Geometry.Point([-4.587895032393094, 37.87202372474622])

        self.study_area = ee.Geometry.Polygon(
            [
                [
                    [-9.139332431531301, 43.49479932356515],
                    [-9.139332431531301, 36.32621662111366],
                    [1.8030503809686982, 36.32621662111366],
                    [1.8030503809686982, 43.49479932356515],
                ]
            ],
            None,
            False,
        )

        self.study_region = self.study_area.bounds(1, "EPSG:4326")
        self.study_crs = "EPSG:32610"

    @time_controller.timeit
    def test_GFS_ET0_model(self):
        return 
        self.setUp()
        gfs_et0 = GFS_ET0(
            study_region=self.study_region,
            start_date=self.start_date,
            end_date=self.end_date,
            scale=10,
            debug=False,
        )
        
        et0_collection = gfs_et0.calculate_eto_daily()
        
        def create_feature(image):
            feature = ee.Feature(self.study_region, {
                "datetime": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd"),
                "et0": ee.Number(image.select("et0").reduceRegion(
                    ee.Reducer.mean(), self.study_region, scale=27830
                ).get("et0")
                )                
            })
            return feature
            
        et0_collection = et0_collection.map(create_feature).getInfo()
        

        #et0_collection.get("features")[i]["properties"] into a dataframe
        et0_df = pd.DataFrame(et0_collection.get("features"))
        et0_df = pd.DataFrame(et0_df["properties"].to_list())
        
        print(et0_df)
        
        
      
        
    @time_controller.timeit
    def test_ET_model(self):
        self.setUp()

        self.setUp()
        gfs_et0 = NASA_ET0(
            study_region=self.study_region,
            start_date=self.start_date,
            end_date=self.end_date,
            scale=10,
            debug=False,
        )
        et0_collection = gfs_et0.calculate_eto_daily()
        
        def create_feature(image):
            feature = ee.Feature(self.study_region, {
                "datetime": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd"),
                "et0": ee.Number(image.select("et0").reduceRegion(
                    ee.Reducer.mean(), self.study_region, scale=27830
                ).get("et0")
                )                
            })
            return feature
            
        et0_collection = et0_collection.map(create_feature).getInfo()
        

        #et0_collection.get("features")[i]["properties"] into a dataframe
        et0_df = pd.DataFrame(et0_collection.get("features"))
        et0_df = pd.DataFrame(et0_df["properties"].to_list())
        
        
        
        print(et0_df)


if __name__ == "__main__":
    unittest.main()
