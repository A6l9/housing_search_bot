from openai import OpenAI
import json

def process_users_query(query, areas, buildings):
    client = OpenAI(api_key = 'TOKEN')

    tools = [{
        "type": "function",
        "function": {
            "name": "database_search",
            "description": "Получить список подходящих объектов недвижимости",
            "parameters": {
                "type": "object",
                "properties": {
                    'min_price': {"type": "number",
                                  "description": "Минимальная цена объекта"},
                    'max_price': {"type": "number",
                                  "description": "Максимальная цена объекта"},
                    'type': {
                        "type": "string",
                        "enum": [
                            "Apartment",
                            "Penthouse",
                            "Residental",
                            "Townhouse",
                            "Villa",
                        ],
                        "description": "Тип искомого объекта"
                    },
                    'purpose' : {
                        "type": "string",
                        "enum": [
                            "",
                            "For Sale",
                            "For Rent"
                        ],
                        "description": "Объект для продажи или для аренды"
                    },
                    'completion' :{
                        "type": "string",
                        "enum": [
                            '',
                            "Off-Plan",
                            "Ready"
                        ],
                        "description": "Готов объект недвижимости или нет"
                    },
                    'handover_date' : {
                        "type": "string",
                        "description": "Дата готовности"
                    },
                    'furnishing' : {
                        "type": "string",
                        "enum": [
                            '',
                            "Furnished",
                            "Unfurnished"
                        ],
                        "description": "Мебелирован объект или нет"
                    },
                    'studio' : {
                        "type": "string",
                        "enum": [
                            '',
                            "Studio",
                            "None"
                        ],
                        "description": "Объект - студия или нет"
                    },
                    'sqft' : {"type": "number", "description": "Площадь объекта"},
                    'bath_count': {"type": "number", "description": "Количество ванн"},
                    'bedroom_count': {"type": "number", "description": "Количество спален"},
                    'view' : {
                        "type": "string",
                        "description": "Название объекта, вид на который нужен"
                    },
                    'vacant' : {
                        "type": "string",
                        "enum": [
                            '',
                            "Vacant",
                            "Rented",
                            "Tenanted"
                        ],
                        "description": "Свободно или занято"
                    },
                    'area' : {
                        "type": "string",
                        "description": "Название района"
                    },
                    'building': {
                        "type": "string",
                        "description": "Название здания"
                    },
                },
                "required": ["min_price", "max_price","type",'purpose','completion','area','building','vacant','view','bedroom_count','bath_count','sqft','studio','furnishing','handover_date'],
                "additionalProperties": False
            },
            "strict": True
        }
    }]


    prompt = f'''Твоя задача - подобрать пользователю по запросу объекты недвижимости.
    Тебе необходимо определить критерии, по которым пользователь ищет объект недвижимости. Минимальная необходимая информация - количество спален (bedroom_count), минимальная цена (min_price), максимальная цена (max_price) и тип объекта (type).
    Если пользователь не сообщил какой-то из обязательных критериев, задавай уточняющие вопросы. Определив критерии, вызови функцию database_search с соответствующими аргументами.
    
    
    Возможные названия зданий:
    {buildings}
    
    Возможные названия районов
    {areas}
    
    Запрос пользователя:
    {query}
    '''


    messages = [{"role": "user", "content": prompt}]

    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        tools=tools,
    )

    if completion.choices[0].message.tool_calls:
        argus = completion.choices[0].message.tool_calls[0].function.arguments
        return completion.choices[0].message.content, json.loads(argus)

    return completion.choices[0].message.content, None
