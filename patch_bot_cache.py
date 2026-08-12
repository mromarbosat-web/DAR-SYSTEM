import re

with open("bot/main.py", "r") as f:
    content = f.read()

content = content.replace('super().__init__(', 'super().__init__(\n            max_messages=10000, # Large message cache for Message Delete Logs')

with open("bot/main.py", "w") as f:
    f.write(content)
