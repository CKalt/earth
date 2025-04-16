import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# ------------------------------------------------------------------------------
# 1. Utility: Convert Degrees to Radians & Compute Great-Circle Points
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

    # Use the spherical law of cosines
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
# 2. Base Flight Paths (Checked by Default)
# ------------------------------------------------------------------------------
# Each entry:
# {
#   "id": "unique_id",
#   "label": "Label for checklist",
#   "checked": True/False,
#   "cities": [
#       (cityA_name, latA, lonA),
#       (cityB_name, latB, lonB)
#   ]
# }
BASE_FLIGHTS = [
    {
        "id": "lax_tokyo",
        "label": "Los Angeles → Tokyo",
        "checked": True,
        "cities": [
            ("Los Angeles", 34.0522, -118.2437),
            ("Tokyo", 35.6895, 139.6917)
        ],
    },
    {
        "id": "nyc_sydney",
        "label": "New York → Sydney",
        "checked": True,
        "cities": [
            ("New York", 40.7128, -74.0060),
            ("Sydney", -33.8688, 151.2093),
        ],
    },
    {
        "id": "london_buenosaires",
        "label": "London → Buenos Aires",
        "checked": True,
        "cities": [
            ("London", 51.5074, 0.1278),
            ("Buenos Aires", -34.6037, -58.3816),
        ],
    },
    {
        "id": "seattle_johannesburg",
        "label": "Seattle → Johannesburg",
        "checked": True,
        "cities": [
            ("Seattle", 47.6062, -122.3321),
            ("Johannesburg", -26.2041, 28.0473),
        ],
    },
    {
        "id": "paris_beijing",
        "label": "Paris → Beijing",
        "checked": True,
        "cities": [
            ("Paris", 48.8566, 2.3522),
            ("Beijing", 39.9042, 116.4074),
        ],
    },
    {
        "id": "vancouver_rio",
        "label": "Vancouver → Rio de Janeiro",
        "checked": True,
        "cities": [
            ("Vancouver", 49.2827, -123.1207),
            ("Rio de Janeiro", -22.9068, -43.1729),
        ],
    },
]

# ------------------------------------------------------------------------------
# 3. Additional ~80 Flights (Initially Unchecked)
#    We'll auto-generate flights between major cities worldwide.
# ------------------------------------------------------------------------------
# Let's define a set of major cities, then generate pairwise flights:
city_data = [
    ("Chicago",         41.8781,  -87.6298),
    ("Cairo",           30.0444,   31.2357),
    ("Mexico City",     19.4326,  -99.1332),
    ("Moscow",          55.7558,   37.6173),
    ("New Delhi",       28.6139,   77.2090),
    ("Rome",            41.9028,   12.4964),
    ("Cape Town",      -33.9249,   18.4241),
    ("Dubai",           25.2048,   55.2708),
    ("Lima",           -12.0464,  -77.0428),
    ("Hong Kong",       22.3193,  114.1694),
    ("Auckland",       -36.8485,  174.7633),
    ("Toronto",         43.6532,  -79.3832),
    ("Singapore",        1.3521,  103.8198),
]

ADDITIONAL_FLIGHTS = []

# We'll generate flights between each pair (City i, City j) for i < j
# to avoid duplicates (A→B and B→A).
for i in range(len(city_data)):
    for j in range(i+1, len(city_data)):
        cityA, latA, lonA = city_data[i]
        cityB, latB, lonB = city_data[j]

        # Create a unique ID and label:
        flight_id = f"{cityA.lower().replace(' ', '_')}_{cityB.lower().replace(' ', '_')}"
        flight_label = f"{cityA} → {cityB}"

        flight_dict = {
            "id": flight_id,
            "label": flight_label,
            "checked": False,  # all additional flights initially unchecked
            "cities": [
                (cityA, latA, lonA),
                (cityB, latB, lonB),
            ]
        }
        ADDITIONAL_FLIGHTS.append(flight_dict)

# OPTIONAL: If you want exactly 80, or a bit more, you could add a couple more lines manually.
# For demonstration, we'll just keep the entire set from the loop. That yields 78 pairs
# from the 13 cities. Let's add 2 more for a round total of 80:

ADDITIONAL_FLIGHTS.append({
    "id": "santiago_istanbul",
    "label": "Santiago → Istanbul",
    "checked": False,
    "cities": [
        ("Santiago", -33.4489, -70.6693),
        ("Istanbul", 41.0082, 28.9784),
    ]
})

ADDITIONAL_FLIGHTS.append({
    "id": "tokyo_rome",
    "label": "Tokyo → Rome",
    "checked": False,
    "cities": [
        ("Tokyo", 35.6895, 139.6917),
        ("Rome", 41.9028, 12.4964),
    ]
})

# Combine all flights into one list
FLIGHT_PATHS = BASE_FLIGHTS + ADDITIONAL_FLIGHTS

# ------------------------------------------------------------------------------
# 4. Functions to Create Plotly Figures
# ------------------------------------------------------------------------------
def create_globe_figure(selected_flights):
    """
    Creates an orthographic 'globe' figure using only flights in selected_flights.
    """
    globe_data = []
    for flight in selected_flights:
        # Unpack city data
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
            oceancolor='rgb(180, 220, 250)'
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return go.Figure(data=map_data, layout=map_layout)

# ------------------------------------------------------------------------------
# 5. Dash App Setup
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)

# Identify which flights are checked by default
default_checked_values = [f["id"] for f in FLIGHT_PATHS if f["checked"]]

app.layout = html.Div([
    html.H1("Dynamic Flight Paths with 80+ Options"),
    html.P("""
        Select which flight paths to display below. 
        They will appear or disappear on both the 3D globe and 
        the 2D flat map simultaneously. 
    """),

    # Checklist of flights
    dcc.Checklist(
        id='flight-checklist',
        options=[{"label": f["label"], "value": f["id"]} for f in FLIGHT_PATHS],
        value=default_checked_values,  # initially selected flights
        labelStyle={'display': 'block'},  # vertical stacking
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
# 6. Callback: when user checks/unchecks flights, update both figures
# ------------------------------------------------------------------------------
@app.callback(
    [Output('globe-graph', 'figure'),
     Output('map-graph', 'figure')],
    [Input('flight-checklist', 'value')]
)
def update_flights(selected_ids):
    """
    selected_ids: list of flight IDs that are currently checked.
    """
    # Filter the master FLIGHT_PATHS by the ones whose IDs are in selected_ids
    selected_flights = [f for f in FLIGHT_PATHS if f["id"] in selected_ids]

    globe_fig = create_globe_figure(selected_flights)
    map_fig = create_2d_figure(selected_flights, projection='equirectangular')
    return globe_fig, map_fig

# ------------------------------------------------------------------------------
# 7. Run
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
