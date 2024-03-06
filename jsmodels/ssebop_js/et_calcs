
function _air_pressure(elev, method) {
    /** Air pressure from elevation
    *
    * Parameters
    * ----------
    * elev : ee.Image or ee.Number
    *     Elevation [m].
    * method : str, optional
    *     Method to use. Default is 'asce'.
    *
    * Returns
    * -------
    * pair : ee.Image or ee.Number
    *     Air pressure [kPa].
    *
    * Notes
    * -----
    *   The current calculation in Ref-ET:
    *   101.3 * (((293 - 0.0065 * elev) / 293) ** (9.8 / (0.0065 * 286.9)))
        Equation 3 in ASCE-EWRI 2005:
        101.3 * (((293 - 0.0065 * elev) / 293) ** 5.26)
        Per Dr. Allen, the calculation with full precision:
        101.3 * (((293.15 - 0.0065 * elev) / 293.15) ** (9.80665 / (0.0065 * 286.9)))

    **/

    
    if (method == 'asce') {
        return elev.multiply(-0.0065).add(293).divide(293).pow(5.26).multiply(101.3)
    }
    else if (method == 'refet') {
        return elev.multiply(-0.0065).add(293).divide(293).pow(9.8 / (0.0065 * 286.9)).multiply(101.3)
    }
   

}

function _sat_vapor_pressure(temperature) {
    /** Saturated vapor pressure from temperature
    *
    * Parameters
    * ----------
    * temperature : ee.Image or ee.Number
    *     Temperature [C].
    *
    * Returns
    * -------
    * es : ee.Image or ee.Number
    *     Saturated vapor pressure [kPa].
    *
    * Notes
    * -----
    *  es = 0.6108 * exp(17.27 * temperature / (temperature + 237.3))
    *
    **/
    return temperature.add(237.3).pow(-1).multiply(temperature).multiply(17.27).exp().multiply(0.6108)
}

function _es_slope(tmean, method) {
    /** Slope of the saturation vapor pressure-temperature curve
    
    Parameters
    ----------
    tmean : ee.Image or ee.Number
        Mean air temperature [C].
    method : {'asce' (default), 'refet'}, optional
        Calculation method:
        * 'asce' -- Calculations will follow ASCE-EWRI 2005 [1] equations.
        * 'refet' -- Calculations will follow RefET software.

    Returns
    -------
    ee.Image or ee.Number

    Notes
    -----
    4098 * 0.6108 * exp(17.27 * T / (T + 237.3)) / ((T + 237.3) ** 2))

    **/

    if (method == 'refet') {
        return _sat_vapor_pressure(tmean)
            .multiply(4098.0).divide(tmean.add(237.3).pow(2))
    }
    else if (method == 'asce') {
        return tmean.add(237.3).pow(-1).multiply(tmean).multiply(17.27).exp()
            .multiply(2503.0).divide(tmean.add(237.3).pow(2))
    } 
}

function _actual_vapor_pressure(q, pair) {
    /** Actual vapor pressure from specific humidity
    *
    * Parameters
    * ----------
    * q : ee.Image or ee.Number
    *     Specific humidity [kg/kg].
    * pair : ee.Image or ee.Number
    *     Air pressure [kPa].
    *
    * Returns
    * -------
    * ea : ee.Image or ee.Number
    *     Actual vapor pressure [kPa].
    *
    * Notes
    * -----
    * ea = q * pair / (0.622 + 0.378 * q)
    *
    **/
    return q.multiply(pair).divide(q.multiply(0.378).add(0.622));
}

function _specific_humidity(ea, pair) {
    /** Specific humidity from actual vapor pressure
    *
    * Parameters
    * ----------
    * ea : ee.Image or ee.Number
    *     Specific humidity [kPa].
    * pair : ee.Image or ee.Number
    *     Air pressure [kPa].
    *
    * Returns
    * -------
    * q : ee.Image or ee.Number
    *     Specific humidity [kg/kg].
    *
    * Notes
    * -----
    * q = 0.622 * ea / (pair - 0.378 * ea)
    *
    **/
    return ea.multiply(-0.378).add(pair).pow(-1).multiply(ea).multiply(0.622);
}

