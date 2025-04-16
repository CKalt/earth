# src/app.py

import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objs as go

# -----------------------------------------------------
# 1. Define Some Great Circle Paths
#    For demonstration, we'll include a few flights.
#    Each flight is specified by two endpoints, and we'll
#    compute intermediate points along the great circle.
# -----------------------------------------------------

# Example flight endpoints:
#  (lat1, lon1), (lat2, lon2)
flight_endpoints = [
    ("Los Angeles", 34.0522, -118.2437, 
     "Tokyo",       35.6895,  139.6917),
    ("New York",    40.7128,  -74.0060,
     "Sydney",     -33.8688,  151.2093),
    ("London",      51.5074,    0.1278,
     "Buenos Aires",-34.6037, -58.3816),
]

def to_radians(deg):
    return deg * np.pi / 180.0

def great_circle_points(lat1, lon1, lat2, lon2, num_points=50):
    """
    Compute a series of lat/lon points representing
    the great-circle path between two coordinates.
    Returns two arrays: lat_list, lon_list.
    """
    # Convert degrees to radians
    lat1_r, lon1_r = to_radians(lat1), to_radians(lon1)
    lat2_r, lon2_r = to_radians(lat2), to_radians(lon2)

    # Compute the angle between the two points
    # using the spherical law of cosines or haversine
    delta = np.arccos(
        np.sin(lat1_r) * np.sin(lat2_r)
        + np.cos(lat1_r) * np.cos(lat2_r) * np.cos(lon2_r - lon1_r)
    )

    # Create an array of interpolation factors
    step_array = np.linspace(0, 1, num_points)

    lat_points = []
    lon_points = []

    for s in step_array:
        # Interpolate along the great circle
        A = np.sin((1 - s) * delta) / np.sin(delta)
        B = np.sin(s * delta) / np.sin(delta)

        x = A * np.cos(lat1_r) * np.cos(lon1_r) + B * np.cos(lat2_r) * np.cos(lon2_r)
        y = A * np.cos(lat1_r) * np.sin(lon1_r) + B * np.cos(lat2_r) * np.sin(lon2_r)
        z = A * np.sin(lat1_r) + B * np.sin(lat2_r)

        # Convert back to lat/lon
        lat_gc = np.arctan2(z, np.sqrt(x * x + y * y))
        lon_gc = np.arctan2(y, x)

        lat_points.append(lat_gc * 180.0 / np.pi)
        lon_points.append(lon_gc * 180.0 / np.pi)

    return lat_points, lon_points


# -----------------------------------------------------
# 2. Build Plotly Figures
#    We'll create:
#    - A 3D "Globe" figure (using a sphere-like geo projection).
#    - A 2D projection figure (equirectangular or orthographic).
# -----------------------------------------------------

def create_globe_figure(flights):
    """
    Create a Plotly figure with 'type': 'scattergeo'
    using the 'orthographic' projection to mimic a globe.
    """
    globe_data = []
    
    for nameA, latA, lonA, nameB, latB, lonB in flights:
        lat_gc, lon_gc = great_circle_points(latA, lonA, latB, lonB)

        # Add the flight path
        globe_data.append(
            go.Scattergeo(
                lat=lat_gc,
                lon=lon_gc,
                mode='lines',
                line=dict(width=2, color='red'),
                name=f"{nameA} → {nameB}"
            )
        )

        # Add endpoints
        globe_data.append(
            go.Scattergeo(
                lat=[latA, latB],
                lon=[lonA, lonB],
                mode='markers+text',
                text=[nameA, nameB],
                textposition=["top center", "top center"],
                marker=dict(size=5, color='blue'),
                showlegend=False
            )
        )

    globe_layout = go.Layout(
        title="Flight Paths on 3D Globe (Orthographic Projection)",
        geo=dict(
            projection=dict(type='orthographic'),
            showland=True,
            landcolor='rgb(230, 230, 230)',
            showcountries=True,
            showocean=True,
            oceancolor='rgb(180, 220, 250)'
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return go.Figure(data=globe_data, layout=globe_layout)

def create_2d_figure(flights, projection='equirectangular'):
    """
    Create a 2D map figure to show how these great circles
    appear in a common flat projection.
    """
    map_data = []
    for nameA, latA, lonA, nameB, latB, lonB in flights:
        lat_gc, lon_gc = great_circle_points(latA, lonA, latB, lonB)

        map_data.append(
            go.Scattergeo(
                lat=lat_gc,
                lon=lon_gc,
                mode='lines',
                line=dict(width=2, color='red'),
                name=f"{nameA} → {nameB}"
            )
        )

        # Add endpoints
        map_data.append(
            go.Scattergeo(
                lat=[latA, latB],
                lon=[lonA, lonB],
                mode='markers+text',
                text=[nameA, nameB],
                textposition=["top center", "top center"],
                marker=dict(size=5, color='blue'),
                showlegend=False
            )
        )

    map_layout = go.Layout(
        title=f"Flight Paths on 2D Map ({projection.capitalize()} Projection)",
        geo=dict(
            projection=dict(type=projection),
            showland=True,
            landcolor='rgb(230, 230, 230)',
            showcountries=True,
            showocean=True,
            oceancolor='rgb(180, 220, 250)'
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return go.Figure(data=map_data, layout=map_layout)


# -----------------------------------------------------
# 3. Create the Dash App
# -----------------------------------------------------
app = dash.Dash(__name__)

# Create two figures: one "3D" (orthographic) and one 2D
globe_fig = create_globe_figure(flight_endpoints)
map_fig = create_2d_figure(flight_endpoints, projection='equirectangular')

app.layout = html.Div([
    html.H1("Great-Circle Flight Paths Demonstration"),
    html.P("""
        This interactive demo shows how flight paths that are 
        essentially straight lines (arcs of a great circle) on 
        the globe appear curved on a flat 2D map projection.
    """),
    html.Div([
        dcc.Graph(
            id='globe-graph',
            figure=globe_fig,
            style={'width': '45%', 'display': 'inline-block'}
        ),
        dcc.Graph(
            id='map-graph',
            figure=map_fig,
            style={'width': '45%', 'display': 'inline-block', 'float': 'right'}
        )
    ]),
])

if __name__ == '__main__':
    app.run_server(debug=True)
