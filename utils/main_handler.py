from database import search_database, get_available_buildings, get_available_areas
from .gpt_handler import process_users_query
from .other_utils import create_whatsapp_link, organize_by_building
import logging

from loader import bot, proj_settings

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def process_real_estate_query(natural_language_query, user_id: int):
    """
    Основная функция для обработки запроса по недвижимости.

    Args:
        natural_language_query: Запрос пользователя на естественном языке

    Returns:
        dict: Результат поиска с группировкой по зданиям и статусом операции
    """
    logger.info(f"Обработка запроса: {natural_language_query}")

    buildings = get_available_buildings()
    areas = get_available_areas()

    message, arguments = process_users_query(natural_language_query, areas,
                                             buildings)

    if message:
        logger.info(message)

    if arguments:
        purpose = arguments.get('purpose')
        beds = arguments.get("bedroom_count")
        property_type = arguments.get('type')
        area = arguments.get("area")
        building = arguments.get("building")
        view = arguments.get("view")
        price_min = arguments.get('min_price')
        price_max = arguments.get('max_price')
        baths = arguments.get('bath_count')
        sqft_min = arguments.get('sqft')
        sqft_max = None
        furnishing = arguments.get('furnishing')
        completion = arguments.get('completion')
        vacant = arguments.get('vacant')
        handover_date = arguments.get('handover_date')


        logger.info(f"Поиск недвижимости с параметрами: purpose={purpose}, beds={beds}, "
                    f"type={property_type}, price_min={price_min}, price_max={price_max}")
        
        if proj_settings.debug_mode:
            await bot.send_message(chat_id=user_id, text=f"Поиск недвижимости с параметрами: purpose={purpose}, beds={beds}, "
                                                        f"type={property_type}, price_min={price_min}, price_max={price_max}")

        # Шаг 2: Поиск с исходными параметрами
        original_results = search_database(
            purpose = purpose,
            beds=beds,
            property_type=property_type,
            area=area,
            building=building,
            view=view,
            price_min=price_min,
            price_max=price_max,
            baths=baths,
            sqft_min=sqft_min,
            sqft_max=sqft_max,
            furnishing=furnishing,
            completion=completion,
            vacant=vacant,
            handover_date=handover_date,
        )

        # Если найдены результаты, организуем их по зданиям
        if original_results:
            logger.info(f"Найдено {len(original_results)} объектов по исходным параметрам")
            return {
                "status": "success",
                "message": f"Найдено {len(original_results)} объектов по вашему запросу",
                "results": organize_by_building(original_results)
            }

        logger.info("Не найдено объектов по исходным параметрам, увеличиваем цену на 20%")
        await bot.send_message(chat_id=user_id, text="Не найдено объектов по исходным параметрам, увеличиваем цену на 20%")

        # Шаг 3: Если нет результатов, увеличиваем цену на 20% и ищем снова
        if price_max:
            increased_price_max = price_max * 1.2

            logger.info(f"Поиск с увеличенной ценой до {increased_price_max}")

            increased_price_results = search_database(
                purpose = purpose,
                beds=beds,
                property_type=property_type,
                area=area,
                building=building,
                view=view,
                price_min=price_min,
                price_max=increased_price_max,
                baths=baths,
                sqft_min=sqft_min,
                sqft_max=sqft_max,
                furnishing=furnishing,
                completion=completion,
                vacant=vacant,
                handover_date=handover_date,
            )

            # Если найдены результаты с увеличенной ценой, организуем их по зданиям
            if increased_price_results:
                logger.info(f"Найдено {len(increased_price_results)} объектов с увеличенной ценой")
                return {
                    "status": "price_increased",
                    "message": f"Найдено {len(increased_price_results)} объектов с увеличенной ценой (до {increased_price_max:,} руб.)",
                    "results": organize_by_building(increased_price_results)
                }

        logger.info("Не найдено объектов даже с увеличенной ценой")
        await bot.send_message(chat_id=user_id, text="Не найдено объектов даже с увеличенной ценой")

        # Шаг 4: Если все еще нет результатов и изначально искали для покупки,
        # проверяем варианты аренды
        if purpose and purpose.lower() == "for sale":
            logger.info("Поиск вариантов аренды вместо покупки")

            rental_results = search_database(
                purpose = 'For Rent',
                beds=beds,
                property_type=property_type,
                area=area,
                building=building,
                view=view,
                price_min=price_min,
                price_max=increased_price_max,
                baths=baths,
                sqft_min=None,
                sqft_max=None,
                furnishing=furnishing,
                completion=completion,
                vacant=vacant,
                handover_date=handover_date,
            )

            # Если найдены варианты аренды, организуем их по зданиям
            if rental_results:
                logger.info(f"Найдено {len(rental_results)} вариантов аренды")
                return {
                    "status": "rent_option",
                    "message": f"Не найдено объектов для покупки, но найдено {len(rental_results)} вариантов аренды",
                    "results": organize_by_building(rental_results)
                }


        # Если не найдено результатов ни в одном поиске, возвращаем пустой словарь
        return {
            "status": "not_found",
            "message": "Не найдено подходящих объектов недвижимости",
            "results": {}
        }
    else:
        return {
            "status": "no_search",
            "message": message
        }



# Пример использования
if __name__ == "__main__":
    user_queries = [
        'Найди мне апартаменты от 4000000 до 7000000 с двумя спальнями',
    ]

    # Демонстрация работы на нескольких запросах
    for query in user_queries:
        print(f"\n\nЗапрос пользователя: '{query}'")
        response = process_real_estate_query(query)
