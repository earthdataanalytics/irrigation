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
        self.start_date = "2023-01-01"
        self.end_date = "2023-02-01"

        self.collections = [
            "LANDSAT/LC09/C02/T1_L2",
            "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT/LE07/C02/T1_L2",
            "LANDSAT/LT05/C02/T1_L2",
        ]

        # self.et_reference_source = "projects/openet/reference_et/cimis/daily"
        # self.et_reference_band = "etr_asce"
        self.et_reference_source = "ECMWF"
        self.et_reference_band = "et0"
        self.et_reference_factor = 1.0
        self.et_reference_resample = "nearest"
        self.et_reference_date_type = "daily"
        # self.own_et_model="ECMWF/ERA5_LAND/HOURLY"

        # Only keep images with an average cloud cover less than
        # Cloud cover filter parameter is not being passed in (yet)
        self.cloud_cover = 20

        # Number of extra days (at start and end) to include in interpolation
        self.interp_days = 32

        # Interpolation method - currently only LINEAR is supported
        self.interp_method = "LINEAR"

        ## DAVIS TEST POINT
        # self.test_point = ee.Geometry.Point([-121.80027912713243, 38.53764735054985])

        # self.study_area = ee.Geometry.Polygon(
        #     [
        #         [
        #             [-121.84027912713243, 38.5592113359509],
        #             [-121.84027912713243, 38.50764735054985],
        #             [-121.75376179314806, 38.50764735054985],
        #             [-121.75376179314806, 38.5592113359509],
        #         ]
        #     ],
        #     None,
        #     False,
        # )

        # CORDOBA RAINFED TEST POINT
        # self.test_point = ee.Geometry.Point([-4.587895032393094, 37.87202372474622])

        # self.study_area = ee.Geometry.Polygon(
        #     [
        #         [
        #             [-4.6535445911386715, 37.901649775506776],
        #             [-4.6535445911386715, 37.834434812504895],
        #             [-4.541621373365234, 37.834434812504895],
        #             [-4.541621373365234, 37.901649775506776],
        #         ]
        #     ],
        #     None,
        #     False,
        # )

        ## TEST POINT IN EGYPT
        ## BEST DATES BETWEEN JANUARY AND MARCH
        self.test_point = ee.Geometry.Point([28.24507697531175, 22.526226362429686])

        self.study_area = ee.Geometry.Polygon(
            [
                [
                    [28.1248764877901, 22.58011855501831],
                    [28.1248764877901, 22.38597531123633],
                    [28.3006577377901, 22.38597531123633],
                    [28.3006577377901, 22.58011855501831],
                ]
            ],
            None,
            False,
        )

        self.study_region = self.study_area.bounds(1, "EPSG:4326")
        self.study_crs = "EPSG:4326"

    @time_controller.timeit
    def test_TimeSeries(self):
        self.setUp()
        debug = True
        profile_enabled = False

        def run_test():
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
                # own_et_model=self.own_et_model,
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
                variables=[
                    "ndvi",
                    "et",
                    "et_reference",
                    "et_fraction",
                    "lst",
                    "tmax",
                    "tmin",
                    "actual_vapor_pressure",
                    "solar_radiation",
                    "wind_speed",
                    "rain",
                ]
            )

            overpass_df = get_region_df(
                overpass_coll.getRegion(self.test_point, scale=30).getInfo()
            )
            print(overpass_df)
            print("")
            print(overpass_df[["et", "et_reference"]].sum())
            if debug:
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

                ndvi_img = PILImage.open(requests.get(ndvi_url, stream=True).raw)
                ndvi_img.show()

                # et_fraction_urk = (
                #     ee.Image(overpass_coll.select(["et_fraction"]).mean())
                #     .reproject(crs=self.study_crs, scale=30)
                #     .getThumbURL(
                #         {
                #             "min": 0.0,
                #             "max": 1.2,
                #             "palette": ",".join(self.et_palette),
                #             "region": self.study_region,
                #             "dimensions": self.image_size,
                #         }
                #     )
                # )

                # et_fraction_img = PILImage.open(
                #     requests.get(et_fraction_urk, stream=True).raw
                # )

                # et_fraction_img.show()

                # daily_coll = model_obj.interpolate(
                #     t_interval="daily",
                #     variables=["et", "et_reference", "et_fraction"],
                #     interp_method=self.interp_method,
                #     interp_days=self.interp_days,
                # )

                # daily_df = get_region_df(
                #     daily_coll.getRegion(self.test_point, scale=30).getInfo()
                # )

                # print(daily_df)
                # print("")
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

                # image_url = (
                #     ee.Image(monthly_coll.select(["et"]).sum())
                #     .reproject(crs=self.study_crs, scale=100)
                #     .getThumbURL(
                #         {
                #             "min": 0.0,
                #             "max": 350,
                #             "palette": self.et_palette,
                #             "region": self.study_region,
                #             "dimensions": self.image_size,
                #         }
                #     )
                # )
                # et_img = PILImage.open(requests.get(image_url, stream=True).raw)
                max_et = monthly_df["et"].max()
                image_url = (
                    ee.Image(monthly_coll.select(["et"]).sum())
                    # .reproject(crs=self.study_crs, scale=100)
                    .getThumbURL(
                        {
                            "min": 0.0,
                            "max": max_et,
                            "palette": self.et_palette,
                            "region": self.study_region,
                            "dimensions": self.image_size,
                        }
                    )
                )
                # see image in matplotlib
                et_reference_img = PILImage.open(
                    requests.get(image_url, stream=True).raw
                )
                et_reference_img.show()
                # et_reference_img.show()

        if profile_enabled:
            with ee.profilePrinting():
                run_test()
        else:
            run_test()


if __name__ == "__main__":
    unittest.main()
