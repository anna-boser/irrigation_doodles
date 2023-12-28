import ee
import pandas as pd
import os
ee.Initialize()

# Load the metadata file with coordinate locations
data = pd.read_csv('data/GEE/meta.csv')

def get_ts(latitude, longitude, site, landcover, ID):
    # Define the point for which you want to extract the EVI time series
    point = ee.Geometry.Point([longitude, latitude])

    # Set the date range
    start_date = '2018-01-01'
    end_date = '2022-12-31'

    # Access the Sentinel-2 image collection, filter it by date and cloud coverage, and focus on the area of interest.
    s2 = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(start_date, end_date) \
            .filterBounds(point)

    # Print out the number of images you got
    image_count = s2.size().getInfo()
    print('Number of images in the collection:', image_count)

    # Define the EVI calculation for Each Image

    def calculate_metrics(image):
        # Sentinel-2 band names for NIR, RED and BLUE, and QA60 for cloud detection
        nir = image.select('B8')  # Near Infrared
        red = image.select('B4')  # Red
        blue = image.select('B2')  # Blue
        qa = image.select('QA60')  # Cloud mask band

        # Cloud mask
        cloudMask = qa.bitwiseAnd(1 << 10).Or(qa.bitwiseAnd(1 << 11)).eq(0)

        # Calculate EVI
        EVI = image.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {
                'NIR': nir,
                'RED': red,
                'BLUE': blue
            }).rename('EVI')
        
        # Calculate NDVI
        NDVI = image.normalizedDifference(['B8', 'B4']).rename('NDVI')

        # Cloud indicator band: 1 if cloudy, 0 if clear
        cloudIndicator = cloudMask.Not().rename('cloudy')

        return image.addBands([EVI, NDVI, cloudIndicator])

    # Map the EVI Calculation and Extract the Data

    evi_ts = s2.map(calculate_metrics)

    def extract_values(image):
        # Extracting date, EVI value, and cloud status
        date = image.date().format('YYYY-MM-dd HH:mm:ss')
        evi_val = image.reduceRegion(ee.Reducer.first(), point).get('EVI')
        ndvi_val = image.reduceRegion(ee.Reducer.first(), point).get('NDVI')
        cloud_status = image.reduceRegion(ee.Reducer.first(), point).get('cloudy')
        return ee.Feature(point, {'date': date, 'EVI': evi_val, 'NDVI': ndvi_val, 'cloudy': cloud_status})


    evi_data = evi_ts.map(extract_values)

    # Convert the EVI data to a list
    evi_list = evi_data.getInfo()

    data = [{
        'longitude': feature['geometry']['coordinates'][0],
        'latitude': feature['geometry']['coordinates'][1],
        'date': feature['properties'].get('date', None),
        'EVI': feature['properties'].get('EVI', None),
        'NDVI': feature['properties'].get('NDVI', None),
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

    # Save the data to a csv file
    df.to_csv(f'data/GEE/sentinel_ts/{site}, {landcover}, {ID}.csv', index=False)

# Iterate through each row in the DataFrame and run the function if the file doesn't exist
for index, row in data.iterrows():
    # Construct the expected file name based on the row data
    expected_filename = f'data/GEE/sentinel_ts/{row["site"]}, {row["landcover"]}, {index}.csv'
    
    # Check if the file already exists
    if not os.path.exists(expected_filename):
        # If the file does not exist, run the get_ts function
        get_ts(row['latitude'], row['longitude'], row['site'], row['landcover'], index)
    else:
        # If the file exists, print a message or simply continue
        print(f"Data for {row['site']}, {row['landcover']}, {index} already computed.")