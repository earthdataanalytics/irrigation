print(1)
// IMPORTS 
var indices_file = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_image.js');
var Masks = require('users/bjonesneu/earthdataanalytics:geesebal_js/geesebal_masks.js');

// GLOBAL VARIABLES
var MAX_CLOUD_COVER = 20;
var FIRSTYEARSENTINEL2 = 2015;
var INITIAL_COORDINATES = {
    latitude: -4.587476,
    longitude: 37.872162,
    altitudeParamater: 11,
};

// -+-+-+-+-+-+-+- LOG MESSAGES -+-+-+-+-+-+-+-+-+--+-
var chooseAnIndexText = 'Choose an index:'

var messageNoImagesInCollection =
    "There are no images in the selected date range, probably because the date range is small or there were many clouds in that period. Try a larger date range.";
var messageDrawPolygonFirst =
    'You must draw a polygon first. Click on the "New Polygon"  button and draw a polygon on the map.';
function messageInitialDateIsBiggerThanFinalDate(initialDate, endDate) {
    return (
        "Sorry, the start date (" +
        initialDate +
        ") cannot be greater than or equal to the end date (" +
        endDate +
        "). Enter a date less than " +
        endDate
    );
}
function messageInitialDateIsLowerThanFirstSentinel2Image(initialDate) {
    return (
        "Sorry, the initial date (" +
        initialDate +
        ") cannot be lower than the first Sentinel 2 image that was taken on 27-06-2015."
    );
}
function messageInitialDateIsBiggerThanToday(initialDate, today) {
    return (
        "Sorry, the initial date (" +
        initialDate +
        ") cannot be greater than or equal to today's date (" +
        today +
        "). Enter a date less than " +
        today
    );
}
function messageDateIsIncorrect(date) {
    return (
        "Sorry, the date (" +
        date +
        ") is incorrect. Please, check the date and try again."
    );
}

var symbols = {
    polygon: "⬛",
};

var backgroundColors = "rgba(255, 255, 255, 0)";

function current_position(point) {

    // edir point
    mainMapPanel.addLayer(point)
    // layer name = Your location
    mainMapPanel.layers().get(0).setName('Your location')

    mainMapPanel.centerObject(point, INITIAL_COORDINATES.altitudeParamater);

}

function errorHandle(error) {
    print(error);
}


function clearGeometry() {
    var layers = drawingTools.layers();
    layers.get(0).geometries().remove(layers.get(0).geometries().get(0));
}

function drawPolygon() {
    clearGeometry();
    drawingTools.setShape('polygon');
    drawingTools.draw();
}


function clearDefinedGeometry(drawingTools) {

    // try to read layer if not exit without and error
    try {
        var layer = drawingTools.layers().get(0);
        layer.geometries().remove(layer.geometries().get(0));
    } catch (error) {
        return
    }
}


// Panel 1 Inside the map
function newPolygonPanel(
    polygonSymbol,
    drawNewPolygon,
    drawingTools,
    clearDefinedGeometry
) {
    var polygonPanel = ui.Panel({
        widgets: [
            ui.Button({
                label: polygonSymbol + " New Polygon",
                onClick: function () {
                    clearDefinedGeometry(drawingTools);
                    drawNewPolygon(drawingTools);
                },
                style: { stretch: "horizontal" },
            }),
            ui.Label('1. Draw a polygon.'),
            ui.Label('2. Click on the "Calculate" button.'),
        ],
        style: { position: "bottom-left" },
        layout: null,
    });

    return polygonPanel;
}
//polygon panel
var controlPanel = ui.Panel({
    widgets: [
        // ui.Label('1. Select a drawing mode.'),
        ui.Button({
            label: symbols.polygon + ' New Polygon',
            onClick: drawPolygon,
            style: { stretch: 'horizontal' }
        }),
        ui.Label('1. Draw a polygon.'),
        ui.Label('2. Click on the "Calculate" button.'),

    ],
    style: { position: 'bottom-left' },
    layout: null,
});

var controlPanel = newPolygonPanel(
    symbols.polygon,
    drawPolygon,
    drawingTools,
    clearDefinedGeometry
);


var panel = ui.Panel({ style: { width: '30%' } });

