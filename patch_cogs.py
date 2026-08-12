import re
from pathlib import Path

# economy.py
eco_path = Path("bot/cogs/economy.py")
content = eco_path.read_text()

# Add LogService import if not there
if "LogService" not in content:
    content = content.replace("from bot.services.economy_service import EconomyService", "from bot.services.economy_service import EconomyService\nfrom bot.services.log_service import LogService")

# In daily_command
def repl_daily(match):
    return match.group(0) + """
            if success:
                log_svc = LogService(session)
                embed_log = discord.Embed(title="💰 مكافأة يومية", color=discord.Color.green())
                embed_log.add_field(name="العضو", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
                embed_log.add_field(name="المبلغ", value=f"`{reward}`", inline=True)
                embed_log.add_field(name="الـ Streak", value=f"`{streak}`", inline=True)
                await log_svc.log_event(interaction.guild, "economy", embed_log)
"""
content = re.sub(r'success,\s*msg,\s*reward,\s*streak\s*=\s*await\s*eco_service\.claim_daily\([^)]+\)', repl_daily, content)

# In pay_command
def repl_pay(match):
    return match.group(0) + """
            if success:
                log_svc = LogService(session)
                embed_log = discord.Embed(title="💸 تحويل رصيد", color=discord.Color.blue())
                embed_log.add_field(name="المرسل", value=f"{interaction.user.mention}", inline=True)
                embed_log.add_field(name="المستلم", value=f"{user.mention}", inline=True)
                embed_log.add_field(name="المبلغ", value=f"`{amount}`", inline=False)
                await log_svc.log_event(interaction.guild, "economy", embed_log)
"""
content = re.sub(r'success,\s*msg\s*=\s*await\s*eco_service\.transfer_coins\([^)]+\)', repl_pay, content)

eco_path.write_text(content)

# shop.py
shop_path = Path("bot/cogs/shop.py")
content = shop_path.read_text()

if "LogService" not in content:
    content = content.replace("from bot.services.shop_service import ShopService", "from bot.services.shop_service import ShopService\nfrom bot.services.log_service import LogService")

def repl_buy(match):
    return match.group(0) + """
            if success:
                log_svc = LogService(session)
                embed_log = discord.Embed(title="🛒 شراء من المتجر", color=discord.Color.gold())
                embed_log.add_field(name="العضو", value=f"{interaction.user.mention}", inline=True)
                embed_log.add_field(name="رقم المنتج", value=f"`{product_id}`", inline=True)
                await log_svc.log_event(interaction.guild, "economy", embed_log)
"""
content = re.sub(r'success,\s*msg\s*=\s*await\s*shop_service\.buy_product\([^)]+\)', repl_buy, content)

def repl_add_prod(match):
    return match.group(0) + """
            log_svc = LogService(session)
            embed_log = discord.Embed(title="🛍️ إضافة منتج", color=discord.Color.green())
            embed_log.add_field(name="المشرف", value=f"{interaction.user.mention}", inline=True)
            embed_log.add_field(name="المنتج", value=f"`{name}`", inline=True)
            await log_svc.log_event(interaction.guild, "economy", embed_log)
"""
content = re.sub(r'product\s*=\s*await\s*shop_service\.add_product\([^)]+\)', repl_add_prod, content)

shop_path.write_text(content)

