import datetime as dt
import re
import csv

from bs4 import BeautifulSoup
from urllib.request import urlopen


class WebsiteScraper:
    def scrape_weather_data(self) -> list[dict]:
        html = urlopen('https://ddro.ru/meteo/')
        bs = BeautifulSoup(html.read(), 'html.parser')
        main_tag = bs.find('main')
        weather_report_arr = []
        if main_tag:
            for child in main_tag.children:
                if child.name == 'div':
                    weather_report = {}
                    data_string = child.get_text()
                    try:
                        # Попробовать взять первые 4 цифры в строке.
                        weather_report['ddro_station_id'] = re.match(r'^\n(\d{4})\s+', data_string).group(1)
                    except AttributeError:
                        weather_report['ddro_station_id'] = '0000'
                    weather_report['ddro_station_name'] = re.match(r'^\n(.*)\n', data_string).group(1)
                    weather_report['latitude'] = re.search(r'([0-9.]{2,}),\s+([0-9.]{6,})', data_string).group(1) 
                    weather_report['longitude'] = re.search(r'([0-9.]{2,}),\s+([0-9.]{6,})', data_string).group(2)
                    weather_report['local'] = re.search(r'Время снятия показаний:\s(\d{1,}[./-]\d{1,}[./-]\d{2,4}\s\d{1,2}:\d{1,2}:\d{1,2})', child.get_text()).group(1)
                    weather_report['precipitation_type'] = re.search(r'Осадки:\s(.*)\n', data_string).group(1)
                    weather_report['surface_cond'] = re.search(r'Поверхность:\s(.*)\n', data_string).group(1)
                    weather_report['friction_coeff'] = re.search(r'Коэфициент трения:\s(.*)\n', data_string).group(1)
                    weather_report['humidity'] = re.search(r'Относительная влажность:\s(.*)%\n', data_string).group(1)
                    weather_report['pressure'] = re.search(r'Атмосферное давление:\s(.*)\sгПа\n', data_string).group(1)
                    weather_report['temperature_air'] = re.search(r'Температура воздуха:\s(.*)°C\n', data_string).group(1)
                    weather_report['dew_point'] = re.search(r'Точка росы:\s(.*)°C\n', data_string).group(1)
                    weather_report['surface_temp'] = re.search(r'Температура поверхности дороги:\s(.*)°C\n', data_string).group(1)
                    weather_report['water_layer_thickness'] = re.search(r'Высота слоя воды:\s(.*)мм\n', data_string).group(1)
                    weather_report['snow_layer_thickness'] = re.search(r'Высота слоя снега:\s(.*)мм\n', data_string).group(1)
                    weather_report['ice_layer_thickness'] = re.search(r'Высота слоя льда:\s(.*)мм\n', data_string).group(1)
                    weather_report['ice_percentage'] = re.search(r'Процент льда:\s(.*)мм\n', data_string).group(1)
                    weather_report['wind_m_s_avg'] = re.search(r'Скорость ветра:\s(\d+.*\d*)\n', data_string).group(1)
                    weather_report['wind_degree'] = re.search(r'Направление ветра:\s(.*)°\n', data_string).group(1)
                    weather_report['precipitation_amount'] = re.search(r'Интенсивность осадков:\s(.*)мм/ч\n', data_string).group(1)
                    weather_report['precipitation_delta'] = re.search(r'Прибавление количества осадков по сравнению с предыдущим измерением:\s(.*)мм\n', data_string).group(1)

                else:
                    continue

                # Проверка давления. Если давление = 0,
                # все данные этого отчета неактульны.
                if weather_report['pressure'] != '0':
                    weather_report_arr.append(weather_report)
        return weather_report_arr

    def write_station_data_csv(self) -> None:
        weather_report_arr = self.scrape_weather_data()
        data_array = []
        data_array.append(['ddro_station_id', 'ddro_ddro_station_name', 'latitude', 'longitude'])
        for weather_report in weather_report_arr:
            data_array.append([
                weather_report['ddro_station_id'], weather_report['ddro_station_name'],
                float(weather_report['latitude']), float(weather_report['longitude'])]
            )

        csv_file_path = 'ddro_station_data' + '_' + dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + '.csv'
        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(data_array)


if __name__ == '__main__':
    service = WebsiteScraper()
    # weather_report_arr = service.scrape_weather_data()
    service.write_station_data_csv()
    # print('weather_report_arr =', weather_report_arr)
