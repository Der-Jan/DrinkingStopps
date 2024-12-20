# GPX Amenity Enhancer

A web application that enhances GPX (GPS Exchange Format) files by automatically adding waypoints for nearby amenities along your tracks. Perfect for hiking, cycling, and outdoor activities where knowing the location of facilities like water sources, shops, and fuel stations is crucial.

## Features

- Upload GPX files through a web interface
- Automatically detects nearby amenities including:
  - Drinking water sources
  - Fuel stations
  - Kiosks
  - Supermarkets
- Downloads enhanced GPX file compatible with Garmin devices

## Technical Details

### Dependencies

- Flask (Web framework)
- requests (HTTP client for OpenStreetMap API)
- xml.etree.ElementTree (XML processing)
- Werkzeug (File handling)
