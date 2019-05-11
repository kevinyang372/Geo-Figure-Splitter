import matplotlib.pyplot as plt
from PIL import Image
import requests
from io import BytesIO
import math

class geoiter:
    
    def __init__(self, bounds, resolution, zoom):
        self.bound = bounds
        self.resolution = resolution
        self.zoom = zoom
        
        # pre-compute the locations of each image
        self.pre_computed_imgs = self._map_tiler(bounds[0], bounds[1], bounds[2], bounds[3], zoom, resolution)
        
    def __iter__(self):

        # initialize the iterator
        self.count = 0
        return self
    
    def __next__(self):

        if self.count < len(self.pre_computed_imgs):
            current_block = self.pre_computed_imgs[self.count]

            # return the image with the pre-computed location
            img = self._img_with_given_resolution(current_block[0], current_block[1], self.zoom)
            self.count += 1
            
            return img
        else:
            raise StopIteration
        
    # convert lat/lng to tiles
    def _geo_converter(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)
        
    # check whether the current resolution could be met    
    def _check_resolution(self, xtile1, ytile1, xtile2, ytile2, zoom, resolution):
    
        len_x = abs(xtile1 - xtile2) * 256
        len_y = abs(ytile1 - ytile2) * 256

        if len_x == 0 or len_y == 0:
            raise Exception("Unable to meet the set resolution requirement with given zoom level. Please increase your zoom level")

        multiplier_x = len_x / resolution[0]
        multiplier_y = len_y / resolution[1]

        if multiplier_x < 1 or multiplier_y < 1:
            multiplier = math.ceil(math.log(1 / min(multiplier_x, multiplier_y), 2)) + 1
            raise Exception("Unable to meet the set resolution requirement with given zoom level. Recommended Minimum Zoom Level: %s" % (zoom + multiplier))

        return math.floor(multiplier_x), math.floor(multiplier_y)
    
    # find the tiles and crop location of a given image
    def _find_tile(self, top_left, bottom_right, outer_top_left):
    
        x = bottom_right[0] - top_left[0]
        y = bottom_right[1] - top_left[1]

        distance_from_top_x = top_left[0] // 256
        distance_from_top_y = top_left[1] // 256

        distance_from_bottom_x = bottom_right[0] // 256 + 1
        distance_from_bottom_y = bottom_right[1] // 256 + 1

        tiles = (outer_top_left[0] + distance_from_top_x, outer_top_left[1] - distance_from_top_y, 
                 outer_top_left[0] + distance_from_bottom_x, outer_top_left[1] - distance_from_bottom_y)

        crop = (top_left[0] - distance_from_top_x * 256, top_left[1] - distance_from_top_y * 256, 
                top_left[0] - distance_from_top_x * 256 + x, top_left[1] - distance_from_top_y * 256 + y)

        return tiles, crop
    
    # compute the tile location for each image
    def _map_tiler(self, lat1, lng1, lat2, lng2, zoom, resolution):
    
        xtile1, ytile1 = self._geo_converter(lat1, lng1, zoom)
        xtile2, ytile2 = self._geo_converter(lat2, lng2, zoom)

        mp_x, mp_y = self._check_resolution(xtile1, ytile1, xtile2, ytile2, zoom, resolution)

        upper_left = (min(xtile1, xtile2), max(ytile1, ytile2))

        temp_upper = [0, 0]
        temp_bottom = [resolution[0], resolution[1]]
        pre_computed_imgs = []

        for i in range(mp_x):

            temp_upper[1] = 0
            temp_bottom[1] = resolution[1]

            for t in range(mp_y):
                tiles, crop = self._find_tile(temp_upper, temp_bottom, upper_left)
                pre_computed_imgs.append([tiles, crop]) 

                temp_upper[1] += resolution[1]
                temp_bottom[1] += resolution[1]

            temp_upper[0] += resolution[0]
            temp_bottom[0] += resolution[0]

        return pre_computed_imgs
    
    # return an image with the given tile location
    def _img_with_given_resolution(self, tiles, crop, zoom):
    
        responses = []

        for i in range(tiles[0], tiles[2] + 1):
            for t in range(tiles[3], tiles[1] + 1):
                responses.append(requests.get('https://a.tiles.mapbox.com/v3/nickponline.g7642h2a/%s/%s/%s.png' % (zoom, i, t)))

        imgs = [Image.open(BytesIO(temp.content)) for temp in responses]

        print("Finished fetching %s images..." % len(imgs))

        total_width = (tiles[2] - tiles[0] + 1) * 256
        total_height = (tiles[1] - tiles[3] + 1) * 256

        new_im = Image.new('RGB', (total_width, total_height))

        x_offset = 0
        y_offset = 0
        count = 0

        for i in range(tiles[2] - tiles[0] + 1):
            for t in range(tiles[1] - tiles[3] + 1):
                new_im.paste(imgs[count], (x_offset, y_offset))
                y_offset += 256
                count += 1
            y_offset = 0
            x_offset += 256

        new_im = new_im.crop(crop)

        return new_im