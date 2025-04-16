import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# ------------------------------------------------------------------------------
# 1. Define Flight Paths and Great-Circle Computation
# ------------------------------------------------------------------------------
def to_radians(deg):
    return deg * np.pi / 180.0

def great_circle_points(lat1, lon1, lat2, lon2, num_points=50):
    """
    Compute a series of lat/lon points representing
    the great-circle path between two coordinates.
    Returns two arrays: lat_list, lon_list.
    """
    lat1_r, lon1_r = to_radians(lat1), to_radians(lon1)
    lat2_r, lon2_r = to_radians(lat2), to_radians(lon2)

    # Spherical law of cosines
    delta = np.arccos(
        np.sin(lat1_r) * np.sin(lat2_r)
        + np.cos(lat1_r) * np.cos(lat2_r) * np.cos(lon2_r - lon1_r)
    )

    step_array = np.linspace(0, 1, num_points)
    lat_points = []
    lon_points = []

    for s in step_array:
        A = np.sin((1 - s) * delta) / np.sin(delta)
        B = np.sin(s * delta) / np.sin(delta)

        x = A * np.cos(lat1_r) * np.cos(lon1_r) + B * np.cos(lat2_r) * np.cos(lon2_r)
        y = A * np.cos(lat1_r) * np.sin(lon1_r) + B * np.cos(lat2_r) * np.sin(lon2_r)
        z = A * np.sin(lat1_r) + B * np.sin(lat2_r)

        lat_gc = np.arctan2(z, np.sqrt(x * x + y * y)) * 180.0 / np.pi
        lon_gc = np.arctan2(y, x) * 180.0 / np.pi

        lat_points.append(lat_gc)
        lon_points.append(lon_gc)

    return lat_points, lon_points

# ------------------------------------------------------------------------------
# 2. Flight Paths Data
# ------------------------------------------------------------------------------
# Each entry: 
#   {
#       "id": "someUniqueID",
#       "label": "Text for checklist",
#       "checked": bool,  (True => flight is visible by default)
#       "cities": [ (CityA name, latA, lonA), (CityB name, latB, lonB) ]
#   }
FLIGHT_PATHS = [
    {
        "id": "lax_tokyo",
        "label": "Los Angeles → Tokyo",
        "checked": True,
        "cities": [
            ("Los Angeles", 34.0522, -118.2437),
            ("Tokyo", 35.6895, 139.6917)
        ]
    },
    {
        "id": "nyc_sydney",
        "label": "New York → Sydney",
        "checked": True,
        "cities": [
            ("New York", 40.7128, -74.0060),
            ("Sydney", -33.8688, 151.2093)
        ]
    },
    {
        "id": "london_buenosaires",
        "label": "London → Buenos Aires",
        "checked": True,
        "cities": [
            ("London", 51.5074, 0.1278),
            ("Buenos Aires", -34.6037, -58.3816)
        ]
    },
    {
        "id": "seattle_johannesburg",
        "label": "Seattle → Johannesburg",
        "checked": False,  # initially unchecked
        "cities": [
            ("Seattle", 47.6062, -122.3321),
            ("Johannesburg", -26.2041, 28.0473)
        ]
    },
    {
        "id": "paris_beijing",
        "label": "Paris → Beijing",
        "checked": False,  # initially unchecked
        "cities": [
            ("Paris", 48.8566, 2.3522),
            ("Beijing", 39.9042, 116.4074)
        ]
    },
    {
        "id": "vancouver_rio",
        "label": "Vancouver → Rio de Janeiro",
        "checked": False,  # initially unchecked
        "cities": [
            ("Vancouver", 49.2827, -123.1207),
            ("Rio de Janeiro", -22.9068, -43.1729)
        ]
    },
]


# ------------------------------------------------------------------------------
# 3. Helper Functions to Build the Figures
# ------------------------------------------------------------------------------
def create_globe_figure(selected_flights):
    """
    Creates an orthographic 'globe' figure using only flights in selected_flights.
    """
    globe_data = []
    
    for flight in selected_flights:
        (nameA, latA, lonA), (nameB, latB, lonB) = flight["cities"]
        lat_gc, lon_gc = great_circle_points(latA, lonA, latB, lonB)

        # Flight path (red line)
        globe_data.append(
            go.Scattergeo(
                lat=lat_gc,
                lon=lon_gc,
                mode='lines',
                line=dict(width=2, color='red'),
                name=flight["label"]
            )
        )

        # Endpoints
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


def create_2d_figure(selected_flights, projection='equirectangular'):
    """
    Creates a 2D map figure using only flights in selected_flights.
    """
    map_data = []
    
    for flight in selected_flights:
        (nameA, latA, lonA), (nameB, latB, lonB) = flight["cities"]
        lat_gc, lon_gc = great_circle_points(latA, lonA, latB, lonB)

        # Flight path (red line)
        map_data.append(
            go.Scattergeo(
                lat=lat_gc,
                lon=lon_gc,
                mode='lines',
                line=dict(width=2, color='red'),
                name=flight["label"]
            )
        )

        # Endpoints
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
            oceancolor='rgb(180, 220, 250)',
            # For equirectangular, set these for full world view:
            # lonaxis=dict(showgrid=True, range=[-180, 180]),
            # lataxis=dict(showgrid=True, range=[-90, 90])
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return go.Figure(data=map_data, layout=map_layout)


# ------------------------------------------------------------------------------
# 4. Dash App Setup
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)

# Prepare the default "checked" values
default_checked_values = [
    flight["id"] for flight in FLIGHT_PATHS if flight["checked"]
]

app.layout = html.Div([
    html.H1("Dynamic Flight Paths with Checkboxes"),
    html.P("""
        Select which flight paths to display. 
        Watch how they appear on both the 3D globe and the 2D map.
    """),

    # Checklist of flights:
    dcc.Checklist(
        id='flight-checklist',
        options=[
            {"label": f["label"], "value": f["id"]} for f in FLIGHT_PATHS
        ],
        value=default_checked_values,  # selected by default
        labelStyle={'display': 'block'},  # one per line
        inputStyle={"margin-right": "5px"}
    ),

    html.Br(),

    # Two side-by-side graphs
    html.Div([
        dcc.Graph(id='globe-graph', style={'width': '45%', 'display': 'inline-block'}),
        dcc.Graph(id='map-graph', style={'width': '45%', 'display': 'inline-block', 'float': 'right'})
    ]),
])


# ------------------------------------------------------------------------------
# 5. Callback: whenever the checklist changes, update both figures
# ------------------------------------------------------------------------------
@app.callback(
    [Output('globe-graph', 'figure'),
     Output('map-graph', 'figure')],
    [Input('flight-checklist', 'value')]
)
def update_flights(selected_ids):
    # selected_ids is a list of flight IDs that are currently checked
    # Filter FLIGHT_PATHS to get only the flights that match these IDs
    selected_flights = [f for f in FLIGHT_PATHS if f["id"] in selected_ids]

    globe_fig = create_globe_figure(selected_flights)
    map_fig = create_2d_figure(selected_flights, projection='equirectangular')
    return globe_fig, map_fig


# ------------------------------------------------------------------------------
# 6. Run
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
