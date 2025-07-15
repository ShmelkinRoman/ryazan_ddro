# import time

import aiohttp
import asyncio
import math

from requests import Response

from .loggers import get_logger


logger = get_logger(__name__)


class HttpClient:

    async def make_request(self, url: str, params: dict = None,
                           max_retries=3, backoff_factor=1, logging=True) -> Response | None:
        """
        Makes an asynchronous GET request to the specified
        URL with query parameters and implements a retry mechanism.
        :return: The response object if the request is successful;
        None otherwise.
        """
        async with aiohttp.ClientSession() as session:
            for attempt in range(max_retries + 2):  # 0, 1, 2, 3, 4
                if attempt > max_retries and logging:
                    logger.error(f'Max retries exceeded for url {url}')
                    return None
                try:
                    async with session.get(url=url, params=params) as response:
                        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
                        if response.status == 200:
                            return await response.json()
                        elif response.status < 400:  # 1xx and 3xx
                            logger.error(
                                f'Http request error: '
                                f'recieved informational or redirectional '
                                f'response status code: {response.status}'
                            )
                            raise aiohttp.http_exceptions.HttpProcessingError
                except (
                    aiohttp.ClientError,
                    aiohttp.http_exceptions.HttpProcessingError
                ) as err:
                    logger.error(f'Http request error: {err}')

                    # Calculate wait time using exponential backoff
                    wait_time = backoff_factor * (2 ** attempt)
                    if attempt <= max_retries and logging:
                        logger.info(f'Retrying in {wait_time} seconds...')
                    await asyncio.sleep(wait_time)  # Non-blocking sleep


class WeatherDataHttpClient(HttpClient):
    BASE_URL = 'http://eismoinfo.lt'

    def get_current_weather(self):
        url = f'{self.BASE_URL}/weather-conditions-service/'
        resp = self.make_request(url=url)
        if resp:
            return resp
        logger.error(
            'get_current_weather: max retries exceeded. Request failed.'
            )

    def get_retrospective_weather(self, station_id, number_of_reports):
        url = f'{self.BASE_URL}/weather-conditions-retrospective/'
        params = {
            'id': station_id,
            'number': number_of_reports
        }
        resp = self.make_request(
            url=url, params=params,
            max_retries=15
            )
        if resp:
            return resp
        logger.error(
            f'Station {station_id}: max retries exceeded. Request failed.'
            )


class StationDataHttpClient(HttpClient):
    def fetch_station_height(
            self, station_id, latitude: float, longitude: float
            ):
        url = 'https://elevation.gismeteo.dev/'
        multiplier = 10 ** 3
        latitude = math.floor(latitude * multiplier) / multiplier
        latitude = math.floor(latitude * multiplier) / multiplier
        params = {
            'lat': latitude,
            'lng': longitude
        }
        resp = self.make_request(
            url=url, params=params,
            max_retries=0, logging=False
            )
        if resp:
            return resp
        logger.error(
            f'Station {station_id}: max retries exceeded. Get station height failed.'
        )
        return None
