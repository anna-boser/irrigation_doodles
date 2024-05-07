import pandas as pd
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import os 

# Load the data
file_path = 'data/GEE/meta.csv'
data = pd.read_csv(file_path)
maps_directory='data/maps'

# Identify all unique landcover types across the entire dataset
all_landcovers = data['landcover'].unique()

# Create a consistent color mapping for these types
color_scale = cm.linear.Set1_09.scale(0, len(all_landcovers))
consistent_color_dict = {landcover: color_scale(i) for i, landcover in enumerate(all_landcovers)}

# Function to create a map for a given site
def create_site_map(df, site_name, color_dict):
    # Filter data for the site
    site_data = df[df['site'] == site_name]
    if site_data.empty:
        return None

    mean_lat = site_data['latitude'].mean()
    mean_long = site_data['longitude'].mean()

    # Create map with satellite basemap
    site_map = folium.Map(
        location=[mean_lat, mean_long],
        zoom_start=12,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite'
    )

    # Add points to the map with consistent color for landcover
    for idx, row in site_data.iterrows():
        folium.CircleMarker(
            location=(row['latitude'], row['longitude']),
            radius=5,
            color=color_dict[row['landcover']],
            fill=True,
            fill_color=color_dict[row['landcover']],
            fill_opacity=0.7,
            popup=f"Index: {idx}, Landcover: {row['landcover']}"
        ).add_to(site_map)
    
    return site_map

# Get unique sites
unique_sites = data['site'].unique()

# Remove sites for which maps have already been created
existing_maps = [file.split('.html')[0] for file in os.listdir(maps_directory)]
unique_sites = [site for site in unique_sites if site not in existing_maps]

# Remove nan from site list
unique_sites = [site for site in unique_sites if str(site) != 'nan']

# Create and display maps for each site (displaying the first one for demonstration)
site_maps = {site: create_site_map(data, site, consistent_color_dict) for site in unique_sites}

# Create and save an HTML file for each map
for site, site_map in site_maps.items():
    if site_map:  # Ensure the map was created successfully
        file_path = f"{maps_directory}/{site.replace(' ', '_')}.html"
        site_map.save(file_path)

