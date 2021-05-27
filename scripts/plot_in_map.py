import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import sys
import json
import os

args = sys.argv[1:]
if len(args) != 3:
    sys.exit('usage: python3 ploy_in_map.py <path_to_graph_file> <output_file> '
             '<fallback')

graph_path = os.path.expanduser(args[0])
output_path = os.path.expanduser(args[1])
fallback = args[2]

with open(graph_path) as f:
    data = json.load(f)
    locations = data["locations"]["nodes"]

UNDEFINED = -1000
lowest_lat = UNDEFINED
highest_lat = UNDEFINED
lowest_lng = UNDEFINED
highest_lng = UNDEFINED

count = 0
for loc in locations.values():
    count += 1
    lat, lng = loc["lat"], loc["lng"]
    if lat < lowest_lat or lowest_lat == UNDEFINED:
        lowest_lat = lat
    if lat > highest_lat or highest_lat == UNDEFINED:
        highest_lat = lat
    if lng < lowest_lng or lowest_lng == UNDEFINED:
        lowest_lng = lng
    if lng > highest_lng or highest_lng == UNDEFINED:
        highest_lng = lng

print(f'Number of nodes: {count}')

border = 5
fallback_color = 'red'
other_color = 'black'

plt.figure(figsize=(30, 15))
m = Basemap(projection='merc', llcrnrlat=lowest_lat-border,
            urcrnrlat=highest_lat+border, llcrnrlon=lowest_lng-border,
            urcrnrlon=highest_lng+border, resolution='h', fix_aspect=True)

for node, loc in locations.items():
    lat, lng = loc["lat"], loc["lng"]
    if node == fallback:
        color = fallback_color
    else:
        color = other_color
    m.plot(lng, lat, latlon=True, marker='o', color=color, markersize=20)

m.drawcountries()
m.fillcontinents()
plt.axis('off')
plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
