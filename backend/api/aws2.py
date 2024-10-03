import asyncio
import aioredis
import aiohttp
import json
from pprint import pprint
from datetime import datetime

# Создание полигона для поиска
def BuildSquare(lon, lat, delta):
    c1 = [lon + delta, lat + delta]
    c2 = [lon + delta, lat - delta]
    c3 = [lon - delta, lat - delta]
    c4 = [lon - delta, lat + delta]
    geometry = {"type": "Polygon", "coordinates": [[c1, c2, c3, c4, c1]]}
    return geometry

def convert_to_rfc3339(date_str):
    dates = date_str.split('/')
    extra_part = 'T00:00:00Z'
    return f'{dates[0]}{extra_part}/{dates[1]}{extra_part}'

# Асинхронная функция для поиска по STAC API
async def get_landsat_items(lon, lat, time_range, min_cloud=0, max_cloud=100):
    url = "https://landsatlook.usgs.gov/stac-server/search"
    geometry = BuildSquare(lon, lat, 0.004)
    payload = {
        "intersects": geometry,
        "datetime": convert_to_rfc3339(time_range),
        "query": {
            "eo:cloud_cover": {
                "gte": min_cloud,
                "lte": max_cloud,
            }
        },
        "collections": ["landsat-c2l2-sr"]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["features"]
            else:
                print(f"Ошибка: {response.status}")
                return None

async def worker(redis: aioredis.Redis):
    while True:
        # Проверяем Redis на наличие нового запроса
        request_data = await redis.lpop('request_queue')
        if request_data:
            # Извлекаем параметры запроса
            request = json.loads(request_data)
            print(request)
            request_id = request['request_id']
            lon = request['lon']
            lat = request['lat']
            min_cloud = int(request['min_cloud'])
            max_cloud = int(request['max_cloud'])
            time_range = request['time_range']

            # Выполняем запрос к STAC API
            items = await get_landsat_items(lon, lat, time_range, min_cloud, max_cloud)

            await redis.set(f"result:{request_id}", json.dumps(items), ex=120)

            print('done')

        await asyncio.sleep(1)

async def main():
    redis = await aioredis.from_url("redis://redis:6379/0")
    await worker(redis)

if __name__ == "__main__":
    asyncio.run(main())