function _vpd(es, ea) {
    /** Vapor pressure deficit
    *
    * Parameters
    * ----------
    * es : ee.Image or ee.Number
    *     Saturated vapor pressure [kPa].
    * ea : ee.Image or ee.Number
    *     Actual vapor pressure [kPa].
    *
    * Returns
    * -------
    * ee.Image or ee.Number
    *     Vapor pressure deficit [kPa].
    *
    **/


    return es.subtract(ea).max(0);
}


function _precipitable_water(ea, pair) {
    /** Precipitable water in the atmosphere (Eq. D.3)
    *
    * Parameters
    * ----------
    * ea : ee.Image
    *     Vapor pressure [kPa].
    * pair : ee.Image or ee.Number
    *     Air pressure [kPa].
    *
    * Returns
    * -------
    * ee.Image or ee.Number
    *     Precipitable water [mm].
    *
    * Notes
    * -----
    * w = pair * 0.14 * ea + 2.1
    *
    **/
    return ea.multiply(pair).multiply(0.14).add(2.1);
}

function _doy_fraction(doy) {
    /** Fraction of the DOY in the year (Eq. 50)
    *
    * Parameters
    * ----------
    * doy : ee.Image or ee.Number
    *     Day of year.
    *
    * Returns
    * -------
    * ee.Image or ee.Number
    *     DOY fraction [radians].
    *
    **/
    return doy.multiply(2.0 * Math.PI / 365);
}


function _delta(doy, method) {
    /**Earth declination (Eq. 51)
        *
        * Parameters
        * ----------
        * doy : ee.Image or ee.Number
        *     Day of year.
        * method : {'asce' (default), 'refet'}, optional
        *     Calculation method:
        *     * 'asce' -- Calculations will follow ASCE-EWRI 2005 [1] equations.
        *     * 'refet' -- Calculations will follow RefET software.
        *
        * Returns
        * -------
        * ee.Image or ee.Number
        *     Earth declination [radians].
        *
        * Notes
        * -----
        * Original equation in Duffie & Beckman (1980) (with conversions to radians):
        *     23.45 * (pi / 180) * sin(2 * pi * (doy + 284) / 365)
        * Equation 24 in ASCE-EWRI (2005):
        *     0.409 * sin((2 * pi * doy / 365) - 1.39)
        *
        **/

    if (method == 'asce') {
        return _doy_fraction(doy).subtract(1.39).sin().multiply(0.409);
    } else {
        return doy.add(284).multiply(2 * Math.PI / 365).sin()
            .multiply(23.45 * (Math.PI / 180));
    }
}

function _dr(doy) {
    /**Inverse square of the Earth-Sun Distance (Eq. 50)
        *
        * Parameters
        * ----------
        * doy : ee.Image or ee.Number
        *     Day of year.
        *
        * Returns
        * -------
        * ee.Image or ee.Number
        *
        * Notes
        * -----
        * This function returns 1 / d^2, not d, for direct use in radiance to
        *   TOA reflectance calculation
        * pi * L * d^2 / (ESUN * cos(theta)) -> pi * L / (ESUN * cos(theta) * d)
        *
        **/
    return _doy_fraction(doy).cos().multiply(0.033).add(1.0);
}


function _seasonal_correction(doy) {
    // Seasonal correction for solar time (Eqs. 57 & 58)

    // Parameters
    // ----------
    // doy : ee.Image or ee.Number
    //     Day of year.

    // Returns
    // ------
    // ee.Image or ee.Number
    //     Seasonal correction [hour]

    // Notes
    // -----
    // sc = 0.1645 * sin(2 * b) - 0.1255 * cos(b) - 0.0250 * sin(b)

    var b = doy.subtract(81).divide(364.0).multiply(2 * Math.PI);
    return b.multiply(2).sin().multiply(0.1645)
        .subtract(b.cos().multiply(0.1255)).subtract(b.sin().multiply(0.0250));
}


