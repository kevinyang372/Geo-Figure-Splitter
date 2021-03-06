# Geoiter

Geoiter is a python library that yields a sequence of images that tiles given geographic bounds with a specific resolution and zoom level. All the images returned in the library is built upon [the OpenStreetMap standard tile server database](https://wiki.openstreetmap.org/wiki/Slippy_Map)

## Setup

Geoiter is built under python3. All the dependencies could be installed by:
```bash
pip install -r requirements.txt
```
Run all the unit test to see if the library is performing correctly by:
```bash
python -m unittest discover -v
```

## Example Usage

Geoiter is a python iterator object which continues generating images until it finished tiling the entire boundary
```python
from geoiter import geoiter

bounds = (31.2304, 121.4737, 35.6762, 139.6503)
resolution = (640, 480)
zoom = 8

for image in geoiter(bounds, resolution, zoom):
    print(image)
```

## Documentation

Geoiter accepts four parameters as the input to the iterator
* __bounds__: a pair of latitude and longitudes - `format: (lat1, lng1, lat2, lng2)`


* __resolution__: the resolution of the output image in pixels - `format: (resolution_x, resolution_y)`


* __zoom__ (optional): an integer referring to the zoom level of the output image (when it is not provided, the algorithm will automatically compute and use the minimum zoom level necessary)

* __include_boundary__ (optional): a boolean variable flagging whether to include the boundary or not. When __include_boundary__ is set to False, the images produced may not capture the boundaries set as the leftover space is too small. When __include_boundary__ is set to True, the images produced will capture the entire area within boundaries but may go overbound. (default: False)

## Basic Ideas

### Map Tiling

The OpenStreetMap standard tile server relies on three distinct parameters to return an image: zoom level, xtile and ytile. Each image returned will all be the same size of 256 * 256.

At zoom level 0, the entire world map will be presented with only one [image](https://a.tiles.mapbox.com/v3/nickponline.g7642h2a/0/0/0.png)

As zoom level increases, a smaller area of the map will be returned. In exchange, it will also contain more detail as the resolution remains unchanged. The exact relationship between zoom level and presented area size is described as below:

__Assume at zoom level n, the area presented with one tile is A(n). Then at zoom level (n + 1), the area presented will be A(n + 1) = A(n) / 4__

Therefore, with a maximum zoom level of 19, the entire map will consist of 2^38 (approximately 275 billion) numbers of tiles

### Xtile and Ytile

As described in the section above, each tile is also distinguished by a (xtile, ytile) geolocation pair. The top left corner is always (0, 0). The value of xtile increases horizontally while the value of ytile increases vertically.

For example, at zoom level 1, the world map is divided into four areas with:
* Top-left corner: 1/0/0 (zoom level: 1, xtile: 0, ytile: 0)
* Top-right corner: 1/1/0 (zoom level: 1, xtile: 1, ytile: 0)
* Bottom-left corner: 1/0/1 (zoom level: 1, xtile: 0, ytile: 1)
* Bottom-right corner: 1/1/1 (zoom level: 1, xtile: 1, ytile: 1)

### Geographic Boundary

The geographic boundary is defined by two pairs of latitude and longitude (lat1, lng1, lat2, lng2).

Under the map tiling system, with the given zoom level, it could be transformed into (xtile1, ytile1, xtile2, ytile2)

Since each tile has the size of 256 * 256, the boundary could be represented with a width of `abs(xtile1 - xtile2) * 256` and a height of `abs(ytile1 - ytile2) * 256`

> _Notice that if either `abs(xtile1 - xtile2) * 256` is smaller than the resolution width or `abs(ytile1 - ytile2) * 256` is smaller than the resolution height. This will trigger an Exception returned by the iterator_

Mathematically, if the resolution is defined by (a0, a1), the geographic boundary could be divided into
* `abs(xtile1 - xtile2) * 256 // a0` in x-axis
* `abs(ytile1 - ytile2) * 256 // a1` in y-axis

### Assembling and Cropping

Knowing how many images could be produced within the geographic boundary, the algorithm then computes the tiles that 'wrap' each image, assembles them together and then crops the desired image out.