function getArrayOfLastYearFromFirstSentinel2Image() {

    var currentDate = new Date()
    var currentYear = currentDate.getFullYear();
    var arrayOfYears = [];
    for (var year = FIRSTYEARSENTINEL2; year <= currentYear; year++) {
        arrayOfYears.push(year.toString());
    }
    return arrayOfYears
}
var year = getArrayOfLastYearFromFirstSentinel2Image()

var month = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
var day = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
    '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23',
    '24', '25', '26', '27', '28', '29', '30', '31'];

var selectYear1 = ui.Select({
    items: year,
    value: year[year.length - 1],
    style: { padding: '0px 0px 0px 10px', stretch: 'horizontal' }
});
var selectYear2 = ui.Select({
    items: year,
    value: year[year.length - 1],
    style: { padding: '0px 0px 0px 10px', stretch: 'horizontal' }
});

var selectMonths1 = ui.Select({
    items: month,
    value: month[0],
    style: { stretch: 'horizontal' }
});
var selectMonths2 = ui.Select({
    items: month,
    value: month[1],
    style: { stretch: 'horizontal' }
});
var selectDay1 = ui.Select({
    items: day,
    value: day[0],
    style: { padding: '0px 0px 0px 10px', stretch: 'horizontal' }
});
var selectDay2 = ui.Select({
    items: day,
    value: day[0],
    style: { padding: '0px 0px 0px 10px', stretch: 'horizontal' }
});







function handleChangePallete() {
    var indexType = selectIndex.getValue();
    // set all legends and colorbars to false except ndvi
    for (var index in indices) {

        if (index != indexType) {
            indices[index].legendTitle.style().set({ shown: false });
            indices[index].colorBar.style().set({ shown: false });
            indices[index].legendLabels.style().set({ shown: false });
        } else {
            indices[index].legendTitle.style().set({ shown: true });
            indices[index].colorBar.style().set({ shown: true });
            indices[index].legendLabels.style().set({ shown: true });
        }
    }
}



function addSurfaceTemperatureFromGEOSCFToSentinel2(image) {
    // add surface temperature from GEOS-CF to Sentinel 2 image
    var geoscf = ee.ImageCollection('NASA/GEOS-CF/v1/rpl/tavg1hr')

    var surfaceTemperature = geoscf.select('TS').filterDate(image.date().format('YYYY-MM-dd'), image.date().advance(1, 'day').format('YYYY-MM-dd')).first()

    return image.addBands(surfaceTemperature.select('TS').rename('T_LST'), null, true);
}


function getSentinel2Collection(polygonShape) {
    var satellite = 'COPERNICUS/S2'
    var collection = ee.ImageCollection(satellite)
        .filterBounds(polygonShape)
        .filterDate(selectYear1.getValue() +
            "-" + selectMonths1.getValue() + "-" +
            selectDay1.getValue(), selectYear2.getValue() + "-" +
            selectMonths2.getValue() + "-" + selectDay2.getValue())
        .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'Less_Than', 10)


        .select(["B1", "B2", "B3", "B4", "B8", "B11", "B12"],
            ["UB", "B", "GR", "R", "NIR", "SWIR_1", "SWIR_2"])
        .map(scaleSentinel2Image)
        .map(Masks.f_albedoL5L7)
        .map(addSurfaceTemperatureFromGEOSCFToSentinel2)


    return collection
}


function prepSrL8(image) {
    var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
    var saturationMask = image.select('QA_RADSAT').eq(0);

    var getFactorImg = function (factorNames) {
        var factorList = image.toDictionary().select(factorNames).values();
        return ee.Image.constant(factorList);
    };
    var scaleImg = getFactorImg([
        'REFLECTANCE_MULT_BAND_.|TEMPERATURE_MULT_BAND_ST_B10']);
    var offsetImg = getFactorImg([
        'REFLECTANCE_ADD_BAND_.|TEMPERATURE_ADD_BAND_ST_B10']);
    var scaled = image.select('SR_B.|ST_B10').multiply(scaleImg).add(offsetImg);

    return image.addBands(scaled, null, true)
        .updateMask(qaMask).updateMask(saturationMask);
}

