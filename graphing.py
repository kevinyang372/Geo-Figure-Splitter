import geo_converter
import math

def graphing(lat1, lng1, lat2, lng2, zoom, resolution):

    len_x = round(abs(lng2 - lng1), 2)
    len_y = round(abs(lat2 - lat1), 2)

    increment_x, increment_y = lcm(len_x, len_y, resolution)

    return increment_x, increment_y


def lcm(len_x, len_y, resolution):

    por1 = int(len_x * 100) * resolution[1]
    por2 = int(len_y * 100) * resolution[0]

    dv = math.gcd(por1, por2)

    n = por1 // dv
    m = por2 // dv

    increment_x = len_x / n
    increment_y = len_y / m

    return increment_x, increment_y