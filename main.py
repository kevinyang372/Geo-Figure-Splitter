from geo_converter import geo_converter
import matplotlib.pyplot as plt
from PIL import Image
import requests
from io import BytesIO
import math

def new_display(xtile, ytile, increase_zoom):
    
    temp = [[xtile*2, ytile*2], [xtile*2, ytile*2 + 1], [xtile*2 + 1, ytile*2], [xtile*2 + 1, ytile*2 + 1]]
    
    if increase_zoom == 1:
        return temp
    
    result = []
    for i in temp:
        result += new_display(i[0], i[1], increase_zoom - 1)
        
    return result

def display_with_given_resolution(lat, lng, zoom, resolution):
    
    xtile, ytile = geo_converter(lat, lng, zoom)
    origin_response = requests.get('https://a.tiles.mapbox.com/v3/nickponline.g7642h2a/%s/%s/%s.png' % (zoom, xtile, ytile))
    origin_img = Image.open(BytesIO(origin_response.content))
    
    multiplier = (max(resolution) - 1) // 256
    
    new_tiles = sorted(new_display(xtile, ytile, multiplier))
    print("Using %s tiles to compile the image" % len(new_tiles))
    
    new_zoom = zoom + multiplier
    print("The new zoom level is %s" % new_zoom)
    
    response = [requests.get('https://a.tiles.mapbox.com/v3/nickponline.g7642h2a/%s/%s/%s.png' % (new_zoom, i[0], i[1])) for i in new_tiles]
    imgs = [Image.open(BytesIO(temp.content)) for temp in response]
    
    print("Finished fetching images...")
    
    total_length = 256 * (multiplier * 2)
    new_im = Image.new('RGB', (total_length, total_length))
    
    x_offset = -256
    y_offset = 0
    count = 0
    
    for i in range(multiplier * 2):
        y_offset = 0
        x_offset += 256
        for t in range(multiplier * 2):
            new_im.paste(imgs[count], (x_offset, y_offset))
            y_offset += 256
            count += 1
    
    left = (new_im.size[0] - resolution[0])/2
    top = (new_im.size[1] - resolution[1])/2
    right = (new_im.size[0] + resolution[0])/2
    bottom = (new_im.size[1] + resolution[1])/2
    
    new_im = new_im.crop((left, top, right, bottom))
    
    return origin_img, new_im