function _solar_time_rad(lon, time_mid, sc) {
    // Solar time (i.e. noon is 0) (Eq. 55)

    // Parameters
    // ----------
    // lon : ee.Image or ee.Number
    //     Longitude [radians].
    // time_mid : ee.Image or ee.Number
    //     UTC time at midpoint of period [hours].
    // sc : ee.Image or ee.Number
    //     Seasonal correction [hours].

    // Returns
    // -------
    // ee.Image or ee.Number
    //     Solar time [hours].

    // Notes
    // -----
    // This function could be integrated into the _omega() function since they are
    // always called together (i.e. _omega(_solar_time_rad()).  It was built
    // independently from _omega to eventually support having a separate
    // solar_time functions for longitude in degrees.
    // time = (lon * 24 / (2 * Math.PI)) + time_mid + sc - 12

    return lon.multiply(24 / (2 * Math.PI)).add(time_mid).add(sc).subtract(12);
}


function _omega(solar_time) {
    // Solar hour angle (Eq. 55)

    // Parameters
    // ----------
    // solar_time : ee.Image or ee.Number
    //     Solar time (i.e. noon is 0) [hours].

    // Returns
    // -------
    // omega : ee.Image or ee.Number
    //     Hour angle [radians].

    var omega = solar_time.multiply(2 * Math.PI / 24.0);

    // Need to adjust omega so that the values go from -pi to pi
    // Values outside this range are wrapped (i.e. -3*pi/2 -> pi/2)
    omega = _wrap(omega, -Math.PI, Math.PI);
    return omega;
}


function _wrap(x, x_min, x_max) {
    // Wrap floating point values into range

    // Parameters
    // ----------
    // x : ee.Image or ee.Number
    //     Values to wrap.
    // x_min : float
    //     Minimum value in output range.
    // x_max : float
    //     Maximum value in output range.

    // Returns
    // -------
    // ee.Image or ee.Number

    // Notes
    // -----
    // This formula is used to mimic the Python modulo operator.
    // Javascript/EE mod operator has the same sign as the dividend,
    //     so negative values stay negative.
    // Python mod operator has the same sign as the divisor,
    //     so negative values wrap to positive.

    var x_range = x_max - x_min;
    return x.subtract(x_min).mod(x_range).add(x_range).mod(x_range).add(x_min);
}


function _omega_sunset(lat, delta) {
    // Sunset hour angle (Eq. 59)

    // Parameters
    // ----------
    // lat : ee.Image or ee.Number
    //     Latitude [radians].
    // delta : ee.Image or ee.Number
    //     Earth declination [radians].

    // Returns
    // -------
    // ee.Image or ee.Number
    //     Sunset hour angle [radians].

    // Notes
    // -----
    // acos(-tan(lat) * tan(delta))

    return lat.tan().multiply(-1).multiply(delta.tan()).acos();
}


function _ra_daily(lat, doy, method) {
    // Daily extraterrestrial radiation (Eq. 21)

    // Parameters
    // ----------
    // lat : ee.Image or ee.Number
    //     latitude [radians].
    // doy : ee.Image or ee.Number
    //     Day of year.
    // method : {'asce' (default), 'refet'}, optional
    //     Calculation method:
    //     * 'asce' -- Calculations will follow ASCE-EWRI 2005 [1] equations.
    //     * 'refet' -- Calculations will follow RefET software.

    // Returns
    // -------
    // ra : ee.Image or ee.Number
    //     Daily extraterrestrial radiation [MJ m-2 d-1].

    // Notes
    // -----
    // Equation in ASCE-EWRI 2005 uses a solar varant of ~1366.666... W m-2
    // Equation in Duffie & Beckman (?) uses a solar varant of 1367 W m-2

    var delta = _delta(doy, method);
    var omegas = _omega_sunset(lat, delta);
    var theta = omegas.multiply(lat.sin()).multiply(delta.sin())
        .add(lat.cos().multiply(delta.cos()).multiply(omegas.sin()));

    var ra;
    if (method === 'asce') {
        ra = theta.multiply(_dr(doy)).multiply((24. / Math.PI) * 4.92);
    } else {
        ra = theta.multiply(_dr(doy)).multiply((24. / Math.PI) * (1367 * 0.0036));
    }
    return ra;
}


