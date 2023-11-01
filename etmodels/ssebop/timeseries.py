# ----------------------------------------------------------------------------------------#
#
# Customized by franciscopuigpb@gmail.com,bjonesneu@berkeley.edu, bjonesneu@gmail.com in October 2023
#   - Added additional output variables
#   - Converted to run all code on GEE Server instead of Client
#
# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------------------#

# PYTHON PACKAGES
import sys
import os
import ee
import pandas as pd

# TODO: Moving to a better place
ee.Initialize()

# add the path to the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from etmodels.test.time_controller import TimeController
from collection import Collection

# FOLDERS


# TIMESRIES FUNCTION
class TimeSeries:
    # ENDMEMBERS DEFAULT
    # ALLEN ET AL. (2013)
    def __init__(
        self,
        year_i,
        month_i,
        day_i,
        year_e,
        month_e,
        day_e,
        cloud_cover,
        coordinate,
        debug=False,
    ):
        ee.Initialize()

        self.landsat_cs = 30
        self.start_date = f"{year_i}-{month_i}-{day_i}"
        self.end_date = f"{year_e}-{month_e}-{day_e}"

        self.collections = [
            "LANDSAT/LC09/C02/T1_L2",
            "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT/LE07/C02/T1_L2",
            "LANDSAT/LT05/C02/T1_L2",
        ]

        self.et_reference_source = "NASA"
        self.et_reference_band = "et0"
        self.et_reference_factor = 1.0
        self.et_reference_resample = "nearest"
        self.et_reference_date_type = "daily"

        self.cloud_cover = cloud_cover

        # Number of extra days (at start and end) to include in interpolation
        self.interp_days = 32

        # Interpolation method - currently only LINEAR is supported
        self.interp_method = "LINEAR"

        self.test_point = coordinate

        def retrieveETandMeteo(image, debug=False):
            image = ee.Image(image)  # just used to ensure correct type casting

            landsat_version = ee.String(image.get("SPACECRAFT_ID"))

            point_value = image.reduceRegion(
                ee.Reducer.first(), self.test_point, self.landsat_cs
            )
            et_point = point_value.get("et")
            et0 = point_value.get("et_reference")
            fraction = point_value.get("et_fraction")

            ndvi_point = point_value.get("ndvi")

            tmax_point = point_value.get("tmax")
            tmin_point = point_value.get("tmin")
            actual_vapor_pressure = point_value.get("actual_vapor_pressure")
            solar_radiation = point_value.get("solar_radiation")
            wind_speed = point_value.get("wind_speed")
            rain = point_value.get("rain")

            etFeature = ee.Feature(
                self.test_point.centroid(),
                {
                    "date": image.date().format("YYYY-MM-dd"),
                    "version": landsat_version,
                    "status": "ok",
                    "ET_24h": et_point,
                    "ET0_24h": et0,
                    "ET_fraction": fraction,
                    "NDVI": ndvi_point,
                    "TMAX": tmax_point,
                    "TMIN": tmin_point,
                    "actual_vapor_pressure": actual_vapor_pressure,
                    "solar_radiation": solar_radiation,
                    "wind_speed": wind_speed,
                    "precip": rain,
                },
            )

            return etFeature

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

        overpass_collection = model_obj.overpass(
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
        
        self.ETandMeteo = overpass_collection.map(retrieveETandMeteo)
