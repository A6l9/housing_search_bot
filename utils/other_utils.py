import urllib.parse

def create_whatsapp_link(phone_number, message):
    # Убедитесь, что номер телефона в международном формате
    phone_number = phone_number.lstrip('+')

    # URL-кодирование сообщения
    encoded_message = urllib.parse.quote(message)

    # Создание ссылки
    whatsapp_link = f"https://wa.me/{phone_number}?text={encoded_message}"

    return whatsapp_link

def format_property_info(prop):
    """
    Форматирование информации о недвижимости для вывода пользователю.

    Args:
        prop: Словарь с данными о недвижимости

    Returns:
        str: Отформатированная строка с информацией
    """
    # Базовая информация, которая есть у всех объектов
    info = f"ID: {prop['id']}, "
    info += f"{prop.get('beds', 'Н/Д')} спален, "
    info += f"{prop.get('baths', 'Н/Д')} ванных, "
    info += f"{prop.get('sqft', 'Н/Д')} кв.футов, "
    info += f"Цена: {prop.get('price', 0):,} дубайских тугриков, "

    # Добавляем вид, если он указан
    if prop.get('view'):
        info += f"Вид: {prop['view']}, "

    # Добавляем статус готовности, если он указан
    if prop.get('completion'):
        info += f"Статус: {prop['completion']}, "

    # Добавляем меблировку, если она указана
    if prop.get('furnishing'):
        info += f"Меблировка: {prop['furnishing']}"

    return info

def organize_by_building(properties):
    """
    Организация объектов недвижимости по зданиям.

    Args:
        properties: Список словарей с объектами недвижимости

    Returns:
        dict: Словарь, где ключи - названия зданий, значения - списки объектов
    """
    result = {}

    for prop in properties:
        building_name = prop.get("building", "Неизвестное здание")

        if building_name not in result:
            result[building_name] = []

        # Создаем новый словарь со всеми характеристиками объекта
        property_details = {
            'id': prop.get('id'),
            'price': prop.get('price'),
            'type_unit': prop.get('type_unit'),
            'purpose': prop.get('purpose'),
            'completion': prop.get('completion'),
            'handover_date': prop.get('handover_date'),
            'furnishing': prop.get('furnishing'),
            'studio': prop.get('Studio'),
            'sqft': prop.get('sqft'),
            'baths': prop.get('Baths'),
            'beds': prop.get('Beds'),
            'view': prop.get('view'),
            'vacant': prop.get('vacant'),
            'agent_name': prop.get('agent_name'),
            'agent_whatsapp': prop.get('agent_whatsapp'),
            'area': prop.get('area'),
            'building': building_name
        }

        result[building_name].append(property_details)

    return result



def display_search_results(response):
    """
    Функция для отображения результатов поиска в удобном для пользователя формате.

    Args:
        response: Результат работы функции process_real_estate_query
    """
    print("\n" + "=" * 50)
    print(f"Статус поиска: {response['status']}")
    print(response['message'])
    print("=" * 50)

    if not 'results' in response:
        return

    if not response['results']:
        print("Не найдено подходящих объектов.")
        return

    total_properties = 0

    # Вывод результатов по зданиям
    for building, properties in response['results'].items():
        print(f"\n📍 Здание: {building}")
        print("-" * 40)

        for i, prop in enumerate(properties, 1):
            print(f"{i}. {format_property_info(prop)}")

        total_properties += len(properties)

    print("\n" + "=" * 50)
    print(f"Всего найдено объектов: {total_properties}")
    print("=" * 50)