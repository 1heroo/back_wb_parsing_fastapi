import time
from time import sleep

import aiohttp
import uvicorn as uvicorn
import requests
from fastapi import FastAPI
from starlette.responses import StreamingResponse
from utils import make_tail, make_head, get_catalogs_wb, parser, parse_card, get_content_catalog2, get_content_catalog
import random
import json
import io
import xlsxwriter
import pandas as pd


app = FastAPI()


@app.get("/products/{article}/")
async def read_item(article):
    data = await parse_card(article)
    data['timestamp'] = float(random.randrange(1669548322, 1669631381))
    return {"article": data}


@app.get("/price_history/{article}/")
async def price(article):
    url = make_head(int(article)) + make_tail(str(article), 'price-history.json')
    response = requests.get(url)
    data = {
        'article': int(article),
        'history': json.loads(response.text) if response.status_code == 200 else 'No changes in price or card does not exist'
        }
    return {f'{article}': data}


# @app.get('/get-seller-data/{seller_article}/')
async def get_seller(seller_article):
    data = {
        'seller_article': int(seller_article)
    }
    url1 = f'https://www.wildberries.ru/webapi/seller/data/short/{seller_article}'
    response1 = requests.get(url1).text
    check_seller = json.loads(response1)
    is_unknown = check_seller.get('isUnknown')
    data['seller_info'] = json.loads(response1) if not is_unknown else f"Seller under article {seller_article} does not exist"

    seller_products = []
    url2 = f'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-2162196,-1257786&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&reg=1&regions=80,64,83,4,38,33,70,82,69,68,86,75,30,40,48,1,22,66,31,71&spp=28&sppFixGeo=4&supplier={seller_article}'
    seller_products += [json.loads(requests.get(url2).text)]

    return data


@app.get('/get-all-categories/')
async def get_cats():
    return get_catalogs_wb()


@app.post('/products-filtering/')
async def get_data(category_url, price_ot, price_do, vendor_code=None, country=None):
    price_ot = int(price_ot)
    price_do = int(price_do)
    data_list = await parser(category_url, low_price=price_ot, top_price=price_do)
    data = pd.DataFrame(data_list)
    # filter = (data['Цена со скидкой'] > price_ot) & (data['Цена со скидкой'] < price_do)
    # data = data[filter]

    if vendor_code is not None:
        data = data[data['Вендор Код(vendor_code)'] == vendor_code]

    if country is not None:
        data = data[data['Страна производства'] == country]

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer)
    writer.save()
    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': f'attachment; filename="filtered_data.xlsx"'})

@app.post('/get-seller-table-in-excel/')
async def get_seller_cards(seller_id):
    data_list = await get_content_catalog2(seller_id)
    data = pd.DataFrame(data_list)

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer)
    writer.save()
    return StreamingResponse(io.BytesIO(output.getvalue()),
                             media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': f'attachment; filename="filtered_data.xlsx"'})


if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
