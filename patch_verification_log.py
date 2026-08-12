import re

with open("bot/services/verification_service.py", "r") as f:
    content = f.read()

content = content.replace('log_event(guild, "member", log_embed)', 'log_event(guild, "verification", log_embed)')

with open("bot/services/verification_service.py", "w") as f:
    f.write(content)
