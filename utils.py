import asyncio
import aiohttp
import requests
import json
import pandas as pd
from time import perf_counter
from cats import categories

template = '/vol{vol}/part{part}/{article}/info/'
head = 'https://basket-0{i}.wb.ru'


async def parse_card(article):
    data = {
        'article': int(article),
    }
    head = make_head(int(article))
    tail = make_tail(str(article), 'ru/card.json')

    url1 = head + tail
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url1) as response1:
            data['card'] = json.loads(await response1.text()) if response1.status == 200 else f'{article} does not exist'

        url2 = f'https://card.wb.ru/cards/detail?spp=28&regions=80,64,83,4,38,33,70,82,69,68,86,75,30,40,48,1,22,66,31,71&pricemarginCoeff=1.0&reg=1&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&sppFixGeo=4&dest=-1029256,-102269,-2162196,-1257786&nm={article}'
        async with session.get(url=url2) as response2:
            data['detail1'] = json.loads(await response2.text()) if response2.status == 200 else f'{article} does not exist'
    return {"article": data}


def make_head(article: int):
    global head
    if article < 14400000:
        number = 1
    elif article < 28800000:
        number = 2
    elif article < 43500000:
        number = 3
    elif article < 72000000:
        number = 4
    elif article < 100800000:
        number = 5
    elif article < 106300000:
        number = 6
    elif article < 111600000:
        number = 7
    elif article < 117000000:
        number = 8
    elif article < 131400000:
        number = 9
    else:
        number = 10
    return head.format(i=number)


def make_tail(article: str, item: str):
    length = len(article)
    global template
    if length <= 3:
        return template.format(vol=0, part=0, article=article) + item
    elif length == 4:
        args = {
            'vol': 0,
            'part': article[0],
            'article': article
        }
        return template.format(**args) + item
    elif length == 5:
        args = {
            'vol': 0,
            'part': article[:2],
            'article': article
        }
        return template.format(**args) + item
    elif length == 6:
        args = {
            'vol': article[0],
            'part': article[:3],
            'article': article
        }
        return template.format(**args) + item
    elif length == 7:
        args = {
            'vol': article[:2],
            'part': article[:4],
            'article': article
        }
        return template.format(**args) + item
    elif length == 8:
        args = {
            'vol': article[:3],
            'part': article[:5],
            'article': article
        }
        return template.format(**args) + item
    elif length == 9:
        args = {
            'vol': article[:4],
            'part': article[:6],
            'article': article
        }
        return template.format(**args) + item


def get_catalogs_wb():
    """получение каталога вб"""
    url = 'https://www.wildberries.ru/webapi/menu/main-menu-ru-ru.json'
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url)
    data = response.json()
    data_list = []
    for d in data:
        try:
            for child in d['childs']:
                try:
                    category_name = child['name']
                    category_url = child['url']
                    shard = child['shard']
                    query = child['query']
                    data_list.append({
                        'category_name': category_name,
                        'category_url': category_url,
                        'shard': shard,
                        'query': query})
                except:
                    continue
                try:
                    for sub_child in child['childs']:
                        category_name = sub_child['name']
                        category_url = sub_child['url']
                        shard = sub_child['shard']
                        query = sub_child['query']
                        data_list.append({
                            'category_name': category_name,
                            'category_url': category_url,
                            'shard': shard,
                            'query': query})
                        try:
                            for sub_sub_child in sub_child['childs']:
                                category_name = sub_sub_child['name']
                                category_url = sub_sub_child['url']
                                shard = sub_sub_child['shard']
                                query = sub_sub_child['query']
                                data_list.append({
                                    'category_name': category_name,
                                    'category_url': category_url,
                                    'shard': shard,
                                    'query': query})
                        except:
                            continue
                except:
                    continue
        except:
            continue
    return data_list


def search_category_in_catalog(url, catalog_list):
    try:
        for catalog in catalog_list:
            if catalog['category_url'] == url.split('https://www.wildberries.ru')[-1]:
                name_category = catalog['category_name']
                shard = catalog['shard']
                query = catalog['query']
                return name_category, shard, query
            else:
                pass
    except:
        print('Данный раздел не найден!')