function _ra_hourly(lat, lon, doy, time_mid, method) {
    // Hourly extraterrestrial radiation (Eq. 48)

    // Parameters
    // ----------
    // lat : ee.Image or ee.Number
    //     Latitude [radians].
    // lon : ee.Image or ee.Number
    //     Longitude [radians].
    // doy : ee.Image or ee.Number
    //     Day of year.
    // time_mid : ee.Image or ee.Number
    //     UTC time at midpoint of period [hours].
    // method : {'asce' (default), 'refet'}, optional
    //     Calculation method:
    //     * 'asce' -- Calculations will follow ASCE-EWRI 2005 [1] equations.
    //     * 'refet' -- Calculations will follow RefET software.

    // Returns
    // -------
    // ra : ee.Image or ee.Number
    //     Hourly extraterrestrial radiation [MJ m-2 h-1].

    // Notes
    // -----
    // Equation in ASCE-EWRI 2005 uses a solar varant of ~1366.666... W m-2
    // Equation in Duffie & Beckman (?) uses a solar varant of 1367 W m-2
    if (method = "undefined") {
        method = 'asce'
    }
    var omega = _omega(_solar_time_rad(lon, time_mid, _seasonal_correction(doy)));
    var delta = _delta(doy, method);
    var omegas = _omega_sunset(lat, delta);

    // Solar time as start and end of period (Eqs. 53 & 54)
    // Modify omega1 and omega2 at sunrise and sunset (Eq. 56)
    var omega1 = omega.subtract(Math.PI / 24).max(omegas.multiply(-1)).min(omegas);
    var omega2 = omega.add(Math.PI / 24).max(omegas.multiply(-1)).min(omegas);
    omega1 = omega1.min(omega2);

    // Extraterrestrial radiation (Eq. 48)
    var theta = omega2.subtract(omega1).multiply(lat.sin()).multiply(delta.sin())
        .add(lat.cos().multiply(delta.cos()).multiply(omega2.sin().subtract(omega1.sin())));

    var ra;
    if (method === 'asce') {
        ra = theta.multiply(_dr(doy)).multiply((12. / Math.PI) * 4.92);
    } else {
        ra = theta.multiply(_dr(doy)).multiply((12. / Math.PI) * (1367 * 0.0036));
    }
    return ra;
}

function _rso_daily(ea, ra, pair, doy, lat) {
    // sin of the angle of the sun above the horizon (D.5 and Eq. 62)
    var sin_beta_24 = _doy_fraction(doy)
        .subtract(1.39)
        .sin()
        .multiply(lat)
        .multiply(0.3)
        .add(0.85)
        .subtract(lat.pow(2).multiply(0.42))
        .sin()
        .max(0.1);

    // Precipitable water
    var w = _precipitable_water(ea, pair);

    // Clearness index for direct beam radiation (Eq. D.2)
    // Limit sin_beta >= 0.01 so that KB does not go undefined
    var kb = w
        .divide(sin_beta_24)
        .pow(0.4)
        .multiply(-0.075)
        .add(pair.multiply(-0.00146).divide(sin_beta_24))
        .exp()
        .multiply(0.98);

    // Transmissivity index for diffuse radiation (Eq. D.4)
    var kd = kb.multiply(-0.36).add(0.35).min(kb.multiply(0.82).add(0.18));

    var rso = kb.add(kd).multiply(ra);
    return rso;
}

