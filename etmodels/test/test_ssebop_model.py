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
        self.start_date = "2023-04-01"
        self.end_date = "2023-06-01"

        self.collections = [
            "LANDSAT/LC09/C02/T1_L2",
            "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT/LE07/C02/T1_L2",
            "LANDSAT/LT05/C02/T1_L2",
        ]

        self.et_reference_source = "projects/openet/reference_et/cimis/daily"
        self.et_reference_band = "etr_asce"
        self.et_reference_factor = 1.0
        self.et_reference_resample = "nearest"
        self.et_reference_date_type = "daily"

        # Only keep images with an average cloud cover less than
        # Cloud cover filter parameter is not being passed in (yet)
        self.cloud_cover = 20

        # Number of extra days (at start and end) to include in interpolation
        self.interp_days = 32

        # Interpolation method - currently only LINEAR is supported
        self.interp_method = "LINEAR"

        self.test_point = ee.Geometry.Point([-121.79909699471962, 38.53358811531448])

        self.study_area = ee.Geometry.Polygon(
            [
                [
                    [-121.91601164381566, 38.61696084232722],
                    [-121.91601164381566, 38.42705725482288],
                    [-121.62624723951879, 38.42705725482288],
                    [-121.62624723951879, 38.61696084232722],
                ]
            ],
            None,
            False,
        )

        self.study_region = self.study_area.bounds(1, "EPSG:4326")
        self.study_crs = "EPSG:32610"

    @time_controller.timeit
    def test_TimeSeries(self):
        self.setUp()

        model_obj = Collection(
            collections=self.collections,
            et_reference_source=self.et_reference_source,
            et_reference_band=self.et_reference_band,
            et_reference_factor=self.et_reference_factor,
            et_reference_resample=self.et_reference_resample,
            et_reference_date_type=self.et_reference_date_type,
            start_date=self.start_date,
            end_date=self.end_date,
            geometry=self.test_point,
            cloud_cover_max=20,
            # filter_args={},
        )

        print(model_obj.get_image_ids())

        def get_region_df(info):
            """Convert the output of getRegions to a pandas dataframe"""
            col_dict = {}
            info_dict = {}
            for i, k in enumerate(info[0][4:]):
                col_dict[k] = i + 4
                info_dict[k] = {}

            for row in info[1:]:
                date = datetime.datetime.utcfromtimestamp(row[3] / 1000.0).strftime(
                    "%Y-%m-%d"
                )
                for k, v in col_dict.items():
                    info_dict[k][date] = row[col_dict[k]]

            return pd.DataFrame.from_dict(info_dict)

        overpass_coll = model_obj.overpass(
            variables=["ndvi", "et", "et_reference", "et_fraction"]
        )

        overpass_df = get_region_df(
            overpass_coll.getRegion(self.test_point, scale=30).getInfo()
        )
        ndvi_url = (
            ee.Image(overpass_coll.select(["ndvi"]).mean())
            .reproject(crs=self.study_crs, scale=30)
            .getThumbURL(
                {
                    "min": -0.1,
                    "max": 0.9,
                    "palette": ",".join(self.ndvi_palette),
                    "region": self.study_region,
                    "dimensions": self.image_size,
                }
            )
        )

        print(overpass_df)
        print("")
        print(overpass_df[["et", "et_reference"]].sum())

        ndvi_img = PILImage.open(requests.get(ndvi_url, stream=True).raw)
        ndvi_img.show()

        et_fraction_urk = (
            ee.Image(overpass_coll.select(["et_fraction"]).mean())
            .reproject(crs=self.study_crs, scale=30)
            .getThumbURL(
                {
                    "min": 0.0,
                    "max": 1.2,
                    "palette": ",".join(self.et_palette),
                    "region": self.study_region,
                    "dimensions": self.image_size,
                }
            )
        )

        et_fraction_img = PILImage.open(requests.get(et_fraction_urk, stream=True).raw)

        et_fraction_img.show()

        daily_coll = model_obj.interpolate(
            t_interval="daily",
            variables=["et", "et_reference", "et_fraction"],
            interp_method=self.interp_method,
            interp_days=self.interp_days,
        )

        daily_df = get_region_df(
            daily_coll.getRegion(self.test_point, scale=30).getInfo()
        )

        print(daily_df)
        print("")
        monthly_coll = model_obj.interpolate(
            t_interval="monthly",
            variables=["et", "et_reference", "et_fraction"],
            interp_method=self.interp_method,
            interp_days=self.interp_days,
        )

        monthly_df = get_region_df(
            monthly_coll.getRegion(self.test_point, scale=30).getInfo()
        )
        print(monthly_df)

        image_url = (
            ee.Image(monthly_coll.select(["et"]).sum())
            .reproject(crs=self.study_crs, scale=100)
            .getThumbURL(
                {
                    "min": 0.0,
                    "max": 350,
                    "palette": self.et_palette,
                    "region": self.study_region,
                    "dimensions": self.image_size,
                }
            )
        )
        et_img = PILImage.open(requests.get(image_url, stream=True).raw)

        image_url = (
            ee.Image(monthly_coll.select(["et_reference"]).sum())
            .reproject(crs=self.study_crs, scale=100)
            .getThumbURL(
                {
                    "min": 0.0,
                    "max": 350,
                    "palette": self.et_palette,
                    "region": self.study_region,
                    "dimensions": self.image_size,
                }
            )
        )
        # see image in matplotlib
        et_reference_img = PILImage.open(requests.get(image_url, stream=True).raw)

        et_img.show()
        et_reference_img.show()

        print("done")


if __name__ == "__main__":
    unittest.main()
