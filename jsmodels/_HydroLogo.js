// convert logo png to geotiff:  https://geoconverter.infs.ch/raster
//      select EPSG:4326 for output format ONLY, leave other options blank
//adding a logo, inspired by:  https://gis.stackexchange.com/questions/331842/adding-a-logo-to-a-panel-on-an-app-in-google-earth-engine

/* 
    gdal_translate -of GTiff -a_srs EPSG:4326 -a_ullr -117.119811 32.700376 -117.059864 32.799896 Hydra_Carta_Main_Logo_500x100.jpg Hydra_Carta_Main_Logo.tif
    
    Then manually upload as a new geotiff asset.
*/

// prior version:  logo_hydracarta
var logo = ee.Image('projects/eda-bjonesneu-proto/assets/Hydra_Carta_Main_Logo').visualize({
    bands:  ['b1', 'b2', 'b3'],
    min: 0,
    max: 255
    })
    
exports.thumb = ui.Thumbnail({
    image: logo,
    params: { format: 'png' },
    })
    
//print(logo.geometry().bounds())