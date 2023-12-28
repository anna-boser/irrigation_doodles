import ee
import pandas as pd
import os
ee.Initialize()

# Load the metadata file with coordinate locations
data = pd.read_csv('data/GEE/meta.csv')

# Define the Function to Retrieve Indices
def get_ts(latitude, longitude, site, landcover, ID):
    print(f'Extracting data for {site}, {landcover}, {ID}.')

    point = ee.Geometry.Point([longitude, latitude])
    start_date = '2018-01-01'
    end_date = '2022-12-31'

    # Access the Landsat 8 image collection
    landsat = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
                  .filterDate(start_date, end_date) \
                  .filterBounds(point)
    
    # Print out the number of images you got
    image_count = landsat.size().getInfo()
    print('Number of images in the collection:', image_count)

    def calculate_indices(image):
        # Calculate NDVI using NIR (B5) and Red (B4)
        ndvi = image.normalizedDifference(['B5', 'B4']).rename("NDVI")
        
        # Calculate EVI using the formula and NIR (B5), Red (B4), and Blue (B2)
        evi = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                'NIR': image.select('B5'),
                'RED': image.select('B4'),
                'BLUE': image.select('B2')
            }).rename("EVI")
        
        # Calculate NDWI using Green (B3) and NIR (B5)
        ndwi = image.normalizedDifference(['B3', 'B5']).rename("NDWI")

        # Retrieve TIR (Thermal Infrared) band - for Landsat 8 this is band 10 or 11; B10 is typically used.
        tir = image.select('B10').rename("TIR")

        # Cloud Masking using QA band
        # Define the bits we need to extract for cloud and cloud confidence
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        qa = image.select('pixel_qa')

        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) \
                 .And(qa.bitwiseAnd(cloudsBitMask).eq(0))

        # Apply the mask to the image
        masked_image = image.updateMask(mask)

        # Add the cloud mask as a separate band for reference (1 for cloudy, 0 for clear)
        cloud_mask = mask.Not().rename("cloudy")

        # Combine all the indices together with the original image
        return masked_image.addBands([ndvi, evi, ndwi, tir, cloud_mask])

    # Apply the function over the image collection
    indexed_collection = landsat.map(calculate_indices)

    def extract_values(image):
        # Extracting date, EVI value, and cloud status
        date = image.date().format('YYYY-MM-dd HH:mm:ss')
        evi_val = image.reduceRegion(ee.Reducer.first(), point).get('EVI')
        ndvi_val = image.reduceRegion(ee.Reducer.first(), point).get('NDVI')
        ndwi_val = image.reduceRegion(ee.Reducer.first(), point).get('NDWI')
        tir_val = image.reduceRegion(ee.Reducer.first(), point).get('TIR')
        cloud_status = image.reduceRegion(ee.Reducer.first(), point).get('cloudy')
        return ee.Feature(point, {'date': date, 
                                  'EVI': evi_val, 
                                  'NDVI': ndvi_val, 
                                  'NDWI': ndwi_val,
                                  'TIR': tir_val,
                                  'cloudy': cloud_status})


    evi_data = indexed_collection.map(extract_values)

    # Convert the data to a list
    evi_list = evi_data.getInfo()

    data = [{
        'longitude': feature['geometry']['coordinates'][0],
        'latitude': feature['geometry']['coordinates'][1],
        'date': feature['properties'].get('date', None),
        'EVI': feature['properties'].get('EVI', None),
        'NDVI': feature['properties'].get('NDVI', None),
        'NDWI': feature['properties'].get('NDWI', None),
        'TIR': feature['properties'].get('TIR', None),
        'Cloudy': feature['properties'].get('cloudy', None)
    } for feature in evi_list['features']]

    # Convert to a pandas DataFrame
    df = pd.DataFrame(data)

    # Further process the 'date' into year, month, day, and time if needed
    df['year'] = pd.to_datetime(df['date']).dt.year
    df['month'] = pd.to_datetime(df['date']).dt.month
    df['day'] = pd.to_datetime(df['date']).dt.day
    df['time'] = pd.to_datetime(df['date']).dt.time

    # Define site and landcover
    df['site'] = site
    df['landcover'] = landcover
    df['ID'] = ID

    # Save the data to a csv file
    df.to_csv(f'data/GEE/landsat_ts/{site}, {landcover}, {ID}.csv', index=False)

# Iterate through each row in the DataFrame and run the function if the file doesn't exist
for index, row in data.iterrows():
    # Construct the expected file name based on the row data
    expected_filename = f'data/GEE/landsat_ts/{row["site"]}, {row["landcover"]}, {index}.csv'
    
    # Check if the file already exists
    if not os.path.exists(expected_filename):
        # If the file does not exist, run the get_ts function
        get_ts(row['latitude'], row['longitude'], row['site'], row['landcover'], index)
    else:
        # If the file exists, print a message or simply continue
        print(f"Data for {row['site']}, {row['landcover']}, {index} already computed.")