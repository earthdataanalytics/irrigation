import ee
def prepSrLandsat8(image):
    """A function that scales and masks Landsat (C2) surface reflectance images.

    Args:
      image: An Earth Engine Landsat 8 surface reflectance image.

    Returns:
      An Earth Engine Landsat surface reflectance image with scaled and masked bands.
    """

    # Develop masks for unwanted pixels (fill, cloud, cloud shadow).
    qaMask = image.select("QA_PIXEL").bitwiseAnd(int("11111", 2)).eq(0)
    saturationMask = image.select("QA_RADSAT").eq(0)

    # Apply the scaling factors to the appropriate bands.
    def getFactorImg(factorNames):
        """Gets a list of scaling factors as an Earth Engine Image."""
        factorList = image.toDictionary().select(factorNames).values()
        return ee.Image.constant(factorList)

    scaleImg = getFactorImg(["REFLECTANCE_MULT_BAND_.|TEMPERATURE_MULT_BAND_ST_B10"])
    offsetImg = getFactorImg(["REFLECTANCE_ADD_BAND_.|TEMPERATURE_ADD_BAND_ST_B10"])
    scaled = image.select("SR_B.|ST_B10").multiply(scaleImg).add(offsetImg)

    # Replace original bands with scaled bands and apply masks.
    return (
        image.addBands(scaled, None, True).updateMask(qaMask).updateMask(saturationMask)
    )

def prepSrLandsat5and7(image):
  """Masks Landsat 4 and 5 SR images.

  Args:
    image: An ee.Image object.

  Returns:
    An ee.Image object with the masks applied.
  """

  # Bit 0 - Fill
  # Bit 1 - Dilated Cloud
  # Bit 2 - Unused
  # Bit 3 - Cloud
  # Bit 4 - Cloud Shadow
  qa_mask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
  saturation_mask = image.select('QA_RADSAT').eq(0)

  # Apply the scaling factors to the appropriate bands.
  optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermal_band = image.select('ST_B6').multiply(0.00341802).add(149.0)

  # Replace the original bands with the scaled ones and apply the masks.
  return image.addBands(optical_bands, None, True) \
      .addBands(thermal_band, None, True) \
      .updateMask(qa_mask) \
      .updateMask(saturation_mask)