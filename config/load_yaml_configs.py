import yaml

with open("config/bot_messages.yaml", encoding="utf-8") as file:
    bot_messages = yaml.safe_load(file)
