from __future__ import annotations
import logging
import logging.config
import simplejson as json
import yaml
from datetime import datetime
import time
from uuid import uuid4, UUID
from typing import Any, Generator, Optional
from confluent_kafka import SerializingProducer
from weather_api import Open_Meteo_API
from simulate_drive import Drive_Simulator, DriveStatus
import random
random.seed(42)


def generate_gps_data(drive_simulator:Generator[dict, None, None], device_id:str, vehicle_type:str='Private') -> dict:
    gps_data = next(drive_simulator)
    identity_data = {
        'id':uuid4(),
        'deviceId': device_id,
        'timestamp':datetime.now().isoformat(),
        'direction':'North-East',
        'vehicleType':vehicle_type
    }
    return identity_data | gps_data


def generate_vehicle_data(device_id:str, timestamp:str, latitude:float, longitude:float, speed:float) -> dict:
    return {
        'id':uuid4(),
        'deviceId': device_id,
        'timestamp':timestamp,
        'latitude':latitude,
        'longitude':longitude,
        'speed':speed,
        'direction':'North-East',
        'make':'BMW',
        'model':'X5',
        'year':2023,
        'fuelType':'Hybrid' 
    }

def generate_weather_data(weather_api:Open_Meteo_API, device_id:str, timestamp:str, latitude:float, longitude:float,) -> dict:
    identity_data = {
        'id':uuid4(),
        'deviceId': device_id,
        'timestamp':timestamp,
    }
    weather_data = weather_api.get_current_weather(latitude, longitude)
    return identity_data | weather_data

def generate_traffic_camera_data(device_id:str, camera_id:str, timestamp:str, latitude:float, longitude:float,) -> dict:
    return {
        'id':uuid4(),
        'deviceId': device_id,
        'cameraId':camera_id,
        'latitude':latitude,
        'longitude':longitude,
        'timestamp':timestamp,
        'snapshot':'Base64EncodedString'
    }

def generate_emergency_data(device_id:str, timestamp:str, latitude:float, longitude:float,) -> dict:
    return {
        'id':uuid4(),
        'deviceId': device_id,
        'incidentId':uuid4(),
        'type':random.choice(['Accident', 'Fire', 'Medical', 'Police', 'None']),
        'timestamp':timestamp,
        'latitude':latitude,
        'longitude':longitude,
        'status':random.choice(['Active', 'Resolved']),
        'description':'Accident Description goes here...'
    }

def json_serializer(obj:Any) -> str:
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not json serializable') 

def delivery_report(err:Any, msg:Any):
    if err is not None:
        logger.error('Producer message delivery failed', exc_info=True)
        print(f'Producer message delivery failed: {err}')
    else: 
        logger.info('Producer message delivered to %s [%s]', str(msg.topic()), str(msg.partition()))
        print(f'Producer message delivered to {msg.topic()} [{msg.partition()}]')

def produce_data_to_kafka(producer:Any, topic:str, data:dict):
    producer.produce(
        topic,
        key=str(data['id']),
        value=json.dumps(data, default=json_serializer).encode('utf-8'),
        on_delivery=delivery_report
    )
    producer.flush()


def simulate_journey(config:dict, producer:Any, weather_api:Open_Meteo_API, gps_data_generator:Generator[dict, None, None], device_id:str):
    while True:
        gps_data = generate_gps_data(gps_data_generator, device_id)
        vehicle_data = generate_vehicle_data(device_id, 
                                            gps_data['timestamp'], 
                                            gps_data['latitude'], 
                                            gps_data['longitude'],
                                            gps_data['speed'])
        weather_data = generate_weather_data(weather_api, 
                                            device_id, 
                                            gps_data['timestamp'], 
                                            gps_data['latitude'], 
                                            gps_data['longitude'],)
        traffic_data = generate_traffic_camera_data(device_id, 
                                                    'Nok-VS5Cam', 
                                                    gps_data['timestamp'], 
                                                    gps_data['latitude'], 
                                                    gps_data['longitude'],)
        emergency_data = generate_emergency_data(device_id, 
                                                gps_data['timestamp'], 
                                                gps_data['latitude'], 
                                                gps_data['longitude'],)
        
        logger.debug('CURRENT GPS DATA = %s', str(gps_data))
        logger.debug('CURRENT WEATHER DATA = %s', str(weather_data))
        
        produce_data_to_kafka(producer, config['gps_topic'], gps_data)
        produce_data_to_kafka(producer, config['vehicle_topic'], vehicle_data)
        produce_data_to_kafka(producer, config['weather_topic'], weather_data)
        produce_data_to_kafka(producer, config['traffic_topic'], traffic_data)
        produce_data_to_kafka(producer, config['emergency_topic'], emergency_data)
        
        if gps_data['status'] == DriveStatus.DESTINATION_REACHED:
            logger.info('Vehicle reached the destination. Simulation ending...')
            print('Vehicle reached the destination. Simulation ending...')
            break
        else:
            time.sleep(config['update_freq'])


def get_main_logger(logging_config_filepath:Optional[str]='jobs/configs/logging_configuration.yaml') -> logging.Logger:
    with open(logging_config_filepath, 'r') as file:
        logging_conf = yaml.safe_load(file)
    logging.config.dictConfig(logging_conf['logging'])
    return logging.getLogger('main_smart_city')

def get_configuration_dict(config_filepath:Optional[str]='jobs/configs/configuration.yaml'):
    with open(config_filepath, 'r') as file:
        config = yaml.safe_load(file)
    return config

if __name__ == "__main__":
    # Load configurations 
    config = get_configuration_dict()
    main_config = config['main_program']
    
    # Configure and get main logger
    logger = get_main_logger()
    # if you host the kafka on the cloud you 
    # need to add username and password to config
    producer_config = {
        'bootstrap.servers': main_config['kafka_bootstrap_servers'],
        'error_cb': lambda err: print(f'Kafka ERROR: {err}')  
    }  
    producer = SerializingProducer(producer_config)
    weather_api = Open_Meteo_API(meteo_configs=config['open_meteo'])
    logger.info('Weather API connection set up is done')
    
    start_coord = (main_config['start_loc_lat'],
                main_config['start_loc_lon'])
    end_coord = (main_config['end_loc_lat'],
                main_config['end_loc_lon'])
    drive_simulator = Drive_Simulator(start_location=start_coord, 
                                        end_location=end_coord, 
                                        update_freq=main_config['update_freq'])
    logger.info('Calculating the shortest route to the destination...')
    gps_data_generator = drive_simulator.generate_movement()
    logger.info('Shortest route generated, starting simulation')
    
    try:
        simulate_journey(main_config, producer, weather_api, gps_data_generator, 'Vehicle-SmartCity-123')
    except KeyboardInterrupt:
        logger.info('\nSimulation ended by the user')
        print('\nSimulation ended by the user')
    except Exception as e:
        logger.error('\nUnexpected error occurred: ', exc_info=True)
        print(f'Unexpected error occurred: {e}')
