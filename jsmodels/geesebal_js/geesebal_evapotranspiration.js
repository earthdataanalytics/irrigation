exports.fexp_inst_et = function(image, Rn24hobs) {
  
  //GET ENERGY FLUXES VARIABLES AND LST
  var i_Rn = image.select('Rn'); 
  var i_G = image.select('G');
  var i_lst = image.select('T_LST_DEM');
  var i_H_final = image.select('H');
  
   //Map.addLayer(i_H_final,{min:0,max: 300},'H') ;
  // Map.addLayer(i_G,{min:0,max: 100},'G')  
  // Map.addLayer(i_Rn,{min:0,max: 600},'Rn')
  
  //FILTER VALUES
  i_H_final=i_H_final.where(i_H_final.lt(0),0);
  //var d_Rn_24h_med = Rn24hobs.reduceRegion({reducer: ee.Reducer.mean(),geometry: image.geometry().bounds(),scale: 20000,maxPixels: 900000000});
  //var n_Rn_24h_med = ee.Number(d_Rn_24h_med.get('Rn24h_G'));
  //var Rn24hobs =Rn24hobs.where(Rn24hobs, n_Rn_24h_med);
  
  //INSTANTANEOUS LATENT HEAT FLUX (LE) [W M-2]
  //BASTIAANSSEN ET AL. (1998)  
    var i_lambda_ET = i_H_final.expression( 
    '(i_Rn-i_G-i_H_fim)', {
      'i_Rn' : i_Rn,
      'i_G': i_G,
      'i_H_fim':i_H_final }).rename('LE');
    
 // Map.addLayer(i_lambda_ET,{min:0,max: 700},'LE')
 
  //FILTER
  i_lambda_ET=i_lambda_ET.where(i_lambda_ET.lt(0),0);
  
  //LATENT HEAT OF VAPORIZATION (LAMBDA) [J KG-1]
  //BISHT ET AL.(2005)
  //LAGOUARDE AND BURNET (1983)  
  var i_lambda = i_H_final.expression( 
    '(2.501-0.002361*(Ts-273.15))', {'Ts' : i_lst });
  
  //INSTANTANEOUS ET (ET_inst) [MM H-1]
  var i_ET_inst = i_H_final.expression( 
    '0.0036 * (i_lambda_ET/i_lambda)', {
      'i_lambda_ET' : i_lambda_ET,
      'i_lambda' : i_lambda  }).rename('ET_inst');
  
  //EVAPORATIVE FRACTION (EF)
  //CRAGO (1996)  
  var i_FE = i_H_final.expression( 
    'i_lambda_ET/(i_Rn-i_G)', {
      'i_lambda_ET' : i_lambda_ET,
      'i_Rn' : i_Rn,
      'i_G' : i_G }).rename('FE');
    
   //FILTER  
   i_FE=i_FE.where(i_lambda_ET.lt(0),0);
  
  //DAILY EVAPOTRANSPIRATION (ET_24h) [MM DAY-1]
  var i_ET24h_calc = i_H_final.expression( 
  '(86.4 *i_FE * Rn24hobs)/(i_lambda * dens)', {
    'i_FE' : i_FE,
    'i_lambda' : i_lambda,
    'Rn24hobs' : Rn24hobs,
    'dens': ee.Number(1000) }).rename('ET_24h');
    
  //i_ET24h_calc=i_ET24h_calc.where(i_ET24h_calc.lt(0),0)
  
  image = image.addBands([i_ET_inst, i_ET24h_calc, i_lambda_ET,i_FE]);
  return image;

};  
  
