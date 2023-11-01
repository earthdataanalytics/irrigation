import datetime
import pprint
import re

import ee

try:
    import common
    import landsat
    import model
    import utils
    from .refetgee.hourly import Hourly
    from .refetgee.daily import Daily
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    import common
    import landsat
    import model
    import utils
    from refetgee.hourly import Hourly
    from refetgee.daily import Daily, Calculate_ET0

PROJECT_FOLDER = "projects/earthengine-legacy/assets/projects/usgs-ssebop"
# PROJECT_FOLDER = 'projects/usgs-ssebop'


def lazy_property(fn):
    """Decorator that makes a property lazy-evaluated

    https://stevenloria.com/lazy-properties/
    """
    attr_name = "_lazy_" + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


class Image:
    """Earth Engine based SSEBop Image"""

    _C2_LST_CORRECT = False  # Enable (True) C2 LST correction to recalculate LST

    def __init__(
        self,
        image,
        et_reference_source=None,
        et_reference_band=None,
        et_reference_factor=None,
        et_reference_resample=None,
        et_reference_date_type=None,
        dt_source="projects/earthengine-legacy/assets/projects/usgs-ssebop/dt/daymet_median_v6",
        tcorr_source="FANO",
        tmax_source="projects/earthengine-legacy/assets/projects/usgs-ssebop/tmax/daymet_v4_mean_1981_2010",
        dt_min=5,
        dt_max=25,
        et_fraction_type="alfalfa",
        reflectance_type="SR",
        **kwargs,
    ):
        """Construct a generic SSEBop Image

        Parameters
        ----------
        image : ee.Image
            A "prepped" SSEBop input image.
            Image must have bands: "ndvi" and "lst" and "ndwi" and "qa_water"
            Image must have properties: 'system:id', 'system:index', and
                'system:time_start'.
        et_reference_source : str, float, optional
            Reference ET source (the default is None).
            Parameter is required if computing 'et' or 'et_reference'.
        et_reference_band : str, optional
            Reference ET band name (the default is None).
            Parameter is required if computing 'et' or 'et_reference'.
        et_reference_factor : float, None, optional
            Reference ET scaling factor.  The default is None which is
            equivalent to 1.0 (or no scaling).
        et_reference_resample : {'nearest', 'bilinear', 'bicubic', None}, optional
            Reference ET resampling.  The default is None which is equivalent
            to nearest neighbor resampling.
        dt_source : str, float, {'DAYMET_MEDIAN_V0', 'DAYMET_MEDIAN_V1', 'DAYMET_MEDIAN_V2'}, optional
            dT source  (the default is None).
        tcorr_source : {'DYNAMIC', 'GRIDDED', 'SCENE_GRIDDED',
                        'SCENE', 'SCENE_DAILY', 'SCENE_MONTHLY',
                        'SCENE_ANNUAL', 'SCENE_DEFAULT', or float}, optional
            Tcorr source keyword (the default is 'DYNAMIC').
        tmax_source : {'CIMIS', 'DAYMET_V3', 'DAYMET_V4', 'GRIDMET',
                       'DAYMET_MEDIAN_V2', 'CIMIS_MEDIAN_V1',
                       collection ID, or float}, optional
            Maximum air temperature source.  The default is
            'projects/usgs-ssebop/tmax/daymet_v3_median_1980_2018'.
        elr_flag : bool, str, optional
            If True, apply Elevation Lapse Rate (ELR) adjustment
            (the default is False).
        dt_min : float, optional
            Minimum allowable dT [K] (the default is 6).
        dt_max : float, optional
            Maximum allowable dT [K] (the default is 25).
        et_fraction_type : {'alfalfa', 'grass'}, optional
            ET fraction  (the default is 'alfalfa').
        reflectance_type : {'SR', 'TOA'}, optional
            Used to set the Tcorr NDVI thresholds
            (the default is 'SR').
        kwargs : dict, optional
            dt_resample : {'nearest', 'bilinear'}
            tcorr_resample : {'nearest', 'bilinear'}
            tmax_resample : {'nearest', 'bilinear'}
            elev_source : str or float
            min_pixels_per_image : int
            min_pixels_per_grid_cell : int
            min_grid_cells_per_image : int

        Notes
        -----
        Input image must have a Landsat style 'system:index' in order to
        lookup Tcorr value from table asset.  (i.e. LC08_043033_20150805)

        """
        self.image = ee.Image(image)

        # Set as "lazy_property" below in order to return custom properties
        # self.lst = self.image.select('lst')
        # self.ndvi = self.image.select('ndvi')

        # Copy system properties
        self._id = self.image.get("system:id")
        self._index = self.image.get("system:index")
        self._time_start = self.image.get("system:time_start")
        self._properties = {
            "system:index": self._index,
            "system:time_start": self._time_start,
            "image_id": self._id,
        }

        # Build SCENE_ID from the (possibly merged) system:index
        scene_id = ee.List(ee.String(self._index).split("_")).slice(-3)
        self._scene_id = (
            ee.String(scene_id.get(0))
            .cat("_")
            .cat(ee.String(scene_id.get(1)))
            .cat("_")
            .cat(ee.String(scene_id.get(2)))
        )

        # Build WRS2_TILE from the scene_id
        self._wrs2_tile = (
            ee.String("p")
            .cat(self._scene_id.slice(5, 8))
            .cat("r")
            .cat(self._scene_id.slice(8, 11))
        )

        # Set server side date/time properties using the 'system:time_start'
        self._date = ee.Date(self._time_start)
        self._year = ee.Number(self._date.get("year"))
        self._month = ee.Number(self._date.get("month"))
        self._start_date = ee.Date(utils.date_to_time_0utc(self._date))
        self._end_date = self._start_date.advance(1, "day")
        self._doy = ee.Number(self._date.getRelative("day", "year")).add(1).int()
        self._cycle_day = (
            self._start_date.difference(ee.Date.fromYMD(1970, 1, 3), "day")
            .mod(8)
            .add(1)
            .int()
        )

        # Reference ET parameters
        self.et_reference_source = et_reference_source
        self.et_reference_band = et_reference_band
        self.et_reference_factor = et_reference_factor
        self.et_reference_resample = et_reference_resample
        self.et_reference_date_type = et_reference_date_type

        # Check reference ET parameters
        if et_reference_factor and not utils.is_number(et_reference_factor):
            raise ValueError("et_reference_factor must be a number")
        if et_reference_factor and self.et_reference_factor < 0:
            raise ValueError("et_reference_factor must be greater than zero")
        et_reference_resample_methods = ["nearest", "bilinear", "bicubic"]
        if (
            et_reference_resample
            and et_reference_resample.lower() not in et_reference_resample_methods
        ):
            raise ValueError("unsupported et_reference_resample method")
        et_reference_date_type_methods = ["doy", "daily"]
        if (
            et_reference_date_type
            and et_reference_date_type.lower() not in et_reference_date_type_methods
        ):
            raise ValueError("unsupported et_reference_date_type method")

        # Model input parameters
        self._dt_source = dt_source
        self._tcorr_source = tcorr_source
        self._tmax_source = tmax_source

        # TODO: Move into keyword args section below
        self._dt_min = float(dt_min)
        self._dt_max = float(dt_max)

        # TODO: Move into keyword args section below
        # Convert elr_flag from string to bool IF necessary
        

        # ET fraction type
        # CGM - Should et_fraction_type be set as a kwarg instead?
        if et_fraction_type.lower() not in ["alfalfa", "grass"]:
            raise ValueError('et_fraction_type must "alfalfa" or "grass"')
        self.et_fraction_type = et_fraction_type.lower()
        # if 'et_fraction_type' in kwargs.keys():
        #     self.et_fraction_type = kwargs['et_fraction_type'].lower()
        # else:
        #     self.et_fraction_type = 'alfalfa'

        self.reflectance_type = reflectance_type
        if reflectance_type not in ["SR", "TOA"]:
            raise ValueError('reflectance_type must "SR" or "TOA"')

        # Image projection and geotransform
        self.crs = image.projection().crs()
        self.transform = ee.List(
            ee.Dictionary(ee.Algorithms.Describe(image.projection())).get("transform")
        )
        # self.crs = image.select([0]).projection().getInfo()['crs']
        # self.transform = image.select([0]).projection().getInfo()['transform']

        """Keyword arguments"""
        # CGM - What is the right way to process kwargs with default values?
        self.kwargs = kwargs

        if "elev_source" in kwargs.keys():
            self._elev_source = kwargs["elev_source"]
        else:
            self._elev_source = None

        # CGM - Should these be checked in the methods they are used in instead?
        # Set the resample method as properties so they can be modified
        if "dt_resample" in kwargs.keys():
            self._dt_resample = kwargs["dt_resample"].lower()
        else:
            self._dt_resample = "bilinear"

        if "tmax_resample" in kwargs.keys():
            self._tmax_resample = kwargs["tmax_resample"].lower()
        else:
            self._tmax_resample = "bilinear"

        if "tcorr_resample" in kwargs.keys():
            self._tcorr_resample = kwargs["tcorr_resample"].lower()
        else:
            self._tcorr_resample = "bilinear"

        """Gridded Tcorr keyword arguments"""
        # TODO: This should probably be moved into tcorr_gridded()
        if "min_pixels_per_grid_cell" in kwargs.keys():
            self.min_pixels_per_grid_cell = kwargs["min_pixels_per_grid_cell"]
        else:
            self.min_pixels_per_grid_cell = 10

        # TODO: This should probably be moved into tcorr_gridded()
        if "min_grid_cells_per_image" in kwargs.keys():
            self.min_grid_cells_per_image = kwargs["min_grid_cells_per_image"]
        else:
            self.min_grid_cells_per_image = 5
            
        # CALCULATE REFERENCE ET AND WEATHER VARIABLES
        self.collection_et_weather = self.calculate_et_and_weather()

        # DEADBEEF - This is checked in tcorr() since the GRIDDED and DYNAMIC
        #   options have different defaults
        # if 'min_pixels_per_image' in kwargs.keys():
        #     self.min_pixels_per_image = kwargs['min_pixels_per_image']
        # else:
        #     self.min_pixels_per_image = 250

        # print(f'this is the tcorr source passed to the image class {tcorr_source}')

    def calculate(self, variables=["et", "et_reference", "et_fraction"]):
        """Return a multiband image of calculated variables

        Parameters
        ----------
        variables : list

        Returns
        -------
        ee.Image

        """
        output_images = []
        for v in variables:
            if v.lower() == "et":
                output_images.append(self.et.float())
                
            elif v.lower() == "et_fraction":
                output_images.append(self.et_fraction.float())
            elif v.lower() == "et_reference":
                output_images.append(self.et_reference.float())
            elif v.lower() == "lst":
                output_images.append(self.lst.float())
            elif v.lower() == "mask":
                output_images.append(self.mask)
            elif v.lower() == "ndvi":
                output_images.append(self.ndvi.float())
            # elif v.lower() == 'qa':
            #     output_images.append(self.qa)
            elif v.lower() == "quality":
                output_images.append(self.quality)
            elif v.lower() == "time":
                output_images.append(self.time)
            else:
                raise ValueError("unsupported variable: {}".format(v))
            
        # reduced_image = ee.Image(output_images).set(self._properties)  
        
        # # get ndvi mean 
        # ndvi_mean = self.ndvi.reduceRegion(
        #     reducer=ee.Reducer.mean(),
        #     geometry=self.image.geometry(),
        #     scale=30,
        #     maxPixels=1e13,
        # ).get("ndvi").getInfo()

        return ee.Image(output_images).set(self._properties)

    @lazy_property
    def qa_water_mask(self):
        """
        Extract water mask from the Landsat Collection 2 SR QA_PIXEL band.
        :return: ee.Image
        """

        return self.image.select(["qa_water"]).set(self._properties)

    @lazy_property
    def et_fraction(self):
        """Fraction of reference ET"""

        # Adjust air temperature based on elevation (Elevation Lapse Rate)
        # TODO: Eventually point this at the model.elr_adjust() function instead
        # =========================================================
       
        tmax = self.tmax

        if type(self._tcorr_source) is str and self._tcorr_source.upper() == "FANO":
            # bilinearly resample tmax at 1km (smoothed).
            tmax = tmax.resample("bilinear")

        if (
            self._dt_resample
            and type(self._dt_resample) is str
            and self._dt_resample.lower() in ["bilinear", "bicubic"]
        ):
            dt = self.dt.resample(self._dt_resample)
        else:
            dt = self.dt

        et_fraction = model.et_fraction(
            lst=self.lst, tmax=tmax, tcorr=self.tcorr, dt=dt
        )


        return et_fraction.set(self._properties).set(
            {
                "tcorr_index": self.tcorr.get("tcorr_index"),
                "et_fraction_type": self.et_fraction_type.lower(),
            }
        )

    @lazy_property
    def et_reference(self):
        """Reference ET for the image date"""
       
        
        # # Assume the collection is daily with valid system:time_start values
        # gfs_et0 = Calculate_ET0(
        #     study_region=self.image.geometry(),
        #     start_date=self._start_date,
        #     end_date=self._end_date,
        #     # scale=self.scale,
        #     debug=False,
        #     model="NASA",
        # )
        et_reference_coll = self.collection_et_weather.select([self.et_reference_band])
           
        et_reference_img = ee.Image(et_reference_coll.first())
        if self.et_reference_resample in ["bilinear", "bicubic"]:
            et_reference_img = et_reference_img.resample(self.et_reference_resample)
    

        if self.et_reference_factor > 1.0:
            et_reference_img = et_reference_img.multiply(self.et_reference_factor)

        # Map ETr values directly to the input (i.e. Landsat) image pixels
        # The benefit of this is the ETr image is now in the same crs as the
        #   input image.  Not all models may want this though.
        # CGM - Should the output band name match the input ETr band name?
        return (
            self.qa_water_mask.float()
            .multiply(0)
            .add(et_reference_img)
            .rename(["et_reference"])
            .set(self._properties)
        )

    @lazy_property
    def et(self):
        """Actual ET as fraction of reference times"""
        return (
            self.et_fraction.multiply(self.et_reference)
            .rename(["et"])
            .set(self._properties)
        )

    @lazy_property
    def lst(self):
        """Input land surface temperature (LST) [K]"""
        return self.image.select(["lst"]).set(self._properties)

    @lazy_property
    def mask(self):
        """Mask of all active pixels (based on the final et_fraction)"""
        return (
            self.et_fraction.multiply(0)
            .add(1)
            .updateMask(1)
            .rename(["mask"])
            .set(self._properties)
            .uint8()
        )

    @lazy_property
    def ndvi(self):
        """Input normalized difference vegetation index (NDVI)"""
        return self.image.select(["ndvi"]).set(self._properties)

    @lazy_property
    def ndwi(self):
        """Input normalized difference water index (NDWI) to mask water features"""
        return self.image.select(["ndwi"]).set(self._properties)

    @lazy_property
    def quality(self):
        """Set quality to 1 for all active pixels (for now)"""
        return self.mask.rename(["quality"]).set(self._properties)

    @lazy_property
    def time(self):
        """Return an image of the 0 UTC time (in milliseconds)"""
        return (
            self.mask.double()
            .multiply(0)
            .add(utils.date_to_time_0utc(self._date))
            .rename(["time"])
            .set(self._properties)
        )

    @lazy_property
    def dt(self):
        """
       
        Returns
        -------
        ee.Image

        Raises
        ------
        ValueError
            If `self._dt_source` is not supported.

        """
      
        # Assumes a string source is an image collection ID (not an image ID),\
        #   MF: and currently only supports a climatology 'DOY-based' dataset filter
        dt_coll = ee.ImageCollection(self._dt_source).filter(
            ee.Filter.calendarRange(self._doy, self._doy, "day_of_year")
        )
        # MF: scale factor property only applied for string ID dT collections, and
        #  no clamping used for string ID dT collections.
        dt_img = ee.Image(dt_coll.first())
        dt_scale_factor = ee.Dictionary(
            {"scale_factor": dt_img.get("scale_factor")}
        ).combine({"scale_factor": "1.0"}, overwrite=False)
        dt_img = dt_img.multiply(
            ee.Number.parse(dt_scale_factor.get("scale_factor"))
        )
        

        return dt_img.rename("dt")


    @lazy_property
    def tcorr(self):
        """Get Tcorr from pre-computed assets for each Tmax source

        Returns
        -------


        Raises
        ------
        ValueError
            If `self._tcorr_source` is not supported.

        Notes
        -----
        Tcorr Index values indicate which level of Tcorr was used
          0 - Gridded blended cold/hot Tcorr (*)
          1 - Gridded cold Tcorr
          2 - Continuous cold tcorr based on an NDVI function.
          3 - Scene specific Tcorr
          4 - Mean monthly Tcorr per WRS2 tile
          5 - Mean seasonal Tcorr per WRS2 tile (*)
          6 - Mean annual Tcorr per WRS2 tile
          7 - Default Tcorr
          8 - User defined Tcorr
          9 - No data

        """
        # TODO: Make this a class property or method that we can query
    
        tcorr_img = ee.Image(self.tcorr_FANO).select(["tcorr"])

        return tcorr_img.rename(["tcorr"])

        
    def calculate_et_and_weather(self):
        gfs_et0 = Calculate_ET0(
            study_region=self.image.geometry(),
            start_date=self._start_date,
            end_date=self._end_date,
            # scale=self.scale,
            debug=False,
            model="NASA",
            
        )
        collection_et_weather = gfs_et0.calculate_eto_daily(
            add_weather_data=True
            )
        return collection_et_weather
        
        
    @lazy_property
    def tmax(self):
        """Get Tmax image from precomputed climatology collections or dynamically

        Returns
        -------
        ee.Image

        Raises
        ------
        ValueError
            If `self._tmax_source` is not supported.

        """
        
        # Process Tmax source as a collection ID
        # The new Tmax collections do not have a time_start so filter using
        #   the "doy" property instead
         # Assume the collection is daily with valid system:time_start values
        # gfs_et0 = Calculate_ET0(
        #     study_region=self.image.geometry(),
        #     start_date=self._start_date,
        #     end_date=self._end_date,
        #     # scale=self.scale,
        #     debug=False,
        #     model="NASA",
            
        # )
        tmax_coll = self.collection_et_weather.select(["tmax"])
        # tmax_coll = ee.ImageCollection(self._tmax_source).filterMetadata(
        #     "doy", "equals", self._doy
        # )
        #     .filterMetadata('doy', 'equals', self._doy.format('%03d'))
        tmax_image = ee.Image(tmax_coll.first()).set(
            {"tmax_source": self._tmax_source}
        )

        if self._tmax_resample and self._tmax_resample.lower() in [
            "bilinear",
            "bicubic",
        ]:
            tmax_image = tmax_image.resample(self._tmax_resample)
        # TODO: A reproject call may be needed here also
        # tmax_image = tmax_image.reproject(self.crs, self.transform)

        return tmax_image

  

    

    @classmethod
    def from_landsat_c1_sr(cls, sr_image, cloudmask_args={}, **kwargs):
        """Returns a SSEBop Image instance from a Landsat Collection 1 SR image

        Parameters
        ----------
        sr_image : ee.Image, str
            A raw Landsat Collection 1 SR image or image ID.
        cloudmask_args : dict
            keyword arguments to pass through to cloud mask function
        kwargs : dict
            Keyword arguments to pass through to Image init function

        Returns
        -------
        Image

        """
        sr_image = ee.Image(sr_image)

        # Use the SATELLITE property identify each Landsat type
        spacecraft_id = ee.String(sr_image.get("SATELLITE"))

        # Rename bands to generic names
        # Rename thermal band "k" coefficients to generic names
        input_bands = ee.Dictionary(
            {
                "LANDSAT_4": ["B1", "B2", "B3", "B4", "B5", "B7", "B6", "pixel_qa"],
                "LANDSAT_5": ["B1", "B2", "B3", "B4", "B5", "B7", "B6", "pixel_qa"],
                "LANDSAT_7": ["B1", "B2", "B3", "B4", "B5", "B7", "B6", "pixel_qa"],
                "LANDSAT_8": ["B2", "B3", "B4", "B5", "B6", "B7", "B10", "pixel_qa"],
            }
        )
        output_bands = [
            "blue",
            "green",
            "red",
            "nir",
            "swir1",
            "swir2",
            "tir",
            "pixel_qa",
        ]
        # TODO: Follow up with Simon about adding K1/K2 to SR collection
        # Hardcode values for now
        k1 = ee.Dictionary(
            {
                "LANDSAT_4": 607.76,
                "LANDSAT_5": 607.76,
                "LANDSAT_7": 666.09,
                "LANDSAT_8": 774.8853,
            }
        )
        k2 = ee.Dictionary(
            {
                "LANDSAT_4": 1260.56,
                "LANDSAT_5": 1260.56,
                "LANDSAT_7": 1282.71,
                "LANDSAT_8": 1321.0789,
            }
        )
        prep_image = (
            sr_image.select(input_bands.get(spacecraft_id), output_bands)
            .multiply([0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.1, 1])
            .set(
                {
                    "k1_constant": ee.Number(k1.get(spacecraft_id)),
                    "k2_constant": ee.Number(k2.get(spacecraft_id)),
                }
            )
        )

        cloud_mask = common.landsat_c1_sr_cloud_mask(
            sr_image, **cloudmask_args
        )

        # Build the input image
        input_image = ee.Image(
            [
                landsat.lst(prep_image),
                landsat.ndvi(prep_image),
                landsat.ndwi(prep_image),
                # CGM - use a blank image for the water mask for now
                landsat.ndvi(prep_image).multiply(0).rename(["qa_water"]),
            ]
        )

        # Apply the cloud mask and add properties
        input_image = input_image.updateMask(cloud_mask).set(
            {
                "system:index": sr_image.get("system:index"),
                "system:time_start": sr_image.get("system:time_start"),
                "system:id": sr_image.get("system:id"),
            }
        )

        # Instantiate the class
        return cls(input_image, reflectance_type="SR", **kwargs)

    @classmethod
    def from_landsat_c2_sr(cls, sr_image, cloudmask_args={}, **kwargs):
        """Returns a SSEBop Image instance from a Landsat Collection 2 SR image

        Parameters
        ----------
        sr_image : ee.Image, str
            A raw Landsat Collection 2 SR image or image ID.
        cloudmask_args : dict
            keyword arguments to pass through to cloud mask function
        kwargs : dict
            Keyword arguments to pass through to Image init function

        Returns
        -------
        Image

        """
        sr_image = ee.Image(sr_image)

        # Use the SPACECRAFT_ID property identify each Landsat type
        spacecraft_id = ee.String(sr_image.get("SPACECRAFT_ID"))

        # Rename bands to generic names
        input_bands = ee.Dictionary(
            {
                "LANDSAT_4": [
                    "SR_B1",
                    "SR_B2",
                    "SR_B3",
                    "SR_B4",
                    "SR_B5",
                    "SR_B7",
                    "ST_B6",
                    "QA_PIXEL",
                    "QA_RADSAT",
                ],
                "LANDSAT_5": [
                    "SR_B1",
                    "SR_B2",
                    "SR_B3",
                    "SR_B4",
                    "SR_B5",
                    "SR_B7",
                    "ST_B6",
                    "QA_PIXEL",
                    "QA_RADSAT",
                ],
                "LANDSAT_7": [
                    "SR_B1",
                    "SR_B2",
                    "SR_B3",
                    "SR_B4",
                    "SR_B5",
                    "SR_B7",
                    "ST_B6",
                    "QA_PIXEL",
                    "QA_RADSAT",
                ],
                "LANDSAT_8": [
                    "SR_B2",
                    "SR_B3",
                    "SR_B4",
                    "SR_B5",
                    "SR_B6",
                    "SR_B7",
                    "ST_B10",
                    "QA_PIXEL",
                    "QA_RADSAT",
                ],
                "LANDSAT_9": [
                    "SR_B2",
                    "SR_B3",
                    "SR_B4",
                    "SR_B5",
                    "SR_B6",
                    "SR_B7",
                    "ST_B10",
                    "QA_PIXEL",
                    "QA_RADSAT",
                ],
            }
        )
        output_bands = [
            "blue",
            "green",
            "red",
            "nir",
            "swir1",
            "swir2",
            "tir",
            "QA_PIXEL",
            "QA_RADSAT",
        ]

        prep_image = (
            sr_image.select(input_bands.get(spacecraft_id), output_bands)
            .multiply(
                [
                    0.0000275,
                    0.0000275,
                    0.0000275,
                    0.0000275,
                    0.0000275,
                    0.0000275,
                    0.00341802,
                    1,
                    1,
                ]
            )
            .add([-0.2, -0.2, -0.2, -0.2, -0.2, -0.2, 149.0, 0, 0])
        )
        # Default the cloudmask flags to True if they were not
        # Eventually these will probably all default to True in openet.core
        if "cirrus_flag" not in cloudmask_args.keys():
            cloudmask_args["cirrus_flag"] = True
        if "dilate_flag" not in cloudmask_args.keys():
            cloudmask_args["dilate_flag"] = True
        if "shadow_flag" not in cloudmask_args.keys():
            cloudmask_args["shadow_flag"] = True
        if "snow_flag" not in cloudmask_args.keys():
            cloudmask_args["snow_flag"] = True
        # if 'saturated_flag' not in cloudmask_args.keys():
        #     cloudmask_args['saturated_flag'] = True

        cloud_mask = common.landsat_c2_sr_cloud_mask(
            sr_image, **cloudmask_args
        )

        # Check if passing c2_lst_correct or soil_emis_coll_id arguments
        if "c2_lst_correct" in kwargs.keys():
            assert isinstance(
                kwargs["c2_lst_correct"], bool
            ), "selection type must be a boolean"
            # Remove from kwargs since it is not a valid argument for Image init
            c2_lst_correct = kwargs.pop("c2_lst_correct")
        else:
            c2_lst_correct = cls._C2_LST_CORRECT

        if c2_lst_correct:
            lst = common.landsat_c2_sr_lst_correct(
                sr_image, landsat.ndvi(prep_image)
            )
        else:
            lst = prep_image.select(["tir"])

        # Build the input image
        # Don't compute LST since it is being provided
        input_image = ee.Image(
            [
                lst.rename(["lst"]),
                landsat.ndvi(prep_image),
                landsat.ndwi(prep_image),
                landsat.landsat_c2_qa_water_mask(prep_image),
            ]
        )

        # Apply the cloud mask and add properties
        input_image = input_image.updateMask(cloud_mask).set(
            {
                "system:index": sr_image.get("system:index"),
                "system:time_start": sr_image.get("system:time_start"),
                "system:id": sr_image.get("system:id"),
            }
        )

        # Instantiate the class
        return cls(input_image, reflectance_type="SR", **kwargs)

    

    @lazy_property
    def tcorr_image_hot(self):
        """Compute the scene wide HOT Tcorr for the current image

        Returns
        -------
        ee.Image of Tcorr values

        """

        lst = ee.Image(self.lst)
        ndvi = ee.Image(self.ndvi)
        tmax = ee.Image(self.tmax)
        dt = ee.Image(self.dt) 
        # TODO need lc mask for barren landcover
        lc = None

        # Compute Hot Tcorr (Same as cold tcorr but you subtract dt from Land Surface Temp.)
        hottemp = lst.subtract(dt)
        tcorr = hottemp.divide(tmax)

        # Adjust NDVI thresholds based on reflectance type
        if self.reflectance_type.upper() == "SR":
            ndvi_threshold = 0.3
        # elif self.reflectance_type.upper() == 'TOA':
        else:
            ndvi_threshold = 0.25

        # Select LOW (but non-negative) NDVI pixels that are also surrounded by LOW NDVI, but
        ndvi_smooth = ndvi.focal_mean(radius=90, units="meters").reproject(
            crs=self.crs, crsTransform=self.transform
        )
        ndvi_smooth_mask = ndvi_smooth.gt(0.0).And(ndvi_smooth.lte(ndvi_threshold))

        # changed the gt and lte to be after the reduceNeighborhood() call
        ndvi_buffer = ndvi.reduceNeighborhood(
            ee.Reducer.min(), ee.Kernel.square(radius=60, units="meters")
        )
        ndvi_buffer_mask = ndvi_buffer.gt(0.0).And(ndvi_buffer.lte(ndvi_threshold))

        # No longer worry about low LST. Filter out high NDVI vals and mask out areas that aren't 'Barren'
        tcorr_mask = lst.And(ndvi_smooth_mask).And(ndvi_buffer_mask)  # .And(lc)

        return (
            tcorr.updateMask(tcorr_mask)
            .rename(["tcorr"])
            .set(
                {
                    "system:index": self._index,
                    "system:time_start": self._time_start,
                    "tmax_source": tmax.get("tmax_source"),
                    "tmax_version": tmax.get("tmax_version"),
                }
            )
        )

    @lazy_property
    def tcorr_FANO(self):
        """Compute the scene wide Tcorr for the current image adjusting tcorr
            temps based on NDVI thresholds to simulate true cold cfactor

        FANO: Forcing And Normalizing Operation

        Returns
        -------
        ee.Image of Tcorr values

        """
        coarse_transform = [5000, 0, 15, 0, -5000, 15]
        coarse_transform100 = [100000, 0, 15, 0, -100000, 15]
        dt_coeff = 0.125
        ndwi_threshold = -0.15
        high_ndvi_threshold = 0.9
        water_pct = 10
        # max pixels argument for .reduceResolution()
        m_pixels = 65535

        lst = ee.Image(self.lst)
        ndvi = ee.Image(self.ndvi).clamp(-1.0, 1.0)
        tmax = ee.Image(self.tmax)
        dt = ee.Image(self.dt)
        ndwi = ee.Image(self.ndwi)
        qa_watermask = ee.Image(self.qa_water_mask)

        # setting NDVI to negative values where Landsat QA Pixel detects water.
        ndvi = ndvi.where(qa_watermask.eq(1).And(ndvi.gt(0)), ndvi.multiply(-1))

        watermask = ndwi.lt(ndwi_threshold)
        # combining NDWI mask with QA Pixel watermask.
        watermask = watermask.multiply(qa_watermask.eq(0))
        # returns qa_watermask layer masked by combined watermask to get a count of valid pixels
        watermask_for_coarse = qa_watermask.updateMask(watermask)

        watermask_coarse_count = (
            watermask_for_coarse.reduceResolution(ee.Reducer.count(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
            .updateMask(1)
            .select([0], ["count"])
        )
        total_pixels_count = (
            ndvi.reduceResolution(ee.Reducer.count(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
            .updateMask(1)
            .select([0], ["count"])
        )

        # Doing a layering mosaic check to fill any remaining Null watermask coarse pixels with valid mask data.
        #   This can happen if the reduceResolution count contained exclusively water pixels from 30 meters.
        watermask_coarse_count = ee.Image(
            [watermask_coarse_count, total_pixels_count.multiply(0).add(1)]
        ).reduce(ee.Reducer.firstNonNull())

        percentage_bad = watermask_coarse_count.divide(total_pixels_count)
        pct_value = 1 - (water_pct / 100)
        wet_region_mask_5km = percentage_bad.lte(pct_value)

        ndvi_avg_masked = (
            ndvi.updateMask(watermask)
            .reduceResolution(ee.Reducer.mean(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
        )
        ndvi_avg_masked100 = (
            ndvi.updateMask(watermask)
            .reduceResolution(ee.Reducer.mean(), True, m_pixels)
            .reproject(self.crs, coarse_transform100)
        )
        ndvi_avg_unmasked = (
            ndvi.reduceResolution(ee.Reducer.mean(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
            .updateMask(1)
        )
        lst_avg_masked = (
            lst.updateMask(watermask)
            .reduceResolution(ee.Reducer.mean(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
        )
        lst_avg_masked100 = (
            lst.updateMask(watermask)
            .reduceResolution(ee.Reducer.mean(), True, m_pixels)
            .reproject(self.crs, coarse_transform100)
        )
        lst_avg_unmasked = (
            lst.reduceResolution(ee.Reducer.mean(), False, m_pixels)
            .reproject(self.crs, coarse_transform)
            .updateMask(1)
        )

        # Here we don't need the reproject.reduce.reproject sandwich bc these are coarse data-sets
        dt_avg = dt.reproject(self.crs, coarse_transform)
        dt_avg100 = dt.reproject(self.crs, coarse_transform100).updateMask(1)
        tmax_avg = tmax.reproject(self.crs, coarse_transform)

        # FANO expression as a function of dT, calculated at the coarse resolution(s)
        Tc_warm = lst_avg_masked.expression(
            f"(lst - (dt_coeff * dt * (ndvi_threshold - ndvi) * 10))",
            {
                "dt_coeff": dt_coeff,
                "ndvi_threshold": high_ndvi_threshold,
                "ndvi": ndvi_avg_masked,
                "dt": dt_avg,
                "lst": lst_avg_masked,
            },
        )

        Tc_warm100 = lst_avg_masked100.expression(
            "(lst - (dt_coeff * dt * (ndvi_threshold - ndvi) * 10))",
            {
                "dt_coeff": dt_coeff,
                "ndvi_threshold": high_ndvi_threshold,
                "ndvi": ndvi_avg_masked100,
                "dt": dt_avg100,
                "lst": lst_avg_masked100,
            },
        )

        # In places where NDVI is really high, use the masked original lst at those places.
        # In places where NDVI is really low (water) use the unmasked original lst.
        # Everywhere else, use the FANO adjusted Tc_warm, ignoring masked water pixels.
        # In places where there is too much land covered by water 10% or greater,
        #   use a FANO adjusted Tc_warm from a coarser resolution (100km) that ignored masked water pixels.
        Tc_cold = (
            lst_avg_unmasked.where(
                (ndvi_avg_masked.gte(0).And(ndvi_avg_masked.lte(high_ndvi_threshold))),
                Tc_warm,
            )
            .where(ndvi_avg_masked.gt(high_ndvi_threshold), lst_avg_masked)
            .where(wet_region_mask_5km, Tc_warm100)
            .where(ndvi_avg_unmasked.lt(0), lst_avg_unmasked)
        )

        c_factor = Tc_cold.divide(tmax_avg)

        # bilinearly smooth the gridded c factor
        c_factor_bilinear = c_factor.resample("bilinear")

        return c_factor_bilinear.rename(["tcorr"]).set(
            {
                "system:index": self._index,
                "system:time_start": self._time_start,
                "tmax_source": tmax.get("tmax_source"),
                "tmax_version": tmax.get("tmax_version"),
            }
        )

    @lazy_property
    def tcorr_stats(self):
        """Compute the Tcorr 2.5 percentile and count statistics

        Returns
        -------
        dictionary

        """
        return ee.Image(self.tcorr_image).reduceRegion(
            reducer=ee.Reducer.percentile([2.5], outputNames=["value"]).combine(
                ee.Reducer.count(), "", True
            ),
            crs=self.crs,
            crsTransform=self.transform,
            geometry=self.image.geometry().buffer(1000),
            bestEffort=False,
            maxPixels=2 * 10000 * 10000,
            tileScale=1,
        )


  