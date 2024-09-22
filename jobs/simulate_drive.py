from math import ceil
from geopy import distance
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString
from shapely import wkt
from enum import Enum
import random
from typing import Tuple, Generator
random.seed(42)


class DriveStatus(str, Enum):
    IDLE = 'Idle'
    MOVING = 'Moving'
    DESTINATION_REACHED = 'Destination reached'

def calc_circle_map_distance(start_latlng: Tuple[float, float], end_latlng: Tuple[float, float]) -> int:
    
    return ceil(distance.distance(start_latlng, end_latlng).m)

def interpolate_line(line:LineString, distance:float) -> Point:
    # Sample a point on the LineString after x distance traveled
    return line.interpolate(distance)

class Drive_Simulator:
    
    def __init__(self, start_location:Tuple[float, float], end_location:Tuple[float, float]=None, update_freq:int=3,  transport_type:str='drive'):
        self.start_location = start_location
        self.end_location = end_location
        self.distance = calc_circle_map_distance(self.start_location, self.end_location) 
        
        self.transport_type = transport_type
        self.update_freq = update_freq
        
        self.G = ox.graph_from_point(self.start_location, dist=self.distance, network_type=self.transport_type)
        self.G = ox.utils_graph.get_largest_component(self.G, strongly=True)
        self.G = ox.routing.add_edge_speeds(self.G)
        self.G = ox.routing.add_edge_travel_times(self.G)
        self.start_node, self.end_node = self.get_start_n_end_graph_nodes()
        
        self.shortest_path = nx.shortest_path(self.G, 
                                                self.start_node,
                                                self.end_node,
                                                weight='travel_time')
        self.route_gdf = ox.routing.route_to_gdf(self.G, self.shortest_path, weight='length')
        self.route_gdf['str_geom'] = self.route_gdf['geometry'].apply(wkt.dumps)
    
    def get_start_n_end_graph_nodes(self):
        start_node = ox.distance.nearest_nodes(self.G, self.start_location[1],
                                        self.start_location[0])
        end_node = ox.distance.nearest_nodes(self.G, self.end_location[1],
                                        self.end_location[0])
        return start_node, end_node
            
    def generate_movement(self) -> Generator[dict, None, None]:
        gps_data = {}
        for _ , row in self.route_gdf.iterrows():
            geom = row['geometry']
            travel_time = row['travel_time']  # in seconds
            speed_limit = row['speed_kph']  # in km/h
            gps_data = {
                'latitude': .0,
                'longitude': .0,
                'osmid': row['osmid'],
                'street_name': row['name'],
                'oneway': row['oneway'],
                'speed': 0,
                'status': DriveStatus.IDLE.value,
                'geometry':row['str_geom']
            }
            if isinstance(geom, Point): # If the driver is not moving
                for t in range(0, travel_time, self.update_freq):
                    gps_data['latitude'] = round(geom.y, 3)
                    gps_data['longitude'] = round(geom.x, 3)
                    gps_data['speed'] = 0
                    yield gps_data

            elif isinstance(geom, LineString): # If the driver is moving either on a straight or curved street
                total_samples = ceil(travel_time // self.update_freq)
                for i in range(total_samples):
                    distance_traveled = speed_limit * i * self.update_freq
                    point = geom.interpolate(distance_traveled)
                    gps_data['latitude'] = round(point.y, 3)
                    gps_data['longitude'] = round(point.x, 3)
                    gps_data['speed'] = random.uniform(10, speed_limit)
                    gps_data['status'] = DriveStatus.MOVING.value
                    yield gps_data
                    
        # Yield a message or the last point to indicate the end of the route
        last_point = row['geometry'].coords[-1] if isinstance(row['geometry'], LineString) else (geom.y, geom.x)
        gps_data['status'] = DriveStatus.DESTINATION_REACHED.value
        gps_data['speed'] = 0 # assume the driver is stopping once reached the destination
        gps_data['latitude'] = round(last_point[1], 3)
        gps_data['longitude'] = round(last_point[0], 3)
        yield gps_data 