function _rso_hourly(ea, ra, pair, doy, time_mid, lat, lon, method) {
    if (method = "undefined") {
        method = 'asce'
    }
    var sc = _seasonal_correction(doy);
    var omega = _omega(_solar_time_rad(lon, time_mid, sc));

    // sin of the angle of the sun above the horizon (D.6 and Eq. 62)
    var delta = _delta(doy, method);
    var sin_beta = lat
        .sin()
        .multiply(delta.sin())
        .add(lat.cos().multiply(delta.cos()).multiply(omega.cos()));

    // Precipitable water
    var w = _precipitable_water(ea, pair);

    // Clearness index for direct beam radiation (Eq. D.2)
    // Limit sin_beta >= 0.01 so that KB does not go undefined
    var kt = 1.0;
    var kb = w
        .divide(sin_beta.max(0.01))
        .pow(0.4)
        .multiply(-0.075)
        .add(pair.multiply(-0.00146).divide(sin_beta.max(0.01).multiply(kt)))
        .exp()
        .multiply(0.98);

    // Transmissivity index for diffuse radiation (Eq. D.4)
    var kd = kb.multiply(-0.36).add(0.35).min(kb.multiply(0.82).add(0.18));

    var rso = kb.add(kd).multiply(ra);
    return rso;
}


function _rso_simple(ra, elev) {
    /*
    Simplified daily/hourly clear sky solar formulation (Eqs. 19 & 45)

    Parameters
    ----------
    ra : ee.Image or ee.Number
        Extraterrestrial radiation [MJ m-2 d-1 or MJ m-2 h-1].
    elev : ee.Image or ee.Number
        Elevation [m].

    Returns
    -------
    rso : ee.Image or ee.Number
        Clear sky solar radiation [MJ m-2 d-1 or MJ m-2 h-1].
        Output data type will match "ra" data type.

    Notes
    -----
    rso = (0.75 + 2E-5 * elev) * ra

    */
    return ra.multiply(elev.multiply(2E-5).add(0.75))
}


function _fcd_daily(rs, rso) {
    /*
    Daytime cloudiness fraction (Eq. 18)

    Parameters
    ----------
    rs : ee.Image or ee.Number
        Measured solar radiation [MJ m-2 d-1].
    rso : ee.Image or ee.Number
        Clear sky solar radiation [MJ m-2 d-1].

    Returns
    -------
    fcd : ee.Image or ee.Number
        Output data type will match "rs" data type.

    Notes
    -----
    fcd = 1.35 * min(max(rs / rso, 0.3), 1.0) - 0.35

    */
    return rs.divide(rso).max(0.3).min(1.0).multiply(1.35).subtract(0.35)
}


function _fcd_hourly(rs, rso, doy, time_mid, lat, lon, method) {
    /*
    Cloudiness fraction (Eq. 45)

    Parameters
    ----------
    rs : ee.Image or ee.Number
        Measured solar radiation [MJ m-2 h-1].
    rso : ee.Image or ee.Number
        Clear sky solar radiation [MJ m-2 h-1].
    doy : ee.Image or ee.Number
        Day of year.
    time_mid : ee.Image or ee.Number
        UTC time at midpoint of period [hours].
    lat : ee.Image or ee.Number
        Latitude [rad].
    lon : ee.Image or ee.Number
        Longitude [rad].
    method : {'asce' (default), 'refet'}, optional
        Calculation method:
        * 'asce' -- Calculations will follow ASCE-EWRI 2005 [1] equations.
        * 'refet' -- Calculations will follow RefET software.
        Passed through to declination calculation (_delta()).

    Returns
    -------
    fcd : ee.Image or ee.Number
        Output data type will match "rs" data type.

    */
    if (method = "undefined") {
        method = 'asce'
    }
    // DEADBEEF - These values are only needed for identifying low sun angles
    sc = _seasonal_correction(doy)
    delta = _delta(doy, method)
    omega = _omega(_solar_time_rad(lon, time_mid, sc))
    beta = lat.sin().multiply(delta.sin())
        .add(lat.cos().multiply(delta.cos()).multiply(omega.cos())).asin()

    fcd = rs.divide(rso).max(0.3).min(1).multiply(1.35).subtract(0.35)

    // Intentionally not using where() so that function will work with ee.Number
    fcd = fcd.max(beta.lt(0.3))

    return fcd
}


