import discord
import logging

logger = logging.getLogger("discord_bot.invite_tracker")

class InviteTracker:
    def __init__(self, bot):
        self.bot = bot
        self.invites = {} # guild_id -> {code -> Invite}
        self.vanity_invites = {} # guild_id -> uses

    async def update_cache(self, guild: discord.Guild):
        try:
            if not guild.me.guild_permissions.manage_guild:
                return
            
            invs = await guild.invites()
            self.invites[guild.id] = {invite.code: invite for invite in invs}
            
            if "VANITY_URL" in guild.features:
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        self.vanity_invites[guild.id] = vanity.uses
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error updating invite cache for guild {guild.id}: {e}")

    async def fetch_inviter(self, member: discord.Member):
        guild = member.guild
        if guild.id not in self.invites:
            await self.update_cache(guild)
            return None

        old_invites = self.invites[guild.id]
        try:
            new_invites = await guild.invites()
        except Exception:
            return None

        # Compare
        for invite in new_invites:
            if invite.code in old_invites:
                if invite.uses > old_invites[invite.code].uses:
                    # Update cache
                    self.invites[guild.id][invite.code] = invite
                    return invite
            elif invite.uses > 0:
                # New invite used
                self.invites[guild.id][invite.code] = invite
                return invite

        # Check Vanity
        if "VANITY_URL" in guild.features:
            try:
                vanity = await guild.vanity_invite()
                if vanity and guild.id in self.vanity_invites:
                    if vanity.uses > self.vanity_invites[guild.id]:
                        self.vanity_invites[guild.id] = vanity.uses
                        return "vanity"
            except Exception:
                pass

        return None

invite_tracker = None

def setup_invite_tracker(bot):
    global invite_tracker
    invite_tracker = InviteTracker(bot)
    return invite_tracker
