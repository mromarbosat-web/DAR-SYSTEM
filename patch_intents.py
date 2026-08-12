import re

with open("bot/main.py", "r") as f:
    content = f.read()

target = "intents.moderation = True       # Required for Audit Logs & Anti-Nuke"
repl = "intents.moderation = True       # Required for Audit Logs & Anti-Nuke\nintents.voice_states = True     # Required for Voice Logs\nintents.invites = True          # Required for Invite Tracking"

content = content.replace(target, repl)

with open("bot/main.py", "w") as f:
    f.write(content)
