import openmeteo_requests
import requests_cache
from retry_requests import retry


class Open_Meteo_API:

	'''
	Weather codes table, from Open-Meteo Docs

	Code		 |	Description
	--------------------------------------------------------------
	0			 |	Clear sky
	1, 2, 3		 |	Mainly clear, partly cloudy, and overcast
	45, 48		 |	Fog and depositing rime fog
	51, 53, 55	 |	Drizzle: Light, moderate, and dense intensity
	56, 57		 |	Freezing Drizzle: Light and dense intensity
	61, 63, 65	 |	Rain: Slight, moderate and heavy intensity
	66, 67		 |	Freezing Rain: Light and heavy intensity
	71, 73, 75	 |	Snow fall: Slight, moderate, and heavy intensity
	77			 |	Snow grains
	80, 81, 82	 |	Rain showers: Slight, moderate, and violent
	85, 86		 |	Snow showers slight and heavy
	95 *		 |	Thunderstorm: Slight or moderate
	96, 99 *	 |	Thunderstorm with slight and heavy hail

	'''

	def __init__(self, meteo_configs:dict):
		# Setup the Open-Meteo API client with cache and retry on error
		self.open_meteo_configs = meteo_configs
		self._cache_session = requests_cache.CachedSession('.cache', 
								expire_after = self.open_meteo_configs['expire_after'])
		self._retry_session = retry(self._cache_session, retries = self.open_meteo_configs['retries'], 
								backoff_factor = self.open_meteo_configs['backoff_factor'])
		self.openMeteoApi = openmeteo_requests.Client(session = self._retry_session)
	
	def get_current_weather(self, latitude:float, longitude:float) -> dict:
		params = {
			'latitude':latitude,
			'longitude':longitude,
			'current':self.open_meteo_configs['metrics'],
			'forecast_days': self.open_meteo_configs['forecast_days'],
		}
		responses = self.openMeteoApi.weather_api(self.open_meteo_configs['url'], params=params)
		return self.process_weather_responses(responses)

	def process_weather_responses(self, responses:list) -> dict:
		# Process first location. Add a for-loop for multiple locations or weather models
		response = responses[0]
		# Process hourly data. The order of variables needs to be the same as requested.
		current_weather_response = response.Current()
		current_weather_dict_data = {
			'latitude':response.Latitude(),
			'longitude':response.Longitude(),
		}
		for i, val in enumerate(self.open_meteo_configs['metrics']):
			current_weather_dict_data[val] = round(current_weather_response.Variables(i).Value(), 2)
					
		return current_weather_dict_data
