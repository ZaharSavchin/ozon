import json
import re

import requests
from aiogram import Bot
from aiogram.enums import ParseMode

from config_data.config import Config, load_config
from database.database import url_images, save_url_images, users_items, save_users_items
import aiohttp
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

API_URL: str = 'https://api.telegram.org/bot'
config: Config = load_config()
BOT_TOKEN = config.tg_bot.token
bot = Bot(token=BOT_TOKEN, parse_mode='HTML')


async def get_item(item_id):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    url_ = f'https://api.ozon.ru/composer-api.bx/page/json/v2?url=/product/{item_id}'
    response = requests.get(url_, headers=headers)
    content = response.json()
    # print(json.dumps(content, indent=4, ensure_ascii=False))
    return content
    # url_ozon_last = f'https://ozon.by/product/{item_id}'
    # response = requests.get(url=url_ozon_last)
    # data = response.text
    # match = re.search(r'<script type="application/ld\+json">(.+?)</script>', data)
    # if match:
    #     json_str = match.group(1)
    #     data = json.loads(json_str)
    #     return data


# async def get_item_details(response):
#     item_details = (response.get('data', {})).get('products', None)[0]
#     return item_details


async def prepare_item(item_id, content):
    if len(content) > 0:

        try:
            dict_ = content['trackingPayloads']
            for k, v in dict_.items():
                res = json.loads(v)
                brand = res["brandName"]
        except Exception:
            brand = None

        try:
            dict_ = content['trackingPayloads']
            for k, v in dict_.items():
                res = json.loads(v)
                link = res["currentPageUrl"]
        except Exception:
            link = None

        dict_ = content['seo']['script'][0]
        for k, v in dict_.items():
            res = json.loads(v)
            price = float(res["offers"]["price"])
            cur = res["offers"]["priceCurrency"]
            name = res["name"]
            break

        return (f"артикул: {item_id}\n"
                f'brand: {brand}\n'
                f'название: {name}\n'
                f'цена: {price} {cur}\n'
                f'ссылка: {link}\n')
        # brand = data['brand']
        # name = data['name']
        # price = data['offers']['price']
        # price_currency = data['offers']['priceCurrency']
        # link = data['offers']['url']
        # return (f"артикул: {item_id}\n"
        #         f"брэнд: {brand}\n"
        #         f"название: {name}\n"
        #         f"цена: {price} {price_currency}\n"
        #         f"ссылка: {link}")


async def get_name(item_id):
    content = await get_item(item_id)
    dict_ = content['seo']['script'][0]
    for k, v in dict_.items():
        res = json.loads(v)
        name = res["name"]
        break
    return name


async def get_price(item_id):
    content = await get_item(item_id)
    dict_ = content['seo']['script'][0]
    for k, v in dict_.items():
        res = json.loads(v)
        price = float(res["offers"]["price"])
        break
    return price


async def search_image(content):
    try:
        image = content['seo']['meta'][3]['content']
    except Exception:
        image = None
    return image


class DeleteCallbackFactory(CallbackData, prefix='id_article'):
    user_id: int
    item_id: int


async def main_search(item_id, user_id, data=None):
    try:
        if data is None:
            data = await get_item(item_id)
        message = await prepare_item(item_id, data)
    except Exception:
        await bot.send_message(chat_id=user_id, text="По этому артикулу ничего не найдено!")
        return None

    dict_ = data['seo']['script'][0]
    for k, v in dict_.items():
        res = json.loads(v)
        price_int = float(res["offers"]["price"])
        name = res["name"]
        break
    users_items[user_id][1][item_id] = price_int
    await save_users_items()

    image_url = await search_image(data)

    button = InlineKeyboardButton(text=f"Удалить: '{name}'",
                                  callback_data=DeleteCallbackFactory(user_id=user_id,
                                                                      item_id=item_id).pack())
    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
    # if image_url:
    # message_with_image = f'{message}\n<a href="{image_url}">&#8203;</a>'
    # await bot.send_message(chat_id=user_id, text=message_with_image, parse_mode=ParseMode.HTML, reply_markup=markup)
    try:
        await bot.send_photo(chat_id=user_id, photo=image_url, caption=message, reply_markup=markup)
    except Exception as err:
        message_with_image = f'{message}\n<a href="{image_url}">&#8203;</a>'
        await bot.send_message(chat_id=user_id, text=message_with_image, parse_mode=ParseMode.HTML, reply_markup=markup)

    # else:
    #     await bot.send_message(chat_id=user_id, text=message, reply_markup=markup)

