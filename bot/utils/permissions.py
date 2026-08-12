import discord
from discord.ext import commands

def check_hierarchy(moderator: discord.Member, target: discord.Member) -> tuple[bool, str]:
    """
    Check if moderator can perform administrative actions on target based on role hierarchy.
    Returns (can_act: bool, reason: str)
    """
    # Cannot target server owner
    if target.id == moderator.guild.owner_id:
        return False, "لا يمكنك اتخاذ إجراء ضد مالك السيرفر! (Cannot target server owner)"

    # Cannot target yourself
    if moderator.id == target.id:
        return False, "لا يمكنك اتخاذ إجراء ضد نفسك! (Cannot target yourself)"

    # Server owner can moderate anyone else
    if moderator.id == moderator.guild.owner_id:
        return True, ""

    # Check top role position
    if moderator.top_role.position <= target.top_role.position:
        return False, "لا يمكنك اتخاذ إجراء ضد عضو يمتلك رتبة مساوية أو أعلى من رتبتك في السيرفر!"

    # Check bot hierarchy
    bot_member = moderator.guild.me
    if bot_member and bot_member.top_role.position <= target.top_role.position:
        return False, "لا يمكن للبوت اتخاذ إجراء ضد هذا العضو لأن رتبته أعلى أو مساوية لرتبة البوت!"

    return True, ""

def check_bot_hierarchy(guild: discord.Guild, target: discord.Member) -> tuple[bool, str]:
    """Check if bot has higher top role than target member"""
    if target.id == guild.owner_id:
        return False, "البوت لا يمكنه اتخاذ إجراء ضد مالك السيرفر."
    
    bot_member = guild.me
    if not bot_member:
        return False, "عضوية البوت غير متاحة."

    if bot_member.top_role.position <= target.top_role.position:
        return False, "رتبة البوت أدنى من أو مساوية لرتبة المستهدف."

    return True, ""
