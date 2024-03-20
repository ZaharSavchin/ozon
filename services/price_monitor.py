import json

from database.database import users_items, save_users_items
from services.search_function import get_price, main_search, bot, get_item
import asyncio
from config_data.config import admin_id


async def monitoring(loops):
    loop_counter = 0
    while True:
        for user_id, list_of_items in users_items.copy().items():
            if len(list_of_items[1]) > 0:
                for item_id, price in list_of_items[1].items():
                    try:
                        # actual_price = await get_price(list_of_items[0], item_id)
                        # actual_price_float = actual_price.pop()
                        content = await get_item(item_id=item_id)
                        dict_ = content['seo']['script'][0]
                        for k, v in dict_.items():
                            res = json.loads(v)
                            actual_price = float(res["offers"]["price"])
                            name = res["name"]
                            break
                        if actual_price < price and actual_price > 0:
                            try:
                                sale = price - actual_price
                                await bot.send_message(chat_id=user_id, text=f"цена товара '{name}' (Артикул: {item_id})"
                                                                             f" снизилась на {round(sale, 2)} "
                                                                             f"{list_of_items[0]}")
                                await main_search(item_id, user_id, data=content)
                            except Exception as error:
                                print(error)
                        if actual_price == 0:
                            await bot.send_message(chat_id=admin_id, text='пауза 40мин')
                            await asyncio.sleep(2400)
                    except Exception as e:
                        print(e)
                    await asyncio.sleep(5)
            await asyncio.sleep(5)
        loop_counter += 1
        if loop_counter % loops == 0 or loop_counter == 1:
            await bot.send_message(chat_id=admin_id, text=f"{loop_counter}", disable_notification=True)
        await asyncio.sleep(5)

