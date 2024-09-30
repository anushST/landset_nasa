from pystac_client import Client
from pprint import pprint

def BuildSquare(lon, lat, delta):
    c1 = [lon + delta, lat + delta]
    c2 = [lon + delta, lat - delta]
    c3 = [lon - delta, lat - delta]
    c4 = [lon - delta, lat + delta]
    geometry = {"type": "Polygon", "coordinates": [[ c1, c2, c3, c4, c1 ]]}
    return geometry

# for item in Landsat_items:
#     scene_id = item.get('id')  # Извлекаем имя сцены
#     scene_datetime = item.get('properties', {}).get('datetime')  # Извлекаем время съёмки
#     print(f"Scene ID: {scene_id}, Date and Time: {scene_datetime}")


def get_landsat_items(lon, lat, time_range, min_cloud=0, max_cloud=100):
    LandsatSTAC = Client.open("https://landsatlook.usgs.gov/stac-server",
                              headers=[])
    geometry = BuildSquare(lon, lat, 0.04)
    landsat_search = LandsatSTAC.search(
        intersects=geometry,
        datetime=time_range,
        query={
            'eo:cloud_cover': {
                'gte': min_cloud,
                'lte': max_cloud,
            }
        },
        collections=["landsat-c2l2-sr"]
    )
    landsat_items = [i.to_dict() for i in landsat_search.get_items()]
    return landsat_items


def dict_to_string(data_dict):
    """Convert dictionary (including nested lists/dicts) to a single formatted string."""
    
    def recursive_format(d, indent=0):
        """Helper function to format the dictionary recursively."""
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                # Если значение - это словарь, рекурсивно вызываем функцию
                lines.append(" " * indent + f"{key}:")
                lines.append(recursive_format(value, indent + 2))  # Увеличиваем отступ
            elif isinstance(value, list):
                # Если значение - это список, форматируем каждый элемент
                lines.append(" " * indent + f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(recursive_format(item, indent + 2))
                    else:
                        lines.append(" " * (indent + 2) + str(item))
            else:
                # Если это обычное значение, добавляем его
                lines.append(" " * indent + f"{key}: {value}")
        return "\n".join(lines)

    return recursive_format(data_dict)
