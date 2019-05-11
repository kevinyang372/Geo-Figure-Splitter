from geoiter import geoiter

bounds = (31.2304, 121.4737, 35.6762, 139.6503)
resolution = (640, 480)
zoom = 8

for image in geoiter(bounds, resolution, zoom):
    print(image)