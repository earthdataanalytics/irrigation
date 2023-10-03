exports.f_cloudMaskL457_SR = function(image) {
  var quality = image.select('pixel_qa');
    var c01 = quality.eq(66); //CLEAR, LOW CONFIDENCE CLOUD 
    var c02 = quality.eq(68); //WATER, LOW CONFIDENCE CLOUD 
  var mask = c01.or(c02);
  return image.updateMask(mask);
  };
  
//FUNCTION FO MASK CLOUD IN LANDSAT 8 FOR SURFACE REFELCTANCE
exports.f_cloudMaskL8_SR = function(image) {
  var quality = image.select('pixel_qa');
    var c01 = quality.eq(322); 
    var c02 = quality.eq(324); 
    var c03 = quality.eq(1346); 
  var mask = c01.or(c02).or(c03);
  return image.updateMask(mask);
  };

//ALBEDO
//TASUMI ET AL(2008) FOR LANDSAT 5 AND 7 
// scale 2.75e-05
exports.f_albedoL5L7=function(image) {
    var alfa = image.expression(
      '(0.254*B1) + (0.149*B2) + (0.147*B3) + (0.311*B4) + (0.103*B5) + (0.036*B7)',{
        'B1' : image.select(['B']).multiply(1),
        'B2' : image.select(['GR']).multiply(1),
        'B3' : image.select(['R']).multiply(1),
        'B4' : image.select(['NIR']).multiply(1),
        'B5' : image.select(['SWIR_1']).multiply(1),
        'B7' : image.select(['SWIR_2']).multiply(1)
      }).rename('ALFA');
    return image.addBands(alfa);
  };

//ALBEDO
//USING TASUMI ET AL. (2008) METHOD FOR LANDSAT 8
//COEFFICIENTS FROM KE ET AL. (2016)
exports.f_albedoL8=function(image) {
    var alfa = image.expression(
      '(0.130*B1) + (0.115*B2) + (0.143*B3) + (0.180*B4) + (0.281*B5) + (0.108*B6) + (0.042*B7)',{ 
        'B1' : image.select(['UB']).multiply(1),
        'B2' : image.select(['B']).multiply(1),
        'B3' : image.select(['GR']).multiply(1),
        'B4' : image.select(['R']).multiply(1),
        'B5' : image.select(['NIR']).multiply(1),
        'B6' : image.select(['SWIR_1']).multiply(1),
        'B7' : image.select(['SWIR_2']).multiply(1)
      }).rename('ALFA');
    return image.addBands(alfa);
  };
