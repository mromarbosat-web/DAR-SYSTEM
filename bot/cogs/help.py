import discord
from discord import app_commands
from discord.ext import commands
from bot.config.settings import settings
from bot.utils.embeds import EmbedBuilder

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="الاقتصاد والعملة (Economy)",
                value="economy",
                description="أوامر المحفظة، المكافأة اليومية، التحويل، البنك، والمتجر",
                emoji="🌫️"
            ),
            discord.SelectOption(
                label="إدارة الرتب (Role Management)",
                value="roles",
                description="أوامر إضافة، إزالة، إنشاء، حذف، وتغيير ألوان وأسماء الرتب",
                emoji="🎭"
            ),
            discord.SelectOption(
                label="الصلاحيات الإدارية (Permissions)",
                value="permissions",
                description="أوامر تعيين رتب Server Admin ومدراء الأنظمة الفرعية",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="الحماية والفلترة التلقائية (Security & AutoMod)",
                value="security",
                description="أوامر أنظمة Anti-Raid، AutoMod، والقائمة البيضاء",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="الإشراف العقوبات (Moderation & Warnings)",
                value="moderation",
                description="أوامر التحذيرات، العزل المؤقت، الطرد، الحظر، والتطهير",
                emoji="🔨"
            ),
            discord.SelectOption(
                label="الرومات الصوتية والسجلات (Voice & Logs)",
                value="utility",
                description="أوامر إدارة الصوتيات، سجلات الأحداث، ونظام التحقق",
                emoji="🎙️"
            ),
        ]
        super().__init__(placeholder="اختر الفئة للاستعراض التفصيلي للـ Slash Commands...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        val = self.values[0]
        if val == "economy":
            embed = EmbedBuilder.info(
                title="🌫️ قسم الاقتصاد والعملة (Economy & Wallet)",
                description=f"أوامر العملة العالمية **{settings.CURRENCY_NAME}**:",
                fields=[
                    ("`/balance [user]`", "عرض رصيد المحفظة والبنك وإجمالي الثروة", False),
                    ("`/daily`", "المطالبة بالمكافأة اليومية مع مضاعف الاستمرارية (Streak)", False),
                    ("`/pay user:User amount:N`", "تحويل مبلغ مالي لعضو آخر", False),
                    ("`/deposit amount:N/all`", "إيداع مبلغ من المحفظة إلى البنك", False),
                    ("`/withdraw amount:N/all`", "سحب مبلغ من البنك إلى المحفظة", False),
                    ("`/leaderboard`", "عرض قائمة أثرياء ومتصدري السيرفر", False),
                    ("`/inventory [user]`", "عرض الحقيبة والمشتروات المملوكة", False),
                    ("`/economy average`", "حساب ومتوسط السيولة لجميع الحسابات", False),
                    ("`/shop` & `/buy product_id:N`", "تصفح وشراء المعروضات والرتب الممتازة", False),
                    ("`/economy give|remove|set|reset`", "أوامر الإدارة الاقتصادية المخصصة لـ `ECONOMY_MANAGER`", False)
                ]
            )
        elif val == "roles":
            embed = EmbedBuilder.info(
                title="🎭 قسم إدارة الرتب (Role Management)",
                description="أوامر التحكم الشامل بالرتب وفق صلاحيات Discord Hierarchy:",
                fields=[
                    ("`/role add user:User role:Role`", "إضافة رتبة لعضو محدد", False),
                    ("`/role remove user:User role:Role`", "سحب رتبة من عضو محدد", False),
                    ("`/role rename role:Role name:Name`", "تغيير اسم الرتبة", False),
                    ("`/role color role:Role color:#Hex`", "تغيير لون الرتبة بواسطة كود الهكس", False),
                    ("`/role create name:Name [color:#Hex]`", "إنشاء رتبة جديدة بالسيرفر", False),
                    ("`/role delete role:Role`", "حذف رتبة مع واجهة زِر التثبيت والتأكيد", False)
                ]
            )
        elif val == "permissions":
            embed = EmbedBuilder.info(
                title="⚙️ قسم الصلاحيات الإدارية (Permission System)",
                description="توزيع الأدوار والصلاحيات لمدراء الأنظمة البوت الفرعية:",
                fields=[
                    ("`/permissions set_admin_role role:Role`", "منح رتبة صلاحيات Server Admin الكاملة للبوت", False),
                    ("`/permissions remove_admin_role role:Role`", "إلغاء رتبة Server Admin", False),
                    ("`/permissions list_admin_roles`", "عرض كافة رتب Server Admin المسجلة", False),
                    ("`/permissions set_manager permission:TYPE role:Role`", "تخصيص رتبة لمدير نظام فرعي محدد", False),
                    ("`/permissions remove_manager permission:TYPE role:Role`", "إزالة رتبة من إدارة نظام فرعي", False),
                    ("`/permissions list_managers`", "استعراض كافة توزيعات المدراء بالسيرفر", False)
                ]
            )
        elif val == "security":
            embed = EmbedBuilder.info(
                title="🛡️ قسم الحماية والفلترة (Security & AutoMod)",
                description="أنظمة حماية السيرفر الذكية والوقاية من المداهمات:",
                fields=[
                    ("`/security setup` & `/security status`", "تخصيص حدود Anti-Spam, Anti-Raid, Anti-Bots", False),
                    ("`/automod setup` & `/automod status`", "فلترة الكلمات الخادشة والروابط والإشارات العشوائية", False),
                    ("`/whitelist add_user|role|bot`", "إضافة أعضاء أو رتب للقائمة البيضاء للأنظمة الحساسة", False)
                ]
            )
        elif val == "moderation":
            embed = EmbedBuilder.info(
                title="🔨 قسم الإشراف والعقوبات (Moderation & Warnings)",
                description="أوامر التحكم بالتأديب والعقوبات:",
                fields=[
                    ("`/warn user:User reason:Reason`", "توجيه تحذير رسمي لعضو مع تفعيل سلم العقوبات تلقائيًا", False),
                    ("`/unwarn warning_id:ID`", "إلغاء تحذير محدد باستخدام الـ ID", False),
                    ("`/warnings user:User`", "عرض سجل التحذيرات الكامل للعضو", False),
                    ("`/timeout user:User duration:Duration`", "عزل عضو مؤقتًا (مثال: `10m`, `1h`, `1d`)", False),
                    ("`/kick user:User [reason]`", "طرد عضو من السيرفر", False),
                    ("`/ban user:User [reason]`", "حظر عضو نهائيًا من السيرفر", False),
                    ("`/clear amount:N`", "تطهير ومسح عدد محدد من الرسائل في الشات", False)
                ]
            )
        elif val == "utility":
            embed = EmbedBuilder.info(
                title="🎙️ قسم الرومات الصوتية والسجلات (Voice, Logs & Verification)",
                description="الأدوات المساعدة وأنظمة السجلات:",
                fields=[
                    ("`/voice setup`", "تفعيل وإنشاء نظام رومات الصوت التلقائية (Interface Voice Channel)", False),
                    ("`/logs setup`", "تحديد روم تسجيل وتتبع كافة الأحداث والتصرفات الإدارية", False),
                    ("`/verification setup`", "إعداد وتفعيل زر التحقق لتأمين الدخول (Captch/Verification)", False),
                    ("`/botinfo` & `/ping`", "استعلام زمن الاستجابة والمعلومات التقنية للبوت", False)
                ]
            )
        else:
            embed = EmbedBuilder.info("الدليل الشامل", "اختر قسمًا من القائمة المنسدلة للتعرف على الأوامر.")

        await interaction.edit_original_response(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

class HelpCog(commands.Cog):
    """Cog providing Categorized Help Command"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="دليل واستعراض كافة أوامر البوت مقسمة حسب التصنيفات")
    async def help_command(self, interaction: discord.Interaction):
        embed = EmbedBuilder.info(
            title="✨ قائمة المساعدة والدليل الشامل (Security & Management Bot)",
            description=(
                f"أهلاً بك **{interaction.user.display_name}** في البوت الشامل للحماية والإدارة والاقتصاد.\n\n"
                f"• **العملة المعتمدة:** `{settings.CURRENCY_NAME}` {settings.CURRENCY_EMOJI}\n"
                f"• **أوامر Slash:** جميع الأوامر تعمل بنظام التفاعلات المباشرة المعتمد من Discord.\n\n"
                f"👇 **يرجى اختيار القسم من القائمة المنسدلة أدناه للتعرف على الأوامر والتفاصيل:**"
            )
        )
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
