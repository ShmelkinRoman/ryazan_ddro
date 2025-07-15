import math

multiplier = 10 ** 3
latitude = math.floor(54.034082 * multiplier) / multiplier
longitude = math.floor(24.078567 * multiplier) / multiplier
params = {
    'lat': latitude,
    'lng': longitude
}

print(params)
