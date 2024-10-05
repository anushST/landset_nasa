import rasterio
from rasterio.session import AWSSession
import boto3
from pyproj import Transformer

# Создаем сессию AWS
session = boto3.Session(
    aws_access_key_id='AKIASU566JJ76QADZGA4',
    aws_secret_access_key='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',
    region_name='us-west-2'
)

# Открываем сессию для работы с S3
aws_session = AWSSession(session, requester_pays=True)

def get_product_info(product_id: str):
    parts = product_id.split('_')
    path = parts[2][:-3]
    row = parts[2][3:]
    year = parts[3][:-4]

    return {'path': path, 'row': row, 'year': year}

def get_scene_data(product_id, lat, lon):
    product_info = get_product_info(product_id)
    cog_url = ('s3://usgs-landsat/collection02/level-2/standard/oli-tirs/'
               f'{product_info["year"]}/{product_info["path"]}/{product_info["row"]}/'
               f'{product_id}/')
    
    file_endings = [
        # '_ANG.txt',
        # '_MTL.json',
        # '_MTL.txt',
        # '_MTL.xml',
        '_QA_PIXEL.TIF',
        '_QA_RADSAT.TIF',
        '_SR_B1.TIF',
        '_SR_B2.TIF',
        '_SR_B3.TIF',
        '_SR_B4.TIF',
        '_SR_B5.TIF',
        '_SR_B6.TIF',
        '_SR_B7.TIF',
        '_SR_QA_AEROSOL.TIF',
        # '_SR_stac.json',
        '_ST_ATRAN.TIF',
        '_ST_B10.TIF',
        '_ST_CDIST.TIF',
        '_ST_DRAD.TIF',
        '_ST_EMIS.TIF',
        '_ST_EMSD.TIF',
        '_ST_QA.TIF',
        '_ST_TRAD.TIF',
        '_ST_URAD.TIF',
        # '_ST_stac.json',
    ]

    output = {}
    with rasterio.Env(aws_session):
        for file in file_endings:
            url = cog_url + product_id + file + '/'
            with rasterio.open(url) as dataset:
                img_crs = dataset.crs
                transformer = Transformer.from_crs("EPSG:4326", img_crs, always_xy=True)
                x, y = transformer.transform(lon, lat)
                row, col = dataset.index(x, y)
                pixel_value = dataset.read(1, window=rasterio.windows.Window(col, row, 1, 1))
                key = file[1:-4]
                output[key] = {
                    'row': row, 'col': col, 'pixel_value': pixel_value,
                }

print(get_scene_data('LC08_L2SP_154033_20240924_20240928_02_T1', 38.5548, 68.7659))
