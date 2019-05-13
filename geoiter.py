from PIL import Image
import requests
from io import BytesIO
import math

class geoiter:
    
    def __init__(self, bounds, resolution, zoom = None):

        # verify if the geoinformation is valid
        if abs(bounds[0]) >= 90 or abs(bounds[2]) >= 90:
            raise Exception("Latitude bigger than 90 or smaller than -90")
        elif abs(bounds[1]) >= 180 or abs(bounds[3]) >= 180:
            raise Exception("Longitude bigger than 180 or smaller than -180")

        self.bound = bounds

        # verify if the resolutions are valid
        if resolution[0] < 0 or resolution[1] < 0:
            raise Exception("Resolution smaller than zero")

        self.resolution = resolution

        # when zoom level is not provided, the algorithm will calculate the minimum zoom level needed
        if zoom is None:
            self.zoom = self._minimum_zoom(bounds, resolution)
        elif zoom < 0 or zoom > 19:
            raise Exception("Zoom level bigger than 19 or smaller than 0")
        else:
            self.zoom = zoom

        # pre-compute the locations of each image
        self.pre_computed_imgs = self._map_tiler(bounds[0], bounds[1], bounds[2], bounds[3], self.zoom, resolution)
        
    def __iter__(self):

        # initialize the iterator
        self.count = 0
        return self
    
    def __next__(self):
        if self.count < len(self.pre_computed_imgs):
            current_block = self.pre_computed_imgs[self.count]

            # fetch the image with precomputed tile and crop information
            img = self._img_with_given_resolution(current_block[0], current_block[1], self.zoom)
            self.count += 1
            
            return img
        else:
            raise StopIteration
        
    # convert from lat/lng to tiles
    def _geo_converter(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)
        
    # check if images with the resolution could be processed under given boundary and zoom level
    def _check_resolution(self, xtile1, ytile1, xtile2, ytile2, zoom, resolution):
    
        len_x = (abs(xtile1 - xtile2) + 1) * 256
        len_y = (abs(ytile1 - ytile2) + 1) * 256

        if len_x == 0 or len_y == 0:
            raise Exception("Unable to meet the set resolution requirement with given zoom level. Please increase your zoom level")

        multiplier_x = len_x / resolution[0]
        multiplier_y = len_y / resolution[1]

        if multiplier_x < 1 or multiplier_y < 1:
            multiplier = math.ceil(math.log(1 / min(multiplier_x, multiplier_y), 2)) + 1
            raise Exception("Unable to meet the set resolution requirement with given zoom level. Recommended Minimum Zoom Level: %s" % (zoom + multiplier))

        return math.floor(multiplier_x), math.floor(multiplier_y)

    # return the minimum zoom level required to satisfy the given resolution
    def _minimum_zoom(self, boundary, resolution):

        for i in range(20):

            xtile1, ytile1 = self._geo_converter(boundary[0], boundary[1], i)
            xtile2, ytile2 = self._geo_converter(boundary[2], boundary[3], i)

            x = abs(xtile2 - xtile1) * 256
            y = abs(ytile2 - ytile1) * 256

            if x > resolution[0] and y > resolution[1]:
                return i
    
        raise Exception("Impossible to return an image with given resolution under the defined boundary.")
    
    # find the tiles that 'wrap' the image and how to crop it to get the image
    def _find_tile(self, top_left, bottom_right, outer_top_left, outer_bottom_right):
    
        # x, y refers to the resolution of the image
        x = bottom_right[0] - top_left[0]
        y = bottom_right[1] - top_left[1]

        # find the distance of current images' top left corner to the boundary's top left corner
        # the result is in the unit of tiles
        distance_from_top_x = top_left[0] // 256
        distance_from_top_y = top_left[1] // 256

        # find the distance of current images' bottom right corner to the boundary's bottom_right corner
        # the result is in the unit of tiles
        distance_from_bottom_x = outer_bottom_right[0] - math.ceil(bottom_right[0] / 256) + 1
        distance_from_bottom_y = outer_bottom_right[1] - math.ceil(bottom_right[1] / 256) + 1

        tiles = (outer_top_left[0] + distance_from_top_x, outer_top_left[1] + distance_from_top_y, 
                 outer_bottom_right[0] - distance_from_bottom_x, outer_bottom_right[1] - distance_from_bottom_y)

        crop = (top_left[0] - distance_from_top_x * 256, top_left[1] - distance_from_top_y * 256, 
                top_left[0] - distance_from_top_x * 256 + x, top_left[1] - distance_from_top_y * 256 + y)

        return tiles, crop
    
    # core function that returns the pre-computed information of each image
    def _map_tiler(self, lat1, lng1, lat2, lng2, zoom, resolution):
    
        # gets the boundary within tile system
        xtile1, ytile1 = self._geo_converter(lat1, lng1, zoom)
        xtile2, ytile2 = self._geo_converter(lat2, lng2, zoom)
        
        # checks whehter the xtile and ytile is correct
        self._check_tile_convertion_integrity(xtile1, ytile1, zoom)
        self._check_tile_convertion_integrity(xtile2, ytile2, zoom)

        # mp_x represents how many pieces of the image will be on the x-axis
        # mp_y represents how many pieces of the image will be on the y-axis
        # the total number of images returned is mp_x * mp_y
        mp_x, mp_y = self._check_resolution(xtile1, ytile1, xtile2, ytile2, zoom, resolution)

        # upper_left represents the top left corner of the boundary
        # bottom_right represents the bottom right corner of the boundary
        upper_left = (min(xtile1, xtile2), min(ytile1, ytile2))
        bottom_right = (max(xtile1, xtile2), max(ytile1, ytile2))

        # temp_upper represents the top_left corner of an instance of the image within the boundary
        # in the algorithm, cutting starts from top_left corner. Therefore, the relative position of
        # the first image is [0, 0]. Notice that the unit is in pixels rather than tile
        temp_upper = [0, 0]
        temp_bottom = [resolution[0], resolution[1]]
        pre_computed_imgs = []

        # the for loop iterates through every image that is going to be returned
        for i in range(mp_x):

            temp_upper[1] = 0
            temp_bottom[1] = resolution[1]

            for t in range(mp_y):

                # the _find_tile function returns two important results:
                # 'tiles' refers to the tiles that "wrap" the image in
                # 'crop' refers to the how the tiles should be cropped in order to get the resulting image 
                tiles, crop = self._find_tile(temp_upper, temp_bottom, upper_left, bottom_right)
                pre_computed_imgs.append([tiles, crop])

                # the relative position of the image moves downwards for the next image
                temp_upper[1] += resolution[1]
                temp_bottom[1] += resolution[1]

            # the relative position of the image moves leftwards for the next image
            temp_upper[0] += resolution[0]
            temp_bottom[0] += resolution[0]

        return pre_computed_imgs
    
    # return the image with pre-computed information
    def _img_with_given_resolution(self, tiles, crop, zoom):
    
        responses = []

        # fetch all the tiles necessary to crop the image
        for i in range(tiles[0], tiles[2] + 1):
            for t in range(tiles[1], tiles[3] + 1):
                responses.append(requests.get('https://a.tiles.mapbox.com/v3/nickponline.g7642h2a/%s/%s/%s.png' % (zoom, i, t)))

        imgs = [Image.open(BytesIO(temp.content)) for temp in responses]

        print("Finished fetching %s images..." % len(imgs))

        total_width = (tiles[2] - tiles[0] + 1) * 256
        total_height = (tiles[3] - tiles[1] + 1) * 256

        new_im = Image.new('RGB', (total_width, total_height))

        x_offset = 0
        y_offset = 0
        count = 0

        # first assemble all the tiles
        for i in range(tiles[2] - tiles[0] + 1):
            for t in range(tiles[3] - tiles[1] + 1):
                new_im.paste(imgs[count], (x_offset, y_offset))
                y_offset += 256
                count += 1
            y_offset = 0
            x_offset += 256

        # crop the image
        new_im = new_im.crop(crop)

        return new_im
    
    # check if the tile information is valid
    def _check_tile_convertion_integrity(self, xtile, ytile, zoom):
        
        tile_size = 2 ** zoom - 1
        
        if xtile > tile_size or xtile < 0 or ytile > tile_size or ytile < 0:
            raise Exception("Tile convertion error. Please refer to https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Zoom_levels for proper lat/lng range with given zoom level")
        