from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.functions import from_json, col
from typing import Optional
import yaml
from spark_schemas import VEHICLE_SCHEMA, GPS_SCHEMA, WEATHER_SCHEMA,\
                        TRAFFIC_SCHEMA, EMERGENCY_SCHEMA

def get_config(config_filepath:Optional[str]='jobs/configs/configuration.yaml'):
    with open(config_filepath, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    config = get_config()
    spark_config = config['spark']
    main_config = config['main_program']
    
    spark = SparkSession.builder.appName(spark_config['app_name'])\
        .config('spark.jars.packages',
        f'{spark_config["mvn_spark_groupId"]}:{spark_config["mvn_spark_artifactId"]}:{spark_config["mvn_spark_version"]},'
        f'{spark_config["mvn_hadoop_groupId"]}:{spark_config["mvn_hadoop_artifactId"]}:{spark_config["mvn_hadoop_version"]},'
        f'{spark_config["mvn_java_groupId"]}:{spark_config["mvn_java_artifactId"]}:{spark_config["mvn_java_version"]}')\
        .config('spark.hadoop.fs.s3a.impl', spark_config['s3_impl_config'])\
        .config('spark.hadoop.fs.s3a.access.key', spark_config['s3_access_key'])\
        .config('spark.hadoop.fs.s3a.secret.key', spark_config['s3_secret_key'])\
        .config('spark.hadoop.fs.s3a.aws.credentials.provider', spark_config['s3_credentials_provider'])\
        .getOrCreate()

    # Adjust the log level to WARN to minimize console writing
    spark.sparkContext.setLogLevel('WARN')
    
    def read_kafka_topic(topic, schema):
        return(spark.readStream
            .format('kafka')
            .option('kafka.bootstrap.servers', spark_config['kafka_broker'])
            .option('subscribe', topic)
            .option('startingOffsets', 'earliest')
            .load()
            .selectExpr('CAST(value AS STRING)')
            .select(from_json(col('value'), schema).alias('data'))
            .select('data.*')
            .withWatermark('timestamp', '5 minutes')    
        )
    
    def streamWriter(input:DataFrame, checkpointFolder, output):
        return (input.writeStream
                .format('parquet')
                .option('checkpointLocation', checkpointFolder)
                .option('path', output)
                .outputMode('append')
                .start()
                )
    
    gpsDF = read_kafka_topic(main_config['gps_topic'], GPS_SCHEMA).alias('gps')
    vehicleDF = read_kafka_topic(main_config['vehicle_topic'], VEHICLE_SCHEMA).alias('vehicle')
    weatherDF = read_kafka_topic(main_config['weather_topic'], WEATHER_SCHEMA).alias('weather')
    trafficDF = read_kafka_topic(main_config['traffic_topic'], TRAFFIC_SCHEMA).alias('traffic')
    emergencyDF = read_kafka_topic(main_config['emergency_topic'], EMERGENCY_SCHEMA).alias('emergency')
    
    # Join all the dfs with id and timestamp
    s3_base_path = spark_config['s3_base_path']
    print(f'spark path {s3_base_path}')
    query1 = streamWriter(gpsDF, f'{s3_base_path}/checkpoints/gps_data',
                        f'{s3_base_path}/data/gps_data')
    query2 = streamWriter(vehicleDF, f'{s3_base_path}/checkpoints/vehicle_data',
                        f'{s3_base_path}/data/vehicle_data')
    query3 = streamWriter(weatherDF, f'{s3_base_path}/checkpoints/weather_data',
                        f'{s3_base_path}/data/weather_data')
    query4 = streamWriter(trafficDF, f'{s3_base_path}/checkpoints/traffic_data',
                        f'{s3_base_path}/data/traffic_data')
    query5 = streamWriter(emergencyDF, f'{s3_base_path}/checkpoints/emergency_data',
                        f'{s3_base_path}/data/emergency_data')
    
    # To ensure that the queries will run in parallel, apply awaitTermination only on the last query
    query5.awaitTermination()

if __name__ == "__main__":
    
    main()