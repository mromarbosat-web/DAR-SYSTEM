import re

with open("bot/services/automod_service.py", "r") as f:
    content = f.read()

content = content.replace('log_event(message.guild, "security", log_embed)', 'log_event(message.guild, "automod", log_embed)')

with open("bot/services/automod_service.py", "w") as f:
    f.write(content)