function maskL457sr(image) {
    var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
    var saturationMask = image.select('QA_RADSAT').eq(0);

    var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
    var thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0);

    return image.addBands(opticalBands, null, true)
        .addBands(thermalBand, null, true)
        .updateMask(qaMask)
        .updateMask(saturationMask);
}


function getLansat8Collection(polygonShape) {

    var collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(polygonShape)
        .filterDate(
            selectYear1.getValue() +
            "-" +
            selectMonths1.getValue() +
            "-" +
            selectDay1.getValue(),
            selectYear2.getValue() +
            "-" +
            selectMonths2.getValue() +
            "-" +
            selectDay2.getValue()
        )
        .map(
            prepSrL8
        )
        .select(["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10"],
            ["UB", "B", "GR", "R", "NIR", "SWIR_1", "SWIR_2", "T_LST"])
        .map(Masks.f_albedoL5L7)
        .filterMetadata("CLOUD_COVER_LAND", "less_than", 20)
    return collection;
}
var LANDSAT_5_7_BANDS = {
    "OFFICIAL": ["SR_B1", "SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7", "ST_B6"],
    "CUSTOM": ["UB", "B", "GR", "R", "NIR", "SWIR_1", "SWIR_2", "T_LST"],
}
function getLansat7Collection(polygonShape) {
    var collection = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        .filterBounds(polygonShape)
        .filterDate(
            selectYear1.getValue() +
            "-" +
            selectMonths1.getValue() +
            "-" +
            selectDay1.getValue(),
            selectYear2.getValue() +
            "-" +
            selectMonths2.getValue() +
            "-" +
            selectDay2.getValue()
        )
        .map(
            maskL457sr
        )
        .select(LANDSAT_5_7_BANDS["OFFICIAL"], LANDSAT_5_7_BANDS["CUSTOM"])
        .map(Masks.f_albedoL5L7)
        .filterMetadata("CLOUD_COVER_LAND", "less_than", MAX_CLOUD_COVER)

    return collection;
}

function getLansat5Collection(polygonShape) {
    var collection = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        .filterBounds(polygonShape)
        .filterDate(
            selectYear1.getValue() +
            "-" +
            selectMonths1.getValue() +
            "-" +
            selectDay1.getValue(),
            selectYear2.getValue() +
            "-" +
            selectMonths2.getValue() +
            "-" +
            selectDay2.getValue()
        )
        .map(
            maskL457sr
        )
        .select(LANDSAT_5_7_BANDS["OFFICIAL"], LANDSAT_5_7_BANDS["CUSTOM"])
        .map(Masks.f_albedoL5L7)
        .filterMetadata("CLOUD_COVER_LAND", "less_than", MAX_CLOUD_COVER)

    return collection;
}
var dateNow = new Date()


function checkIfInitialDateIsBiggerThanFinalDate(initialDate, endDate) {
    var valuesStart = initialDate.split("-");
    var valuesEnd = endDate.split("-");
    var dateStart = new Date(valuesStart[2], (valuesStart[1] - 1), valuesStart[0]);
    var dateEnd = new Date(valuesEnd[2], (valuesEnd[1] - 1), valuesEnd[0]);
    if (dateStart >= dateEnd) {
        return true;
    }
    return false;
}



function checkIfYearIsLeap(year) {
    var isLeap = false
    if (year % 4 == 0) {
        if (year % 100 == 0) {
            if (year % 400 == 0) {
                isLeap = true
            } else {
                isLeap = false
            }
        }
        else {
            isLeap = true
        }
    }
    else {
        isLeap = false
    }
    return isLeap
}

function checkIfDateIsCorrect(day, month, year) {
    var thereIsError = false
    var yearIsLeap = checkIfYearIsLeap(year)

    if (month == 2) {
        if (yearIsLeap) {
            if (day > 29) {
                thereIsError = true
            }
        } else {
            if (day > 28) {
                thereIsError = true
            }
        }
    }
    else if (month == 4 || month == 6 || month == 9 || month == 11) {
        if (day > 30) {
            thereIsError = true
        }
    }

    return thereIsError
}

var runIndexImageButton = ui.Button({

    label: 'Calculate',

    onClick: runMap,


    style: { padding: '0px 10px', stretch: 'horizontal', backgroundColor: backgroundColors, color: "#1B72A0" }

});

