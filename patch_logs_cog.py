import re

with open("bot/cogs/logs.py", "r") as f:
    content = f.read()

repl = """            app_commands.Choice(name="Role Logs (إنشاء وتعديل وحذف الرتب)", value="role"),
            app_commands.Choice(name="Channel Logs (إنشاء وتعديل وحذف القنوات)", value="channel"),
            app_commands.Choice(name="Server Logs (إعدادات السيرفر والـ Webhooks)", value="server"),
            app_commands.Choice(name="Security Logs (Anti-Raid & Anti-Nuke & AutoMod)", value="security"),
            app_commands.Choice(name="Voice Logs (الدخول والخروج من الرومات الصوتية)", value="voice"),
            app_commands.Choice(name="Invite Logs (تتبع الدعوات ودخول الأعضاء)", value="invite"),
            app_commands.Choice(name="Economy Logs (عمليات تحويل وشراء وحصول على أرصدة)", value="economy"),
            app_commands.Choice(name="Verification Logs (محاولات التوثيق ونجاحها أو فشلها)", value="verification"),
            app_commands.Choice(name="AutoMod Logs (سجلات نظام الحماية التلقائي)", value="automod")
"""

target = """            app_commands.Choice(name="Role Logs (إنشاء وتعديل وحذف الرتب)", value="role"),
            app_commands.Choice(name="Channel Logs (إنشاء وتعديل وحذف القنوات)", value="channel"),
            app_commands.Choice(name="Server Logs (إعدادات السيرفر والـ Webhooks)", value="server"),
            app_commands.Choice(name="Security Logs (Anti-Raid & Anti-Nuke & AutoMod)", value="security")"""

content = content.replace(target, repl)

with open("bot/cogs/logs.py", "w") as f:
    f.write(content)
