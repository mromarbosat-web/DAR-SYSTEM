with open('bot/cogs/help.py', 'r') as f:
    content = f.read()

old_str = '("`/balance [user]`", "عرض رصيد المحفظة والبنك وإجمالي الثروة", False),'
new_str = '("`/balance`, `/cash`, `/رصيدي`", "عرض رصيد المحفظة والبنك وإجمالي الثروة", False),'
content = content.replace(old_str, new_str)

old_str2 = '("`/daily`", "المطالبة بالمكافأة اليومية مع مضاعف الاستمرارية (Streak)", False),'
new_str2 = '("`/daily`, `/يومي`", "المطالبة بالمكافأة اليومية مع مضاعف الاستمرارية", False),'
content = content.replace(old_str2, new_str2)

old_str3 = '("`/leaderboard`", "عرض قائمة أثرياء ومتصدري السيرفر", False),'
new_str3 = '("`/leaderboard`, `/top`, `/اغنياء`", "عرض قائمة أثرياء ومتصدري كل السيرفرات", False),'
content = content.replace(old_str3, new_str3)

with open('bot/cogs/help.py', 'w') as f:
    f.write(content)
