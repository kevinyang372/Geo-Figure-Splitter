import unittest
from geoiter import geoiter

class GeoiterTestCase(unittest.TestCase):

    # test resolution higher than 256 * 256
    def test_256_300(self):
        bounds = (80, 170, -80, -170)
        resolution = (256, 300)
        zoom = 1

        test = geoiter(bounds, resolution, zoom)

        self.assertEqual(len(test.pre_computed_imgs), 2)

    # test resolution lower than 256 * 256
    def test_60_40(self):
        bounds = (80, 170, -80, -170)
        resolution = (60, 40)
        zoom = 1

        test = geoiter(bounds, resolution, zoom)

        self.assertEqual(len(test.pre_computed_imgs), 96)

    # test if invalid lat/lng is correctly captured
    def test_lat_lng_exception(self):
        bounds = (90, 180, -90, -180)
        resolution = (60, 40)
        zoom = 1

        with self.assertRaises(Exception) as context:
            geoiter(bounds, resolution, zoom)

        self.assertTrue("Latitude bigger than 90 or smaller than -90" in str(context.exception))

    # test if resolution too high under current boundary and zoom level is correctly captured
    def test_resolution_exception(self):
        bounds = (80, 170, -80, -170)
        resolution = (1280, 720)
        zoom = 1

        with self.assertRaises(Exception) as context:
            geoiter(bounds, resolution, zoom)

        self.assertTrue("Unable to meet the set resolution requirement" in str(context.exception))

    # test if invalid zoom level is correctly captured
    def test_zoom_exception(self):
        bounds = (80, 170, -80, -170)
        resolution = (60, 40)
        zoom = 20

        with self.assertRaises(Exception) as context:
            geoiter(bounds, resolution, zoom)

        self.assertTrue("Zoom level bigger than 19 or smaller than 0" in str(context.exception))

    # test automatic calculation of the minimum zoom level
    def test_without_zoom(self):
        bounds = (80, 170, -80, -170)
        resolution = (60, 40)

        test = geoiter(bounds, resolution)

        self.assertEqual(len(test.pre_computed_imgs), 96)

    # test if resolution too higher under current boundary is correctly captured
    def test_without_zoom_exception(self):
        bounds = (31.2304, 121.4737, 31.2305, 121.4738)
        resolution = (1280, 760)

        with self.assertRaises(Exception) as context:
            geoiter(bounds, resolution)

        self.assertTrue("Impossible to return an image with given resolution under the defined boundary" in str(context.exception))

if __name__ == '__main__':
    unittest.main()