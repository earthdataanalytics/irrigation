import unittest
import datetime
import ee

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

class TestUtils(unittest.TestCase):

    def test_getinfo(self):
        self.assertEqual(utils.getinfo(ee.Number(1)), 1)

    def test_getinfo_exception(self):
        with self.assertRaises(Exception):
            utils.getinfo('deadbeef')

    # CGM - Not sure how to trigger an EEException to test that the output is None
    # This fails before it is sent to the getinfo function
    # def test_getinfo_eeexception(self):
    #     self.assertIsNone(utils.getinfo(ee.Number('deadbeef')))

    def test_constant_image_value(self):
        tol = 0.000001
        expected = 10.123456789
        input_img = ee.Image.constant(expected)
        output = utils.constant_image_value(input_img)
        self.assertLessEqual(abs(output['constant'] - expected), tol)

    def test_point_image_value(self):
        tol = 0.001
        expected = 2364.351
        output = utils.point_image_value(ee.Image('USGS/NED'), [-106.03249, 37.17777])
        self.assertLessEqual(abs(output['elevation'] - expected), tol)

    def test_point_coll_value(self):
        tol = 0.001
        expected = 2364.351
        output = utils.point_coll_value(
            ee.ImageCollection([ee.Image('USGS/NED')]), [-106.03249, 37.17777])
        self.assertLessEqual(abs(output['elevation']['2012-04-04'] - expected), tol)

    def test_c_to_k(self):
        c = 20
        k = 293.15
        tol = 0.000001
        
        output = utils.constant_image_value(utils.c_to_k(ee.Image([c])))
        self.assertLessEqual(abs(output['constant'] - k), tol)

    @unittest.expectedFailure
    @unittest.skip("Optional reason for skipping")
    def test_date_to_time_0utc(self):
        input = '2015-07-13T18:33:39'
        expected = 1436745600000
        input_img = ee.Date(input)
        self.assertEqual(utils.getinfo(utils.date_to_time_0utc(input_img)), expected)

    @unittest.expectedFailure
    @unittest.skip("Optional reason for skipping")
    def test_is_number(self):
        inputs = [300, '300', 300.25, '300.25', 'a']
        expected = [True, True, True, True, False]
        for input_val, expected_val in zip(inputs, expected):
            self.assertEqual(utils.is_number(input_val), expected_val)

    def test_millis(self):
        self.assertEqual(utils.millis(datetime.datetime(2015, 7, 13)), 1436745600000)

    def test_valid_date(self):
        self.assertTrue(utils.valid_date('2015-07-13'))
        self.assertFalse(utils.valid_date('2015-02-30'))
        self.assertFalse(utils.valid_date('20150713'))
        self.assertFalse(utils.valid_date('07/13/2015'))
        self.assertTrue(utils.valid_date('07-13-2015', '%m-%d-%Y'))

if __name__ == '__main__':
    unittest.main()
