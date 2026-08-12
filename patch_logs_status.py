import re

with open("bot/services/setup_service.py", "r") as f:
    content = f.read()

target = '            ("⚙️ Server Logs", fmt_ch(logs.server_log_channel_id), True)\n        ]'

repl = """            ("⚙️ Server Logs", fmt_ch(logs.server_log_channel_id), True),
            ("🔊 Voice Logs", fmt_ch(getattr(logs, 'voice_log_channel_id', None)), True),
            ("🔗 Invite Logs", fmt_ch(getattr(logs, 'invite_log_channel_id', None)), True),
            ("💰 Economy Logs", fmt_ch(getattr(logs, 'economy_log_channel_id', None)), True),
            ("✅ Verification Logs", fmt_ch(getattr(logs, 'verification_log_channel_id', None)), True),
            ("🤖 AutoMod Logs", fmt_ch(getattr(logs, 'automod_log_channel_id', None)), True)
        ]"""

content = content.replace(target, repl)

with open("bot/services/setup_service.py", "w") as f:
    f.write(content)
