import uvicorn as uvicorn
import requests
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import StreamingResponse
from utils import make_tail, make_head, get_catalogs_wb, parser, parse_card
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


@app.get('/get-seller-data/{seller_article}/')
async def get_seller(seller_article):
    data = {
        'seller_article': int(seller_article)
    }
    url1 = f'https://www.wildberries.ru/webapi/seller/data/short/{seller_article}'
    response1 = requests.get(url1).text
    check_seller = json.loads(response1)
    is_unknown = check_seller.get('isUnknown')
    data['seller_info'] = json.loads(response1) if not is_unknown else f"Seller under article {seller_article} does not exist"

    url2 = f'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-2162196,-1257786&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&reg=1&regions=80,64,83,4,38,33,70,82,69,68,86,75,30,40,48,1,22,66,31,71&spp=28&sppFixGeo=4&supplier={seller_article}'
    data['sellers_products'] = json.loads(requests.get(url2).text)

    return data


@app.get('/get-all-categories/')
async def get_cats():
    return get_catalogs_wb()


@app.post('/products-filtering/')
async def get_data(request: Request, category_url, price_ot, price_do):
    try:
        price_ot = int(price_ot)
        price_do = int(price_do)
        url = f'https://www.wildberries.ru{category_url}'
        data_list = await parser(url, low_price=price_ot, top_price=price_do)

        df = pd.DataFrame(data_list)
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()
        return StreamingResponse(io.BytesIO(output.getvalue()), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename="filtered_data.xlsx"'})
    except Exception as e:
        return {'Ошибка': f'{e}'}


"""
returning xlsx file
@app.get("/payments/xlsx", response_description='xlsx')
async def payments():
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'ISBN')
    worksheet.write(0, 1, 'Name')
    worksheet.write(0, 2, 'Takedown date')
    worksheet.write(0, 3, 'Last updated')
    workbook.close()
    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="lol.xlsx"'
    }
    return StreamingResponse(output, headers=headers)
"""

if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
