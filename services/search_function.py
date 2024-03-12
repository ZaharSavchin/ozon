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
    url_ozon_last = f'https://ozon.by/product/{item_id}'
    response = requests.get(url=url_ozon_last)
    data = response.text
    match = re.search(r'<script type="application/ld\+json">(.+?)</script>', data)
    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        return data


# async def get_item_details(response):
#     item_details = (response.get('data', {})).get('products', None)[0]
#     return item_details


async def prepare_item(item_id, data):
    if len(data) > 0:
        brand = data['brand']
        name = data['name']
        price = data['offers']['price']
        price_currency = data['offers']['priceCurrency']
        link = data['offers']['url']
        return (f"артикул: {item_id}\n"                                                                                                 
                f"брэнд: {brand}\n"
                f"название: {name}\n"
                f"цена: {price} {price_currency}\n"
                f"ссылка: {link}")


async def get_name(item_id):
    data = await get_item(item_id)
    name = data['name']
    return name


async def get_price(item_id):
    data = await get_item(item_id)
    price = float(data['offers']['price'])
    return price


async def search_image(data):
    image = data['image']
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

    image_url = data['image']
    price_int = float(data['offers']['price'])
    users_items[user_id][1][item_id] = price_int
    await save_users_items()

    name = data['name']
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