function checkIfThereIsPolygon() {
    var thereIsPolygon = false;
    var layers = drawingTools.layers();
    if (layers.get(0).geometries().length() > 0) {
        thereIsPolygon = true;
    } else {
        alert(messageDrawPolygonFirst);
    }
    return thereIsPolygon

}

function checkIfThereIsNoImagesFromCollection(collection) {
    var thereIsImages = false;
    if (collection.size().getInfo() > 0) {
        thereIsImages = true;
    } else {
        alert(messageNoImagesInCollection);
    }
    return thereIsImages

}
function runMap() {

    var polygonShape = drawingTools.layers().get(0).getEeObject();
    geometryLayer.set('shown', false);

    var initialDate = (selectDay1.getValue() + "-" + selectMonths1.getValue() +
        "-" + selectYear1.getValue());
    var endDate = (selectDay2.getValue() + "-" + selectMonths2.getValue() + "-" + selectYear2.getValue());
    var dateNow = new Date()
    var today = (dateNow.getDate() + '-' + (dateNow.getMonth() + 1) + '-' + dateNow.getFullYear()).toString()
    var startDateIsIncorrect = checkIfDateIsCorrect(selectDay1.getValue(), selectMonths1.getValue(), selectYear1.getValue())
    var endDateIsIncorrect = checkIfDateIsCorrect(selectDay2.getValue(), selectMonths2.getValue(), selectYear2.getValue())

    if (startDateIsIncorrect) {
        alert(messageDateIsIncorrect(initialDate))
        return
    }
    if (endDateIsIncorrect) {
        alert(messageDateIsIncorrect(endDate))
        return
    }
    if (checkIfInitialDateIsBiggerThanFinalDate(initialDate, endDate)) {
        alert(messageInitialDateIsBiggerThanFinalDate(initialDate, endDate));
    }
    else if (!checkIfInitialDateIsBiggerThanFinalDate(initialDate, '01-07-2015')) {
        alert(messageInitialDateIsLowerThanFirstSentinel2Image(initialDate));


    } else if (checkIfInitialDateIsBiggerThanFinalDate(initialDate, today)) {
        alert(messageInitialDateIsBiggerThanToday(initialDate, today))
    }

    else {
        var thereIsAPolygon = checkIfThereIsPolygon();

        if (!thereIsAPolygon) {
            return;
        }

        var indexType = selectIndex.getValue()

        var index_metadata = indices[indexType];
        var serie_mean = undefined;
        if (index_metadata.collectionType == 'SentinelSebal') {
            var sentinelCollection = getSentinel2Collection(polygonShape);
            var thereIsImages = checkIfThereIsNoImagesFromCollection(sentinelCollection);
            if (!thereIsImages) {
                return;
            }
            var sentinel_coleccion = indices[indexType].imageFuntion(sentinelCollection, polygonShape).map(function (image) {
                return image.clip(polygonShape)
            })

            serie_mean = ui.Chart.image.series(sentinel_coleccion.select("ET_24h"),
                polygonShape, ee.Reducer.mean(), 20).setOptions(indices[indexType].chartOptions);


        } else if (index_metadata.collectionType == 'LandsatSebal') {

            var landsat8Collection = getLansat8Collection(polygonShape);
            var landsat7Collection = getLansat7Collection(polygonShape);
            var landsat5Collection = getLansat5Collection(polygonShape);

            var landsatCollection = landsat8Collection.merge(landsat7Collection).merge(landsat5Collection)
            var log = landsatCollection.map(function (image) {
                return ee.Feature(null, { 'image_id': image.id(), 'date': image.date().format('YYYY-MM-dd') })
            })

            for (var i = 0; i < log.size().getInfo(); i++) {
                var image = ee.Image(log.toList(1, i).get(0))
                var image_id = image.get('image_id').getInfo()
                var date = image.get('date').getInfo()
                console.log("---------")
                console.log(image_id)
                console.log(date)
                console.log("---------")
            }

            var thereIsImages = checkIfThereIsNoImagesFromCollection(landsatCollection);
            if (!thereIsImages) {
                return;
            }
            var landsat_coleccion = indices[indexType].imageFuntion(landsatCollection, polygonShape)
            // var coleccion = collection.map(function (entrada) {
            //     return indices[indexType].chartFunction(entrada, polygonShape)
            // });
            serie_mean = ui.Chart.image.series(landsat_coleccion.select("ET_24h"),
                polygonShape, ee.Reducer.mean(), 20).setOptions(indices[indexType].chartOptions);
        }
        panel.widgets().set(9, serie_mean);
    }
}

