import requests
import json
import pandas as pd
template = '/vol{vol}/part{part}/{article}/info/'
head = 'https://basket-0{i}.wb.ru'


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
                except:
                    # print(f'не имеет дочерних каталогов *{i["name"]}*')
                    continue
        except:
            # print(f'не имеет дочерних каталогов *{d["name"]}*')
            continue
    return data_list


def search_category_in_catalog(url, catalog_list):
    """пишем проверку пользовательской ссылки на наличии в каталоге"""
    try:
        for catalog in catalog_list:
            if catalog['category_url'] == url.split('https://www.wildberries.ru')[-1]:
                print(f'найдено совпадение: {catalog["category_name"]}')
                name_category = catalog['category_name']
                shard = catalog['shard']
                query = catalog['query']
                return name_category, shard, query
            else:
                # print('нет совпадения')
                pass
    except:
        print('Данный раздел не найден!')


def get_data_from_json(json_file):
    """извлекаем из json интересующие нас данные"""
    data_list = []
    for data in json_file['data']['products']:
        try:
            price = int(data["priceU"] / 100)
        except:
            price = 0
        data_list.append({
            'Наименование': data['name'],
            'id': data['id'],
            'Скидка': data['sale'],
            'Цена': price,
            'Цена со скидкой': int(data["salePriceU"] / 100),
            'Бренд': data['brand'],
            'id бренда': int(data['brandId']),
            'feedbacks': data['feedbacks'],
            'rating': data['rating'],
            'Ссылка': f'https://www.wildberries.ru/catalog/{data["id"]}/detail.aspx?targetUrl=BP'
        })
    return data_list


def get_content(shard, query, low_price=None, top_price=None):
    # вставляем ценовые рамки для уменьшения выдачи, вилбериес отдает только 100 страниц
    headers = {'Accept': "*/*", 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    data_list = []
    for page in range(1, 101):
        print(f'Сбор позиций со страницы {page} из 100')
        # url = f'https://wbxcatalog-ru.wildberries.ru/{shard}' \
        #       f'/catalog?appType=1&curr=rub&dest=-1029256,-102269,-1278703,-1255563' \
        #       f'&{query}&lang=ru&locale=ru&sort=sale&page={page}' \
        #       f'&priceU={low_price * 100};{top_price * 100}'
        url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub&dest=-1075831,-77677,-398551,12358499' \
              f'&locale=ru&page={page}&priceU={low_price * 100};{top_price * 100}' \
              f'&reg=0&regions=64,83,4,38,80,33,70,82,86,30,69,1,48,22,66,31,40&sort=popular&spp=0&{query}'
        r = requests.get(url, headers=headers)
        data = r.json()
        print(f'Добавлено позиций: {len(get_data_from_json(data))}')
        if len(get_data_from_json(data)) > 0:
            data_list.extend(get_data_from_json(data))
        else:
            print(f'Сбор данных завершен.')
            break
    return data_list


def save_excel(data, filename):
    """сохранение результата в excel файл"""
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'temporary_files/{filename}.xlsx')
    df.to_excel(writer, 'data')
    writer.save()
    print(f'Все сохранено в {filename}.xlsx')


def parser(url, low_price, top_price):
    # получаем список каталогов
    catalog_list = get_catalogs_wb()
    try:
        name_category, shard, query = search_category_in_catalog(url=url, catalog_list=catalog_list)
        data_list = get_content(shard=shard, query=query, low_price=low_price, top_price=top_price)
        file_name = f'{name_category}_from_{low_price}_to_{top_price}'
        return data_list, file_name + '.xlsx'
    except TypeError:
        print('Ошибка! Возможно не верно указан раздел. Удалите все доп фильтры с ссылки')
    except PermissionError:
        print('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')

