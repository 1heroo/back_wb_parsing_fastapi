import asyncio
import csv

import aiohttp
import json
import sys
from utils import make_tail, make_head



async def get_seller_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response1:
            #try:          
            card_id = json.loads(await response1.text())['data']['products'][0].get('id')
            #except:
             #   return {}
            
        head = make_head(int(card_id))
        url1 = head + make_tail(str(card_id), 'sellers.json')
        async with session.get(url1) as response2:
            json_data = json.loads(await response2.text())

    
    return json_data


async def main(start, stop):
    tasks = []
    articles = []
    url = 'https://catalog.wb.ru/sellers/catalog?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-2162196,-1257786&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&reg=0&regions=80,64,83,4,38,33,70,69,86,75,30,40,48,1,22,66,31,68,71&spp=0&supplier={article}'
    data = []
    for index in range(start, stop):
        with open(f'../sellers/sellers/sellers_{index}000.txt', 'r') as file:
            articles += file.read() \
                .replace("'", '') \
                .replace('[', '') \
                .replace(']', '') \
                .split(',')
        print(index)
        for article in articles:
            print(article)
            tasks.append(asyncio.create_task(get_seller_data(url.format(article=article))))
        result = await asyncio.gather(*tasks)
        result = [seller for seller in result if not isinstance(seller, Exception)]
        data += result
        tasks = []
        articles = []
    import pandas
    df = pandas.DataFrame(data)
    df.to_csv('seller_inn.csv')


if __name__ == '__main__':
    prg, start, stop = sys.argv
    start, stop = int(start), int(stop)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(start, stop))
