import psycopg2
from psycopg2 import extras
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Параметры подключения к базе данных
db_params = {
    "host": "45.159.250.69",
    "database": "query_ai_test",
    "user": "query_ai",
    "password": "AItest!@25",
    "port": "5432"
}


def get_db_connection():
    """
    Создание соединения с базой данных PostgreSQL.

    Returns:
        connection: Объект соединения с базой данных
    """
    try:
        connection = psycopg2.connect(**db_params)
        return connection
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        raise


def search_database(purpose=None, beds=None, property_type=None, area=None,
                    building=None, view=None, price_min=None, price_max=None,
                    baths=None, sqft_min=None, sqft_max=None, furnishing=None,
                    completion=None, vacant=None, handover_date=None):
    """
    Поиск объектов недвижимости в базе данных по заданным параметрам.

    Args:
        purpose (str): Назначение (покупка/аренда)
        beds (int): Количество спален
        property_type (str): Тип недвижимости
        area (str): Район
        building (str): Название здания
        view (str): Вид из окна
        price_min (float): Минимальная цена
        price_max (float): Максимальная цена
        baths (int): Количество ванных комнат
        sqft_min (float): Минимальная площадь в квадратных футах
        sqft_max (float): Максимальная площадь в квадратных футах
        furnishing (str): Меблировка
        completion (str): Статус готовности

    Returns:
        list: Список объектов недвижимости, соответствующих критериям
    """
    # Проверка обязательных параметров
    if property_type is None or beds is None or price_min is None or price_max is None:
        logger.error("Отсутствуют обязательные параметры: type_unit, Beds, price_min, price_max")
        return []

    # Преобразование параметров
    if purpose == 'buy':
        purpose = 'For sale'
    elif purpose == 'rent':
        purpose = 'For rent'

    # Начало построения SQL запроса
    query = """
    SELECT 
        u.id, u.price, u.type_unit, u.purpose, u.completion, 
        u.handover_date, u.furnishing, u."Studio", u.sqft, 
        u."Baths", u."Beds", u.view, u.vacant, 
        b.name as building_name, a.original_name as area_name
    FROM 
        "Units" u
    LEFT JOIN 
        "Buildings" b ON u.building_id = b.id
    LEFT JOIN 
        "Areas" a ON u.area_id = a.id
    WHERE 
        u.post_status != 'archived'
    """

    # Список параметров для подготовленного запроса
    params = []

    # Добавление условий поиска
    if property_type:
        query += " AND u.type_unit ILIKE %s"
        params.append(property_type)


    if beds:
        query +=  ' AND u."Beds" = %s'
        params.append(beds)

    if price_min is not None:
        query += " AND u.price >= %s"
        params.append(price_min)

    if price_max is not None:
        query += " AND u.price <= %s"
        params.append(price_max)

    if purpose:
        query += " AND u.purpose ILIKE %s"
        params.append(purpose)

    if view:
        query += " AND u.view ILIKE %s"
        params.append(view)

    if area:
        query += " AND a.original_name ILIKE %s"
        params.append(f"%{area}%")  # ILIKE для нечувствительного к регистру поиска с частичным совпадением

    if building:
        query += " AND b.name ILIKE %s"
        params.append(f"%{building}%")  # ILIKE для нечувствительного к регистру поиска с частичным совпадением

    # Дополнительные параметры поиска
    if baths:
        query += ' AND u."Baths" = %s'
        params.append(baths)

    if sqft_min:
        query += " AND u.sqft >= %s"
        params.append(sqft_min)

    if sqft_max:
        query += " AND u.sqft <= %s"
        params.append(sqft_max)

    if furnishing:
        query += " AND u.furnishing ILIKE %s"
        params.append(furnishing)

    if vacant:
        query += " AND u.vacant ILIKE %s"
        params.append(vacant)

    if furnishing:
        query += " AND u.handover_date < %s"
        params.append(handover_date)

    if completion:
        query += " AND u.completion = %s"
        params.append(completion)

    # Сортировка результатов по цене
    query += " ORDER BY u.price ASC"

    print(query)

    try:
        # Получение соединения с базой данных
        connection = get_db_connection()
        with connection:
            with connection.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # Выполнение запроса
                cursor.execute(query, params)
                results = cursor.fetchall()

                # Преобразование результатов в список словарей
                properties = []
                for row in results:
                    # Преобразование строк RealDictRow в обычные словари
                    property_dict = dict(row)

                    # Переименование ключей для соответствия ожидаемому формату
                    property_dict['building'] = property_dict.pop('building_name')
                    property_dict['area'] = property_dict.pop('area_name')

                    properties.append(property_dict)

                return properties
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return []


def get_available_areas():
    """
    Получение списка всех доступных районов.

    Returns:
        list: Список названий районов
    """
    query = """
    SELECT original_name 
    FROM "Areas" 
    ORDER BY original_name
    """

    try:
        connection = get_db_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Ошибка при получении списка районов: {e}")
        return []


def get_available_buildings():
    """
    Получение списка всех доступных зданий.

    Returns:
        list: Список названий зданий
    """
    query = """
    SELECT name 
    FROM "Buildings" 
    ORDER BY name
    """

    try:
        connection = get_db_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Ошибка при получении списка зданий: {e}")
        return []




# Пример использования
if __name__ == "__main__":
    #Пример поиска квартиры
    properties = search_database(
        beds=2,
        property_type="Apartment",
        price_min=4000000,
        price_max=9000000
    )

    print(f"Найдено объектов: {len(properties)}")

    for prop in properties:
        print(f"ID: {prop['id']}, Цена: {prop['price']}, "
              f"Здание: {prop['building']}, Район: {prop['area']}")
    # areas = get_available_areas()
    # buildings = get_available_buildings()
    # print(areas)
    # print(buildings)