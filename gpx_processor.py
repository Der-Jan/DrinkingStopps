# ... (keep all your imports) ...
import overpy
import xml.etree.ElementTree as ET
import geopy.distance
from flask import current_app
    
# Funktion, um relevante Orte in der Nähe eines Punkts zu finden
def find_bbox_amenities(api, s,w,n,e):
    query = f"""
    [out:json];
    (
    node["amenity"="drinking_water"]({s},{w},{n},{e});
    node["amenity"="fuel"]({s},{w},{n},{e});
    node["amenity"="restaurant"]({s},{w},{n},{e});
    node["shop"="kiosk"]({s},{w},{n},{e});
    node["shop"="supermarket"]({s},{w},{n},{e});
    );
    out center;
    """
    try:
        result = api.query(query)
        current_app.logger.debug('OSM-Abfrage erfolgreich - '+str(len(result.nodes))+' Orte gefunden')
        return result.nodes
    except Exception as e:
        current_app.logger.error(f"Error querying OSM: {str(e)}")
        return []

def unique_waypoints(amenities, track_points, waypoints, radius, progress_callback=None):
# Wegpunkte sammeln
    current_app.logger.debug('Suche im '+str(radius)+' Radius')
    current_point = 0
    
    ref_trkpt = {}
    total_points = len(track_points)
    
    for lat, lon in track_points:
        amenitycount=0
        for node in amenities:
            dist = geopy.distance.geodesic((lat,lon), (node.lat,node.lon)).km
            if (dist<radius):
                waypoint = {
                    'name': node.tags.get('name', 'Unknown'),
                    'lat': node.lat,
                    'lon': node.lon,
                    'type': node.tags.get('amenity', node.tags.get('shop', 'Unknown'))
                }
                if (amenitycount not in ref_trkpt):
                    ref_trkpt[amenitycount] = { 'wp': waypoint, 'lat': lat, 'lon': lon, 'dist': dist}
                    current_app.logger.debug('Watt gefunden für Trackpoint '+str(current_point)+' ' + waypoint['name'] +'\n')
                else:
                    if (dist<ref_trkpt[amenitycount]['dist']):
                        ref_trkpt[amenitycount] = { 'wp': waypoint, 'lat': lat, 'lon': lon, 'dist': dist}
                        current_app.logger.debug('Trackpoint '+str(current_point)+' ist näher an ' + waypoint['name'] +'\n')
            amenitycount+=1    
        current_point += 1
        if progress_callback:
            progress_callback(current_point, total_points)
    for amn in ref_trkpt:
        wp = ref_trkpt[amn]['wp']
        wp['lat']=ref_trkpt[amn]['lat']
        wp['lon']=ref_trkpt[amn]['lon']
        wp['name']=wp['name']+': '+str(round(ref_trkpt[amn]['dist'],1))+'km'
        waypoints.append(wp)
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

def process_gpx(input_path, output_path, progress_callback=None):
    tree = ET.parse(input_path)
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
    waypoints = unique_waypoints(all_amenities,track_points, waypoints, 1.0, progress_callback)
    # if (max_waypoint_dist(waypoints)>10):
    #     waypoints = unique_waypoints(all_amenities, track_points, waypoints, 2.0, progress_callback)

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
        "drinking_water": "WATER",
        "fuel": "STORE",
        "kiosk": "FOOD",
        "restaurant": "FOOD",
        "supermarket": "STORE"
    }

    # Wegpunkte in das GPX-Dokument einfügen
    for waypoint in waypoints:
        try:
            wpt = ET.Element(f'{{{gpx_ns}}}wpt', lat=str(waypoint['lat']), lon=str(waypoint['lon']))
            ET.SubElement(wpt, f'{{{gpx_ns}}}name').text = f"{waypoint['name']}: {waypoint['type']}"
            ET.SubElement(wpt, f'{{{gpx_ns}}}type').text = SYMBOL_MAPPING.get(waypoint['type'], "Flag")
            gpx.insert(1, wpt)
        except Exception as e:
            current_app.logger.error(f"Error adding waypoint: {str(e)}")

    # tree = ET.ElementTree(gpx)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    current_app.logger.debug(f"Wegpunkte wurden in {output_path} gespeichert.")
        
    return output_path 