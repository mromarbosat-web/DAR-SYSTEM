import re

with open("bot/main.py", "r") as f:
    content = f.read()

imports = """
from bot.events.on_message_events import register_message_logs_events
from bot.events.on_voice_events import register_voice_logs_events
from bot.events.on_role_events import register_role_logs_events
from bot.events.on_channel_events import register_channel_logs_events
from bot.events.on_server_events import register_server_logs_events
from bot.events.on_member_events_ext import register_member_logs_ext_events
"""

content = content.replace("from bot.events.on_message import register_message_event", "from bot.events.on_message import register_message_event" + imports)

registers = """
    register_message_logs_events(bot)
    register_voice_logs_events(bot)
    register_role_logs_events(bot)
    register_channel_logs_events(bot)
    register_server_logs_events(bot)
    register_member_logs_ext_events(bot)
"""

content = content.replace("    register_message_event(bot)", "    register_message_event(bot)" + registers)

with open("bot/main.py", "w") as f:
    f.write(content)
