import geopandas as gpd

####################################################################################################
# Do 2021

# Load the GeoJSON file
file_path = 'data/Timon data/newTD_20210726.geojson'
geo_data = gpd.read_file(file_path)

# Calculate the centroid of each polygon to get latitude and longitude
geo_data['centroid'] = geo_data.geometry.centroid
geo_data['latitude'] = geo_data.centroid.y
geo_data['longitude'] = geo_data.centroid.x

# Selecting the required columns and renaming them accordingly
selected_columns = geo_data[['latitude', 'longitude', 'area', 'landcover_level2']]
selected_columns.columns = ['latitude', 'longitude', 'site', 'landcover']

selected_columns = selected_columns.drop_duplicates()

# Saving the selected data to a CSV file
csv_file_path = 'data/Timon data/centroids2021.csv'
selected_columns.to_csv(csv_file_path, index=False)