// -+-+-+-+-+-+- MAIN MAP -+-+-+-+-+-+-+-

var mainMapPanel = ui.Map();
ui.util.getCurrentPosition(current_position, errorHandle)



var start_end_date = {
    start_day: selectDay1.getValue(),
    start_month: selectMonths1.getValue(),
    start_year: selectYear1.getValue(),
    end_day: selectDay2.getValue(),
    end_month: selectMonths2.getValue(),
    end_year: selectYear2.getValue(),
}

var indices = indices_file.indices(backgroundColors, mainMapPanel, start_end_date)
var indexTypeArray = [];
for (var index in indices) {
    if (indices[index].show) {
        indexTypeArray.push(index);
    }
}

var drawingTools = mainMapPanel.drawingTools();
drawingTools.setShown(false);

while (drawingTools.layers().length() > 0) {
    var layer = drawingTools.layers().get(0);
    drawingTools.layers().remove(layer);
}

var geometryLayer =
    ui.Map.GeometryLayer({ geometries: null, name: 'geometry', color: '23cba7', shown: false });

drawingTools.layers().add(geometryLayer);

// -+-+-+-+-+- UI -+-+-+-+-+-
mainMapPanel.add(controlPanel);

var panel = ui.Panel({
    layout: ui.Panel.Layout.flow('vertical'),
    style: { width: '400px' }
});

var mapTitle = ui.Label('GEESEBAL');
mapTitle.style().set('color', 'green');
mapTitle.style().set('fontWeight', 'bold');
mapTitle.style().set({
    fontSize: '20px',
    padding: '10px'
});

var mapDesc = ui.Label('');
mapDesc.style().set({
    fontSize: '16px',
    padding: '0px 10px'
});



var selectIndexLabel = ui.Label(chooseAnIndexText);
selectIndexLabel.style().set({
    fontWeight: 'bold', backgroundColor: backgroundColors,
});

var selectStartLabel = ui.Label('Start Date (dd/MM/YY):');
selectStartLabel.style().set({ fontWeight: 'bold', backgroundColor: backgroundColors });
var selectEndLabel = ui.Label('End Date (dd/MM/YY):');
selectEndLabel.style().set({ fontWeight: 'bold', backgroundColor: backgroundColors });


var selectIndex = ui.Select({
    items: indexTypeArray,
    value: indexTypeArray[0],
    onChange: handleChangePallete,
    style: {
        padding: "0px 0px 0px 10px",
        stretch: "horizontal",
        backgroundColor: backgroundColors,
    },
});
handleChangePallete();





Map.style().set('cursor', 'crosshair');


panel.add(mapTitle);

panel.add(ui.Panel([selectIndexLabel, selectIndex],
    ui.Panel.Layout.flow('horizontal')

));
panel.add(mapDesc);
panel.add(selectStartLabel);
panel.add(ui.Panel([selectDay1, selectMonths1, selectYear1],
    ui.Panel.Layout.flow('horizontal')));
panel.add(selectEndLabel);
panel.add(ui.Panel([selectDay2, selectMonths2, selectYear2],
    ui.Panel.Layout.flow('horizontal')));


panel.add(runIndexImageButton);

function makeLegendPanel() {
    var arrayLegendPanel = [];
    for (var index in indices) {
        arrayLegendPanel.push(indices[index].legendTitle);
        arrayLegendPanel.push(indices[index].colorBar);
        arrayLegendPanel.push(indices[index].legendLabels);
    }
    var legendPanel = ui.Panel(arrayLegendPanel);
    legendPanel.style().set({ position: "bottom-right", backgroundColor: backgroundColors });
    return legendPanel;
}
var legendPanel = makeLegendPanel();


panel.widgets().set(9, legendPanel);



ui.root.insert(0, panel);

ui.root.clear();
ui.root.add(ui.SplitPanel(panel, mainMapPanel));