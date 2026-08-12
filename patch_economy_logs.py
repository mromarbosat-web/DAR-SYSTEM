import re

with open("bot/services/economy_service.py", "r") as f:
    content = f.read()

# Change admin_modify_balance log from "moderation" to "economy"
content = content.replace('log_event(admin_member.guild, "moderation", log_embed)', 'log_event(admin_member.guild, "economy", log_embed)')

with open("bot/services/economy_service.py", "w") as f:
    f.write(content)
