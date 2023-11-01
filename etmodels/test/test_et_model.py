import unittest
import sys
import os
import ee
import datetime
import pandas as pd
from PIL import Image as PILImage
import requests
import time

# add the path to the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ssebop")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../ssebop/refetgee"))
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))


from daily import Calculate_ET0
from etmodels.test.time_controller import TimeController
from collection import Collection
from IPython.display import Image
from batch import ee_export_image_collection_to_asset

time_controller = TimeController()


# create a test class
class TestSsebop(unittest.TestCase):
    ## class to run code on the top

    def setUp(self):
        ee.Initialize()
        self.task_name = "test_europe"
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
        self.start_date = "2023-04-10"
        self.end_date = "2023-05-12"

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

        self.test_point = ee.Geometry.Point([-4.59, 37.86])

        """ self.study_area = ee.Geometry.Polygon(
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
        ) """
        # self.study_area = ee.Geometry.Polygon(
        #     [
        #         [
        #             [-20.673055938396296, 59.8539499561377],
        #   [-20.673055938396296, 32.488037505645565],
        #   [41.905069061603704, 32.488037505645565],
        #   [41.905069061603704, 59.8539499561377],
        #         ]
        #     ],
        #     None,
        #     False,
        # )
        # self.test_point = ee.Geometry.Point([-4.59, 37.86])

        self.study_area = ee.Geometry.Polygon(
            [
                [
                    [-4.59673559330618, 37.87785028383721],
                    [-4.59673559330618, 37.86490927780263],
                    [-4.579054471480008, 37.86490927780263],
                    [-4.579054471480008, 37.87785028383721],
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
            feature = ee.Feature(
                self.study_region,
                {
                    "datetime": ee.Date(image.get("system:time_start")).format(
                        "YYYY-MM-dd"
                    ),
                    "et0": ee.Number(
                        image.select("et0")
                        .reduceRegion(ee.Reducer.mean(), self.study_region, scale=27830)
                        .get("et0")
                    ),
                },
            )
            return feature

        et0_collection = et0_collection.map(create_feature).getInfo()

        # et0_collection.get("features")[i]["properties"] into a dataframe
        et0_df = pd.DataFrame(et0_collection.get("features"))
        et0_df = pd.DataFrame(et0_df["properties"].to_list())

        print(et0_df)

    @time_controller.timeit
    def test_ET_model(self):
        self.setUp()

        with ee.profilePrinting():
            gfs_et0 = Calculate_ET0(
                study_region=self.study_region,
                start_date=self.start_date,
                end_date=self.end_date,
                scale=10,
                debug=False,
                model="NASA",
            )
            et0_collection = gfs_et0.calculate_eto_daily()

            def create_feature_polygone(image):
                feature = ee.Feature(
                    self.study_region,
                    {
                        "datetime": ee.Date(image.get("system:time_start")).format(
                            "YYYY-MM-dd"
                        ),
                        "et0": ee.Number(
                            image.select("et0")
                            .reduceRegion(
                                ee.Reducer.mean(), self.study_region, scale=27830
                            )
                            .get("et0")
                        ),
                    },
                )
                return feature
            def create_feature_point(image):
                feature = ee.Feature(
                    self.study_region,
                    {
                        "datetime": ee.Date(image.get("system:time_start")).format(
                            "YYYY-MM-dd"
                        ),
                        "et0": ee.Number(
                            image.select("et0")
                            .reduceRegion(
                                ee.Reducer.mean(), self.test_point, scale=27830
                            )
                            .get("et0")
                        ),
                    },
                )
                return feature

            # export collection to drive to use later in gee
            # task = ee.batch.Export.image.toAsset(
            #     image=et0_collection.first(),
            #     description="et0_collection_2",
            #     assetId="projects/gee-franciscopuig/assets/et0_collection_2",
            #     region=self.study_region,
            #     scale=et0_collection.first().projection().nominalScale().getInfo(),
            #     crs=et0_collection.first().projection().crs().getInfo(),
            #     maxPixels=1e13,
            # )

            # task.start()

            # while task.status()["state"] == "RUNNING":
            #     print(task.status())
            #     time.sleep(5)

            # if task.status()["state"] == "COMPLETED":
            #     print("task completed")

            # elif task.status()["state"] == "FAILED":
            #     print(f"task failed: {task.status()['error_message']}")

            et0_collection_info = et0_collection.map(create_feature_point).getInfo()

            # et0_df = pd.DataFrame(et0_collection_info.get("features"))
            # et0_df = pd.DataFrame(et0_df["properties"].to_list())
            # list_of_names = [f"et0_{self.task_name}_{et0_df.iloc[i]['datetime']}" for i in range(len(et0_df))]
            # list_of_asset = [f"projects/gee-franciscopuig/assets/{list_of_names[i]}" for i in range(len(et0_df))]
            # ee_export_image_collection_to_asset(
            #     ee_object=et0_collection,
            #     descriptions=list_of_names,
            #     assetIds=list_of_asset,
            #     region=self.study_region,
            #     scale=et0_collection.first().projection().nominalScale().getInfo(),
            #     crs=et0_collection.first().projection().crs().getInfo(),
            #     maxPixels=1e13,
            #     # region=self.study_region,
            # )

            # et0_collection.get("features")[i]["properties"] into a dataframe
            et0_df = pd.DataFrame(et0_collection_info.get("features"))
            et0_df = pd.DataFrame(et0_df["properties"].to_list())

            print(et0_df)


if __name__ == "__main__":
    unittest.main()
