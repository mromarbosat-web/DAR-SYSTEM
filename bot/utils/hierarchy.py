import discord
from typing import Tuple, Optional

def can_moderate_member(
    issuer: discord.Member,
    target: discord.Member,
    bot_member: Optional[discord.Member] = None,
    check_bot: bool = True
) -> Tuple[bool, str]:
    """
    Validates role hierarchy between issuer, target, and bot.
    Returns (allowed: bool, reason: str)
    """
    if issuer.id == target.id:
        return False, "لا يمكنك تطبيق هذا الإجراء على نفسك."

    if target.id == issuer.guild.owner_id:
        return False, "لا يمكنك تطبيق أي إجراء على مالك السيرفر."

    # Server Owner always bypasses issuer top role hierarchy
    if issuer.id != issuer.guild.owner_id:
        if issuer.top_role.position <= target.top_role.position:
            return False, f"لا يمكنك تطبيق هذا الإجراء على {target.mention} لأن رتبته أفقية أو أعلى من رتبتك."

    # Check Bot hierarchy if required
    if check_bot and bot_member:
        if bot_member.top_role.position <= target.top_role.position:
            return False, f"لا يستطيع البوت تطبيق هذا الإجراء على {target.mention} لأن رتبة البوت أدنى من أو تساوي رتبته."

    return True, ""

def has_warning_permission(
    member: discord.Member,
    action_type: str, # "issue", "view", "edit", "remove", "expire", "evidence", "settings"
    warning_settings = None
) -> bool:
    """
    Check if member has the required role ID or discord permissions.
    """
    if member.guild_permissions.administrator or member.id == member.guild.owner_id:
        return True

    if not warning_settings:
        # Fallback to standard discord permissions
        if action_type in ["issue", "edit", "expire", "evidence"]:
            return member.guild_permissions.moderate_members or member.guild_permissions.manage_messages
        elif action_type in ["remove", "settings"]:
            return member.guild_permissions.administrator or member.guild_permissions.manage_guild
        elif action_type == "view":
            return member.guild_permissions.moderate_members or member.guild_permissions.view_audit_log
        return False

    # Check configured Role IDs
    role_map = {
        "issue": warning_settings.issuer_role_id,
        "view": warning_settings.viewer_role_id,
        "edit": warning_settings.editor_role_id,
        "remove": warning_settings.remover_role_id,
        "expire": warning_settings.expirer_role_id,
        "evidence": warning_settings.evidence_manager_role_id,
        "settings": warning_settings.settings_manager_role_id,
    }

    required_role_id = role_map.get(action_type)
    if required_role_id:
        member_role_ids = [r.id for r in member.roles]
        if required_role_id in member_role_ids:
            return True

    # Default fallback permissions if specific role ID is not set or not matched
    if action_type in ["issue", "edit", "expire", "evidence", "view"]:
        return member.guild_permissions.moderate_members
    elif action_type in ["remove", "settings"]:
        return member.guild_permissions.administrator or member.guild_permissions.manage_guild

    return False

def has_voice_permission(
    member: discord.Member,
    action_type: str, # "move", "disconnect", "mute", "unmute", "lock", "unlock", "settings"
    voice_settings = None
) -> bool:
    """
    Check if member has voice management permissions.
    """
    if member.guild_permissions.administrator or member.id == member.guild.owner_id:
        return True

    if voice_settings and voice_settings.voice_manager_role_id:
        member_role_ids = [r.id for r in member.roles]
        if voice_settings.voice_manager_role_id in member_role_ids:
            return True

    # Discord permission fallbacks
    perms = member.guild_permissions
    if action_type in ["move", "disconnect"]:
        return perms.move_members
    elif action_type in ["mute", "unmute"]:
        return perms.mute_members
    elif action_type in ["lock", "unlock"]:
        return perms.manage_channels
    elif action_type == "settings":
        return perms.administrator or perms.manage_guild

    return False
