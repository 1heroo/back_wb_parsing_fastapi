import asyncio
import requests
import json
import pandas as pd
import aiohttp
import requests
import json
import pandas as pd
from time import perf_counter

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
    else:
        number = 9
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
    response = requests.get(url, headers=headers)
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
                            # print(f'не имеет дочерних каталогов *{j["name"]}*')
                            continue
                except:
                    # print(f'не имеет дочерних каталогов *{i["name"]}*')
                    continue
        except:
            # print(f'не имеет дочерних каталогов *{d["name"]}*')
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


async def get_data_from_json(json_file):
    """извлекаем из json интересующие нас данные"""
    data_list = []
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for data in json_file['data']['products']:
        try:
            price = int(data["priceU"] / 100)
        except:
            price = 0
        article = data['id']
        extra_data = await parse_card(article)
        card = extra_data['article']['card']
        output_data = {
            'id': data['id'],
            'Наименование': data['name'],
            'Категория(subj_root_name)': card['subj_root_name'],
            'Подкатегория(subj_name)': card['subj_name'],
            'Вид Категории(imt_name)': card['imt_name'],
            'Вендор Код(vendor_code)': card['vendor_code'],
            'Цвет (color)': card['nm_colors_names'],
            'sale': data['sale'],
            'Цена': price,
            'Цена со скидкой': int(data["salePriceU"] / 100),
            'Бренд': data['brand'],
            'id бренда': int(data['brandId']),
            'season': card.get('season', None),
            'Фото(pics)': int(data['pics']),
            'Пол(kinds)': card['kinds'],
            'feedbacks': data['feedbacks'],
            'rating': data['rating'],
        }
        option_list = ['Ширина упаковки', 'Высота упаковки', 'Длина упаковки', 'Страна производства', 'ТНВЭД']
        for option in card['options']:
            name = option['name']
            if name in option_list:
                output_data.update({name: option['value']})

        output_data.update({'Ссылка': f'https://www.wildberries.ru/catalog/{data["id"]}/detail.aspx?targetUrl=BP'})
        data_list.append(output_data)
    return data_list
data_list = []


async def get_page_content(page, shard, query, low_price=None, top_price=None):
    global data_list
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    print(f'Сбор позиций со страницы {page} из 100')
    url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub&dest=-1075831,-77677,-398551,12358499' \
          f'&locale=ru&page={page}&priceU={low_price * 100};{top_price * 100}' \
          f'&reg=0&regions=64,83,4,38,80,33,70,82,86,30,69,1,48,22,66,31,40&sort=popular&spp=0&{query}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = json.loads(await response.text())
            get_data = await get_data_from_json(data)
            if len(get_data) > 0:
                data_list.extend(get_data)


async def get_content(shard, query, low_price=None, top_price=None):
    tasks = []
    for page in range(1, 101):
        task = asyncio.create_task(get_page_content(page, shard, query, low_price, top_price))
        tasks.append(task)
    await asyncio.gather(*tasks, return_exceptions=True)
    tasks = []


def save_excel(data, filename):
    """сохранение результата в excel файл"""
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'{filename}.xlsx')
    df.to_excel(writer, 'data')
    writer.save()
    print(f'Все сохранено в {filename}.xlsx')


async def parser(url, low_price, top_price):
    # получаем список каталогов
    catalog_list = get_catalogs_wb()
    global data_list
    try:
        start = perf_counter()
        # поиск введенной категории в общем каталоге
        name_category, shard, query = search_category_in_catalog(url=url, catalog_list=catalog_list)
        # сбор данных в найденном каталоге
        await get_content(shard=shard, query=query, low_price=low_price, top_price=top_price)
        end = perf_counter()
        print(f'time {end - start:.8f} sec')
        return data_list
        # сохранение найденных данных
        # save_excel(data_list, f'{name_category}_from_{low_price}_to_{top_price}')
    except TypeError:
        print('Ошибка! Возможно не верно указан раздел. Удалите все доп фильтры с ссылки')
    except PermissionError:
        print('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')