async def get_data_from_json(data):
    try:
        price = int(data["priceU"] / 100)
    except:
        price = 0
    article = data['id']
    head = make_head(int(article))
    url1 = head + make_tail(str(article), 'ru/card.json')
    url2 = head + make_tail(str(article), 'sellers.json')

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url1) as response1:
            card = json.loads(await response1.text()) if response1.status == 200 else None

    compositions = card.get('compositions', None)

    seller = card.get('selling', None)
    if seller:
        seller = seller.get('supplier_id')

    output_data = {
        'id': article,
        'Наименование': data.get('name', None),
        'Категория(subj_root_name)': card.get('subj_root_name', None),
        'Подкатегория(subj_name)': card.get('subj_name', None),
        'Вид Категории(imt_name)': card.get('imt_name', None),
        'Вендор Код(vendor_code)': card.get('vendor_code', None),
        'Цвет (color)': card.get('nm_colors_names', None),
        'seller_id': seller,
        'sale': data.get('sale', None),
        'Цена': price,
        'Цена со скидкой': int(data["salePriceU"] / 100),
        'Бренд': data.get('brand', None),
        'id бренда': int(data.get('brandId', False)),
        'season': card.get('season', None),
        'Фото(pics)': int(data.get('pics', False)),
        'Пол(kinds)': card.get('kinds', None),
        'feedbacks': data.get('feedbacks', None),
        'rating': data.get('rating', None),
        'compositions': [item['name'] for item in compositions] if compositions is not None else None,
        'Ссылка': f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=BP'
    }
    option_list = ['Ширина упаковки', 'Высота упаковки', 'Длина упаковки', 'Страна производства', 'ТНВЭД']
    options = card.get('options', None)
    if options:
        for option in options:
            name = option['name']
            if name in option_list:
                output_data.update({name: option['value']})
    return output_data


async def get_data_from_json2(data):
    try:
        price = int(data["priceU"] / 100)
    except:
        price = 0
    article = data['id']

    output_data = {
        'id': article,
        'Наименование': data.get('name', None),
        'sale': data.get('sale', None),
        'Цена': price,
        'Цена со скидкой': int(data["salePriceU"] / 100),
        'Бренд': data.get('brand', None),
        'id бренда': int(data.get('brandId', False)),
        'Фото(pics)': int(data.get('pics', False)),
        'feedbacks': data.get('feedbacks', None),
        'rating': data.get('rating', None),
        'Ссылка': f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=BP'
    }

    return output_data


async def get_page_content(url):
    tasks = []
    data_list = []
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = json.loads(await response.text())
            for item in data['data']['products']:
                task = asyncio.create_task(get_data_from_json(item))
                tasks.append(task)

            curr_list = await asyncio.gather(*tasks, return_exceptions=True)

            curr_list = [item for item in curr_list if not isinstance(item, Exception)]
            data_list.extend(curr_list)
            curr_list = []
            tasks = []
            return data_list


async def get_page_content2(url):
    tasks = []
    data_list = []
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = json.loads(await response.text())
            for item in data['data']['products']:
                task = asyncio.create_task(get_data_from_json2(item))
                tasks.append(task)

            curr_list = await asyncio.gather(*tasks, return_exceptions=True)

            curr_list = [item for item in curr_list if not isinstance(item, Exception)]
            data_list.extend(curr_list)
            curr_list = []
            tasks = []
            return data_list


async def get_content_catalog(shard, query, low_price=None, top_price=None):
    data_list = []
    for page in range(1, 101):
        url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub&dest=-1075831,-77677,-398551,12358499' \
              f'&locale=ru&page={page}&priceU={low_price * 100};{top_price * 100}' \
              f'&reg=0&regions=64,83,4,38,80,33,70,82,86,30,69,1,48,22,66,31,40&sort=popular&spp=0&{query}'
        data_list += await get_page_content(url=url)
    return data_list


async def get_content_catalog2(article):
    data_list = []
    for page in range(1, 101):
        url = f'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-2162196,-1257786'\
              f'&emp=0&lang=ru&locale=ru&page={page}&pricemarginCoeff=1.0&reg=0&regions=80,64,83,4,38,33,70,82,69,68,86,75,30,40,48,1,22,66,31,71'\
                                                                                 f'&sort=popular&spp=0&supplier={article}'
        data_list += await get_page_content2(url=url)
    return data_list


async def parser(category_url, low_price, top_price):
    catalog_list = get_catalogs_wb()
    url = f'https://www.wildberries.ru{category_url}'
    try:
        start = perf_counter()
        name_category, shard, query = search_category_in_catalog(url=url, catalog_list=catalog_list)
        data_list = await get_content_catalog(shard=shard, query=query, low_price=low_price, top_price=top_price)
        end = perf_counter()

        print(f'time {end - start:.8f} sec')
        return data_list
    except TypeError:
        data_list = []
        category_list = [cat for cat in categories if category_url in cat]

        for cat_url in category_list:
            data_list += await parser(category_url=cat_url, low_price=low_price, top_price=top_price)
            print('iteration of ', cat_url)
        return data_list
    except PermissionError:
        print('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')
