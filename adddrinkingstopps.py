import overpy
import xml.etree.ElementTree as ET
import geopy.distance


# GPX-Datei laden und Track-Punkte extrahieren
gpx_file_path = 'dein_gpx_track.gpx'
tree = ET.parse(gpx_file_path)
root = tree.getroot()

ns = {'default': 'http://www.topografix.com/GPX/1/1'}

track_points = []
s=200
n=-200
w=200
e=-200
for trkpt in root.findall('.//default:trkpt', ns):
    lat = float(trkpt.get('lat'))
    lon = float(trkpt.get('lon'))
    track_points.append((lat, lon))
    if (lat<s): s=lat
    if (lat>n): n=lat
    if (lon<w): w=lon
    if (lon>e): e=lon

# OSM Overpass API initialisieren
api = overpy.Overpass()

# Funktion, um relevante Orte in der Nähe eines Punkts zu finden
def find_bbox_amenities(s,w,n,e):
    query = f"""
    [out:json];
    (
      node["amenity"="drinking_water"]({s},{w},{n},{e});
      node["amenity"="fuel"]({s},{w},{n},{e});
      node["amenity"="kiosk"]({s},{w},{n},{e});
      node["shop"="supermarket"]({s},{w},{n},{e});
    );
    out center;
    """
    result = api.query(query)
    return result.nodes

# Funktion, um relevante Orte in der Nähe eines Punkts zu finden
def find_nearby_amenities(lat, lon, radius=1000):
    query = f"""
    [out:json];
    (
      node["amenity"="drinking_water"](around:{radius},{lat},{lon});
      node["amenity"="fuel"](around:{radius},{lat},{lon});
      node["amenity"="kiosk"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
    );
    out center;
    """
    result = api.query(query)
    return result.nodes

all_amenities = find_bbox_amenities(s,w,n,e)
def unique_waypoints(track_points, waypoints, radius):
# Wegpunkte sammeln
    print('Suche im '+str(radius)+' Radius')
    i = 0
    for lat, lon in track_points:
        for node in all_amenities:
            if (geopy.distance.geodesic((lat,lon), (node.lat,node.lon)).km<1):
                waypoint = {
                    'name': node.tags.get('name', 'Unknown'),
                    'lat': node.lat,
                    'lon': node.lon,
                    'type': node.tags.get('amenity', node.tags.get('shop', 'Unknown'))
                }
                if (waypoint not in waypoints):
                    waypoints.append(waypoint)
                    print('Watt gefunden für Trackpoint '+str(i)+' ' + waypoint['name'] +'\n')
        i += 1
    return waypoints

def max_waypoint_dist(waypoints):
    maxdist=0
    prev_wp=None
    for wp in waypoints:
        if (prev_wp):
            if (geopy.distance.geodesic( (wp['lat'], wp['lon']), (prev_wp['lat'], prev_wp['lon']) ).km>maxdist): 
                maxdist = geopy.distance.geodesic((wp['lat'],wp['lon']), (prev_wp['lat'],prev_wp['lon'])).km
        prev_wp=wp
    return maxdist

waypoints = []
waypoints = unique_waypoints(track_points, waypoints, 1.0)
if (max_waypoint_dist(waypoints)>10):
    waypoints = unique_waypoints(track_points, waypoints, 2.0)
if (max_waypoint_dist(waypoints)>15):
    waypoints = unique_waypoints(track_points, waypoints, 3.0)
if (max_waypoint_dist(waypoints)>20):
    waypoints = unique_waypoints(track_points, waypoints, 4.0)
if (max_waypoint_dist(waypoints)>25):
    waypoints = unique_waypoints(track_points, waypoints, 5.0)

# GPX Namespace
gpx_ns = 'http://www.topografix.com/GPX/1/1'
ET.register_namespace('', gpx_ns)

# Neue GPX-Struktur mit Namespace erstellen
#gpx = ET.Element(f'{{{gpx_ns}}}gpx', version="1.1", creator="Python Script")
gpx = root

# Wegpunkte in das GPX-Dokument einfügen
for waypoint in waypoints:
    wpt = ET.Element(f'{{{gpx_ns}}}wpt', lat=str(waypoint['lat']), lon=str(waypoint['lon']))
    ET.SubElement(wpt, f'{{{gpx_ns}}}name').text = f"{waypoint['type']}: {waypoint['name']}"
    gpx.insert(1, wpt) # garmin basecamp will die waypoints vor den trackdaten

# Neue GPX-Datei speichern
new_gpx_file = 'updated_track_with_waypoints.gpx'
# tree = ET.ElementTree(gpx)
tree.write(new_gpx_file, encoding="UTF-8", xml_declaration=True)

print(f"Wegpunkte wurden in {new_gpx_file} gespeichert.")
