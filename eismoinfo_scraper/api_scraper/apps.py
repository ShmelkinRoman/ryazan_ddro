from django.apps import AppConfig


class ApiScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_scraper'

    def ready(self):
        import api_scraper.stations
        import api_scraper.weather_data_service