function _rnl_daily(tmax, tmin, ea, fcd) {
    /*
    Daily net long-wave radiation  (Eq. 17)

    Parameters
    ----------
    tmax : ee.Image or ee.Number
        Daily maximum air temperature [C].
    tmin : ee.Image or ee.Number
        Daily minimum air temperature [C].
    ea : ee.Image or ee.Number
        Actual vapor pressure [kPa].
    fcd : ee.Image or ee.Number
        cloudiness fraction.

    Returns
    -------
    ee.Image or ee.Number
        Daily net long-wave radiation [MJ m-2 d-1].
        Output data type will match "tmax" data type.

    Notes
    -----
    rnl = 4.901E-9 * fcd * (0.34 - 0.14 * sqrt(ea)) *
          0.5 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4))

    */
    return tmax.add(273.16).pow(4).add(tmin.add(273.16).pow(4)).multiply(0.5)
        .multiply(ea.sqrt().multiply(-0.14).add(0.34))
        .multiply(fcd).multiply(4.901E-9)
}


function _rnl_hourly(tmean, ea, fcd) {
    /*
    Hourly net long-wave radiation  (Eq. 44)

    Parameters
    ----------
    tmean : ee.Image or ee.Number
        Mean hourly air temperature [C].
    ea : ee.Image or ee.Number
        Actual vapor pressure [kPa].
    fcd : ee.Image or ee.Number
        Cloudiness fraction.

    Returns
    -------
    ee.Image or ee.Number
        Hourly net long-wave radiation [MJ m-2 h-1].
        Output data type will match "tmean" data type.

    Notes
    -----
    rnl = 2.042E-10 * fcd * (0.34 - 0.14 * sqrt(ea)) * ((tmean + 273.16) ** 4)

    */
    return tmean.add(273.16).pow(4)
        .multiply(ea.sqrt().multiply(-0.14).add(0.34))
        .multiply(fcd).multiply(2.042E-10)
}


function _rn(rs, rnl) {
    /*
    Net daily/hourly radiation (Eqs. 15 & 16)

    Parameters
    ----------
    rs : ee.Image or ee.Number
        Measured solar radiation [MJ m-2 d-1 or MJ m-2 h-1].
    rnl : ee.Image or ee.Number
        Hourly net long-wave radiation [MJ m-2 d-1 or MJ m-2 h-1].

    Returns
    -------
    ee.Image or ee.Number
        Hourly net long-wave radiation [MJ m-2 d-1 or MJ m-2 h-1].
        Output data type will match "rnl" data type.

    Notes
    -----
    Switching calculation to work from rnl (which is computed from temperature)
    rnl = 0.77 * rs - rnl

    */
    return rnl.multiply(-1).add(rs.multiply(0.77))
}



function _wind_height_adjust(uz, zw) {
    /*
    Wind speed at 2 m height based on full logarithmic profile (Eq. 33)

    Parameters
    ----------
    uz : ee.Image or ee.Number
        Wind speed at measurement height [m s-1].
    zw : ee.Image or ee.Number
        Wind measurement height [m].

    Returns
    -------
    ee.Image or ee.Number
        Wind speed at 2 m height [m s-1].

    Notes
    -----
    u2 = uz * 4.87 / log(67.8 * zw - 5.42)

    */
    return uz.multiply(4.87).divide(zw.multiply(67.8).subtract(5.42).log())
}

exports.make_calcs = function () {
    return {
        air_pressure: _air_pressure,
        sat_vapor_pressure: _sat_vapor_pressure,
        es_slope: _es_slope,
        actual_vapor_pressure: _actual_vapor_pressure,
        specific_humidity: _specific_humidity,
        vpd: _vpd,
        precipitable_water: _precipitable_water,
        doy_fraction: _doy_fraction,
        delta: _delta,
        dr: _dr,
        seasonal_correction: _seasonal_correction,
        solar_time_rad: _solar_time_rad,
        omega: _omega,
        omega_sunset: _omega_sunset,
        ra_daily: _ra_daily,
        ra_hourly: _ra_hourly,
        rso_daily: _rso_daily,
        rso_hourly: _rso_hourly,
        rso_simple: _rso_simple,
        fcd_daily: _fcd_daily,
        fcd_hourly: _fcd_hourly,
        rnl_daily: _rnl_daily,
        rnl_hourly: _rnl_hourly,
        rn: _rn,
        wind_height_adjust: _wind_height_adjust
    }
}
