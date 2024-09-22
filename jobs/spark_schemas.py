from pyspark.sql.types import StructType, StructField, StringType, DoubleType, \
                IntegerType, TimestampType, BooleanType

GPS_SCHEMA = StructType([
    StructField('id', StringType(), True),
    StructField('deviceId', StringType(), True),
    StructField('timestamp', TimestampType(), True),
    StructField('direction', StringType(), True),
    StructField('vehicleType', StringType(), True),
    StructField('latitude', DoubleType(), True),
    StructField('longitude', DoubleType(), True),
    StructField('osmid', IntegerType(), True),
    StructField('street_name', StringType(), True),
    StructField('oneway', BooleanType(), True),
    StructField('speed', DoubleType(), True),
    StructField('status', StringType(), True),
    StructField('geometry', StringType(), True),
])

VEHICLE_SCHEMA = StructType([
    StructField('id', StringType(), True),
    StructField('deviceId', StringType(), True),
    StructField('timestamp', TimestampType(), True),
    StructField('latitude', DoubleType(), True),
    StructField('longitude', DoubleType(), True),
    StructField('speed', DoubleType(), True),
    StructField('direction', StringType(), True),
    StructField('make', StringType(), True),
    StructField('model', StringType(), True),
    StructField('year', IntegerType(), True),
    StructField('fuelType', StringType(), True)
])


WEATHER_SCHEMA = StructType([
    StructField('id', StringType(), True),
    StructField('deviceId', StringType(), True),
    StructField('timestamp', TimestampType(), True),
    StructField('latitude', DoubleType(), True),
    StructField('longitude', DoubleType(), True),
    StructField('temperature_2m', DoubleType(), True),
    StructField('relative_humidity_2m', DoubleType(), True),
    StructField('apparent_temperature', DoubleType(), True),
    StructField('is_day', DoubleType(), True),
    StructField('precipitation', DoubleType(), True),
    StructField('rain', DoubleType(), True),
    StructField('showers', DoubleType(), True),
    StructField('snowfall', DoubleType(), True),
    StructField('weather_code', DoubleType(), True),
    StructField('cloud_cover', DoubleType(), True),
    StructField('pressure_msl', StringType(), True),
    StructField('surface_pressure', DoubleType(), True),
    StructField('wind_speed_10m', DoubleType(), True),
    StructField('wind_direction_10m', DoubleType(), True),
    StructField('wind_gusts_10m', DoubleType(), True)
])

TRAFFIC_SCHEMA = StructType([
    StructField('id', StringType(), True),
    StructField('deviceId', StringType(), True),
    StructField('cameraId', StringType(), True),
    StructField('latitude', DoubleType(), True),
    StructField('longitude', DoubleType(), True),
    StructField('timestamp', TimestampType(), True),
    StructField('snapshot', StringType(), True)
])

EMERGENCY_SCHEMA = StructType([
    StructField('id', StringType(), True),
    StructField('deviceId', StringType(), True),
    StructField('incidentId', StringType(), True),
    StructField('type', StringType(), True),
    StructField('timestamp', TimestampType(), True),
    StructField('latitude', DoubleType(), True),
    StructField('longitude', DoubleType(), True),
    StructField('status', StringType(), True),
    StructField('description', StringType(), True)
])