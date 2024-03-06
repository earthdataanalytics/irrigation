// -+-+-+-+-+-+-+-+- IMPORTS -+-+-+-+-+-+-+-+-+-
var meteorologicalData = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_era5.js');
var endmembers = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_endmembers.js');
var tools = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_tools.js');
var evapotranspiration = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_evapotranspiration.js');


// -+-+-+-+-+-+-+-+- indices -+-+-+-+-+-+-+-+-+-
exports.indices = function (backgroundColors, mainMapPanel, start_end_date) {
    function makeColorBarParams(palette, min, max) {
        return {
            bbox: [0, 0, 1, 0.1],
            dimensions: '100x10',
            format: 'png',
            min: min,
            max: max,
            palette: palette,
        };
    }



    function makeColorBar(indexColor) {
        var colorBar = ui.Thumbnail({
            image: ee.Image.pixelLonLat().select(0),
            params: makeColorBarParams(indexColor.palette),
            style: { stretch: "horizontal", margin: "0px 8px", maxHeight: "24px" },
        });
        return colorBar;
    }

    function makeLegendLabels(indexColor) {
        var legendLabels = ui.Panel({
            widgets: [
                ui.Label(indexColor.min, {
                    margin: "4px 8px",
                    backgroundColor: backgroundColors,
                }),
                ui.Label((indexColor.max + indexColor.min) / 2, {
                    margin: "4px 8px",
                    textAlign: "center",
                    stretch: "horizontal",
                    backgroundColor: backgroundColors,
                }),
                ui.Label(indexColor.max, {
                    margin: "4px 8px",
                    backgroundColor: backgroundColors,
                }),
            ],
            layout: ui.Panel.Layout.flow("horizontal"),
            style: { backgroundColor: backgroundColors },
        });
        return legendLabels;
    }

    function makeLegendTitle(title) {
        var legendTitle = ui.Label({
            value: title,
            style: { fontWeight: "bold", backgroundColor: backgroundColors },
        });
        return legendTitle;
    }

    function makeChartOptions(indexType) {
        var options = {
            title: indexType,
            vAxis: { title: indexType + ' Value' },
            hAxis: {
                title: 'Date',
                format: 'dd-MM',

            }
        };
        return options
    }

    function getMaxValue(value){
        // use reduce
        var maxValue = value.reduceRegion({
            reducer: ee.Reducer.max(),
            scale: 30,
            maxPixels: 1e9
          });
        return maxValue
    }

    function getMinValue(value){
        // use reduce
        var minValue = value.reduceRegion({
            reducer: ee.Reducer.min(),
            scale: 30,
            maxPixels: 1e9
          });
        return minValue
    }

    function printValue(title, value){
        return
        console.log(title)
        console.log("Max value: ")
        console.log(getMaxValue(value))
        console.log("Min value: ")
        console.log(getMinValue(value))
    }
     // --------------- GEESEBAL LANDSAT INDEX -----------------

     var geesebalColor = {

        min: 0,
        max: 7,
        bands: ['ET_24h'],


        palette: ['deac9c', 'EDD9A6', 'f2dc8d', 'fff199', 'b5e684', '3BB369', '20998F', '25b1c1', '16678A', '114982', '0B2C7A']
    }


    // --------------- GEESEBAL LANDSAT INDEX -----------------



    var geesebalLandsatColorBar = makeColorBar(geesebalColor);

    var geesebalLandsatLegendLabels = makeLegendLabels(geesebalColor);

    var geesebalLandsatLegendTitle = makeLegendTitle("GEESEBAL Palette");

    function processSingleImageLandsat(image, _) {
        var image_geeSEBAL = image
        var topNDVI = 5
        var coldestTs = 20
        var lowestNDVI = 10
        var hottestTs = 20

        var image = image_geeSEBAL
        var index = image.get('system:index'); //LANDSAT ID
        var sun_elevation = image.get("SUN_ELEVATION") // NEW IN COLLECTION2 
        var azimuth_angle = image.get('SOLAR_AZIMUTH_ANGLE'); //SOLAR AZIMUTH ANGLE FROM LS
        var time_start = image.get('system:time_start'); //TIME START FROM LS
        var date = ee.Date(time_start); //GET EE.DATE
        var year = ee.Number(date.get('year')); //YEAR
        var month = ee.Number(date.get('month')); //MONTH
        var day = ee.Number(date.get('day')); //DAY
        var hour = ee.Number(date.get('hour')); //HOUR
        var min = ee.Number(date.get('minutes')); //MINUTES
        var crs = image.projection().crs(); //PROJECTION
        var transform = ee.List(ee.Dictionary(ee.Algorithms.Describe(image.projection())).get('transform'));

        //ENDMEMBERS
        var p_top_NDVI = ee.Number(topNDVI); //TOP NDVI PERCENTILE (FOR COLD PIXEL)
        var p_coldest_Ts = ee.Number(coldestTs); //COLDEST TS (FOR COLD PIXEL)
        var p_lowest_NDVI = ee.Number(lowestNDVI); //LOWEST NDVI (FOR HOT PIXEL)
        var p_hottest_Ts = ee.Number(hottestTs); //HOTTEST TS (FOR HOT PIXEL)

        //METEOROLOGY PARAMETERS - GLDAS 2.1 AND 2.0
        var col_ERA5 = meteorologicalData.era5(image, time_start);


        var T_air = col_ERA5.select('AirT_G');
       
        var ux = col_ERA5.select('ux_G');

        //RELATIVE HUMIDITY [%]
        var UR = col_ERA5.select('RH_G');

        //NET RADIATION 24H [W M-2]
        var Rn24hobs = col_ERA5.select('Rn24h_G');
        
        //SRTM DATA ELEVATION
        var SRTM_ELEVATION = 'USGS/SRTMGL1_003';
        var srtm = ee.Image(SRTM_ELEVATION).clip(image.geometry().bounds());
        var z_alt = srtm.select('elevation');

        //SPECTRAL IMAGES (NDVI, EVI, SAVI, LAI, T_LST, e_0, e_NB, long, lat)
        image = tools.spec_ind(image, false);

        //LAND SURFACE TEMPERATURE 
        image = tools.LST_correction(image, z_alt, T_air, UR, sun_elevation, hour, min);
        
        printValue("LAND SURFACE TEMPERATURE NW", image.select('LST_NW'))
        printValue("LAND SURFACE TEMPERATURE DEM", image.select('T_LST_DEM'))
        printValue("LAND SURFACE TEMPERATURE NEG", image.select('LST_neg'))
        printValue("Solar_angle_cos", image.select('Solar_angle_cos'))
        //COLD PIXEL
        var d_cold_pixel = endmembers.fexp_cold_pixel(image, p_top_NDVI, p_coldest_Ts);

        //COLD PIXEL NUMBER
        var n_Ts_cold = ee.Number(d_cold_pixel.get('temp'));
        // console.log("COLD PIXEL NUMBER: ")
        // console.log( n_Ts_cold)
        //INSTANTANEOUS OUTGOING LONG-WAVE RADIATION [W M-2]
        image = tools.fexp_radlong_up(image);

        //INSTANTANEOUS INCOMING SHORT-WAVE RADIATION [W M-2]
        image = tools.fexp_radshort_down(image, z_alt, T_air, UR, sun_elevation);

        //INSTANTANEOUS INCOMING LONGWAVE RADIATION [W M-2]
        image = tools.fexp_radlong_down(image, n_Ts_cold);

        //INSTANTANEOUS NET RADIATON BALANCE [W M-2]
        image = tools.fexp_radbalance(image);

        //SOIL HEAT FLUX (G) [W M-2]
        image = tools.fexp_soil_heat(image);

        //HOT PIXEL 
        var d_hot_pixel = endmembers.fexp_hot_pixel(image, p_lowest_NDVI, p_hottest_Ts);
        //SENSIBLE HEAT FLUX (H) [W M-2]
        image = tools.fexp_sensible_heat_flux(image, ux, UR, Rn24hobs, n_Ts_cold, d_hot_pixel);

        //DAILY EVAPOTRANSPIRATION (ET_24H) [MM DAY-1]
        image = evapotranspiration.fexp_inst_et(image, Rn24hobs);

      
        return image
    }

    function getGEESEBALLandsatImage(collection, polygonShape) {
        // iterate over collection and apply processSingleImage function
        var newCollection = ee.ImageCollection([]);
        for (var i = 0; i < collection.size().getInfo(); i++) {
            var image = ee.Image(collection.toList(collection.size()).get(i));
            var newImage = processSingleImageLandsat(image, null).clip(polygonShape)
            newCollection = newCollection.merge(newImage);
        }

        image = ee.Image(newCollection.mean());
      

        //ADD ALL LAYER BUT BY DEFAULD ONLY SHOW ET_24H
        mainMapPanel.addLayer(
            image,
            geesebalColor,
            "GEESEBAL_" +
            start_end_date.start_day +
            "-" +
            start_end_date.start_month +
            "-" +
            start_end_date.start_year,
            1
        );

        

        return newCollection
    }

    function GEESEBAL_LANDSAT_CHART(entrada, _) {

       return 0
    }

    var geesebalLandsatChartOptions = makeChartOptions('GEESEBAL_LANDSAT')



    var indices = {
        "GEESEBAL_LANDSAT": {
            show: true,
            showOnPhone: true,
            colorBar: geesebalLandsatColorBar,
            legendLabels: geesebalLandsatLegendLabels,
            legendTitle: geesebalLandsatLegendTitle,
            imageFuntion: getGEESEBALLandsatImage,
            chartFunction: GEESEBAL_LANDSAT_CHART,
            chartOptions: geesebalLandsatChartOptions,
            collectionType: 'LandsatSebal'
        },
    };


    return indices
}