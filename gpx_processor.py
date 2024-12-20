# ... (keep all your imports) ...
import overpy
import xml.etree.ElementTree as ET
import geopy.distance
    
# Funktion, um relevante Orte in der Nähe eines Punkts zu finden
def find_bbox_amenities(api, s,w,n,e):
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

def unique_waypoints(amenities, track_points, waypoints, radius):
# Wegpunkte sammeln
    print('Suche im '+str(radius)+' Radius')
    i = 0
    for lat, lon in track_points:
        for node in amenities:
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

def process_gpx(input_path, output_path):
    # Move your existing code here, but replace the hardcoded file paths:
    # Replace: gpx_file_path = 'dein_gpx_track.gpx'
    # With: gpx_file_path = input_path
    
    # And replace the output path:
    # Replace: new_gpx_file = 'updated_track_with_waypoints.gpx'
    # With: new_gpx_file = output_path
    

    # GPX-Datei laden und Track-Punkte extrahieren
    gpx_file_path = input_path
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

    all_amenities = find_bbox_amenities(api,s,w,n,e)

    waypoints = []
    waypoints = unique_waypoints(all_amenities,track_points, waypoints, 1.0)
    if (max_waypoint_dist(waypoints)>10):
        waypoints = unique_waypoints(all_amenities, track_points, waypoints, 2.0)
    # if (max_waypoint_dist(waypoints)>15):
    #     waypoints = unique_waypoints(track_points, waypoints, 3.0)
    # if (max_waypoint_dist(waypoints)>20):
    #     waypoints = unique_waypoints(track_points, waypoints, 4.0)
    # if (max_waypoint_dist(waypoints)>25):
    #     waypoints = unique_waypoints(track_points, waypoints, 5.0)

    # GPX Namespace
    gpx_ns = 'http://www.topografix.com/GPX/1/1'
    ET.register_namespace('', gpx_ns)

    # Neue GPX-Struktur mit Namespace erstellen
    #gpx = ET.Element(f'{{{gpx_ns}}}gpx', version="1.1", creator="Python Script")
    gpx = root

    # Dictionary mapping amenity types to Garmin symbols
    SYMBOL_MAPPING = {
        "drinking_water": "Drinking Water",
        "fuel": "Gas Station",
        "kiosk": "Shopping Cart",
        "supermarket": "Shopping Cart"
    }

    # Wegpunkte in das GPX-Dokument einfügen
    for waypoint in waypoints:
        try:
            wpt = ET.Element(f'{{{gpx_ns}}}wpt', lat=str(waypoint['lat']), lon=str(waypoint['lon']))
            ET.SubElement(wpt, f'{{{gpx_ns}}}name').text = f"{waypoint['name']}"
            ET.SubElement(wpt, f'{{{gpx_ns}}}sym').text = SYMBOL_MAPPING.get(waypoint['type'], "Flag")
            ET.SubElement(wpt, f'{{{gpx_ns}}}type').text = waypoint['type']
            gpx.insert(1, wpt)
        except Exception as e:
            print(f"Error adding waypoint: {e}")

    # tree = ET.ElementTree(gpx)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    print(f"Wegpunkte wurden in {output_path} gespeichert.")
        
    return output_path 