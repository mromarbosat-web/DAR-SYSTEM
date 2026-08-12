# 🛡️ Security & Management Bot | دليل التشغيل والنشر الشامل

**Security & Management Bot** هو بوت ديسكورد احترافي متكامل مصمم خصيصًا لحماية وتأمين وإدارة السيرفرات الضخمة والصغيرة بكفاءة عالية، مع دعم متعدد السيرفرات (**Multi-Guild Isolation**) والتوافق التام مع النشر على استضافة **Railway** كـ **Worker** واستخدام **Supabase PostgreSQL** كقاعدة بيانات دائمة وآمنة.

---

## 📐 الهيكلية والتصميم (Architecture)

تم بناء البوت باستخدام أحدث معايير البرمجة الهيكلية للـ Discord Bots:

```text
bot/
├── main.py                     # المدخل الرئيسي للبوت
├── config/
│   └── settings.py             # إدارة المتغيرات والبيئات
├── database/
│   ├── connection.py           # الربط البرمجي لـ Supabase (SQLAlchemy Async)
│   ├── models/                 # 14 جدولا في قاعدة البيانات (Guilds, Security, AutoMod, Logs...)
│   └── repositories/           # طبقة فصل الاستعلامات Repository Pattern
├── services/                   # منطق الأعمال (Anti-Raid, Anti-Nuke, AutoMod, Mod, Verification)
├── cogs/                       # أوامر Slash Commands المقسمة لوحدات مستقلة
├── events/                     # معالجة الأحداث والـ Gateway Listeners والـ Audit Logs
└── utils/                      # المساعدات الإدارية، التحقق من الرتب والـ Embeds
```

---

## 🚀 1. إعداد تطبيق Discord والبوت (Discord Developer Portal)

1. توجه إلى [Discord Developer Portal](https://discord.com/developers/applications).
2. أنشئ تطبيقًا جديدًا باسم **Security & Management Bot**.
3. من قائمة **Bot**:
   - اضغط على **Reset Token** للحصول على الـ `DISCORD_BOT_TOKEN`.
   - قم بتفعيل الخيارات التالية ضمن **Privileged Gateway Intents** (ضروري جدًا لتشغيل خصائص الحماية):
     - ✅ **PRESENCE INTENT**
     - ✅ **SERVER MEMBERS INTENT** (ضروري لنظام Anti-Raid والتوثيق والـ Member Logs)
     - ✅ **MESSAGE CONTENT INTENT** (ضروري لنظام AutoMod والـ Anti-Spam)
4. من قائمة **OAuth2 -> URL Generator**:
   - حدد Scope: `bot` و `applications.commands`.
   - حدد الصلاحيات (Bot Permissions): **Administrator** أو (Manage Server, Manage Roles, Manage Channels, Kick Members, Ban Members, Moderate Members, Manage Messages, View Audit Log).
   - انسخ الرابط وقم بدعوة البوت لسيرفرك.

---

## 🗄️ 2. إعداد قاعدة البيانات في Supabase PostgreSQL

1. افتح حسابك في [Supabase](https://supabase.com) وأنشئ مشروعًا جديدًا.
2. من **Project Settings -> Database**:
   - انسخ رابط الاتصال **URI / Connection String**.
   - تأكد من تحويل بادئة الرابط إلى `postgresql+asyncpg://` لاستخدام محرك `asyncpg` التزامني.
   - مثال:
     ```env
     DATABASE_URL=postgresql+asyncpg://postgres.ref:your-password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
     ```
3. يقوم البوت عند أول تشغيل بإنشاء جميع الجداول تلقائيًا عن طريق `SQLAlchemy Base`.
4. (اختياري) يمكنك تنشيط الجداول يدويًا بفتح **SQL Editor** في Supabase ولصق المحتوى الموجود في ملف `schema.sql`.

---

## 🚂 3. النشر على Railway (Railway Deployment)

المشروع مجهز بالكامل للعمل كـ Worker مستقر على Railway دون الحاجة لمنفذ Web Port:

1. قم بإنشاء مشروع جديد في [Railway](https://railway.app) وربطه مع المستودع (GitHub Repository).
2. سيقوم Railway باكتشاف الـ `Dockerfile` و `railway.json` تلقائيًا.
3. توجه إلى تبويب **Variables** وأضف المتغيرات التالية:

| المتغير (Variable) | الوصف (Description) |
| :--- | :--- |
| `DISCORD_BOT_TOKEN` | توكن البوت الرسمي من Discord Developer Portal |
| `DATABASE_URL` | رابط الاتصال بـ Supabase PostgreSQL (`postgresql+asyncpg://...`) |
| `LOG_LEVEL` | مستوى اللوجز (`INFO` أو `DEBUG`) |
| `ENVIRONMENT` | بيئة التشغيل (`production`) |

4. تأكد أن أمر التشغيل (Start Command) في Railway هو:
   ```bash
   python -m bot.main
   ```

---

## 📜 4. أوامر الـ Slash Commands المتاحة

### 🛡️ أمن وحماية السيرفر (Security & Anti-Raid & Anti-Nuke)
- `/security setup`: ضبط خيارات Anti-Raid و Anti-Nuke وحظر الدخول الجماعي.
- `/security status`: عرض تقرير متكامل لحالة الحماية في السيرفر.
- `/lock [all_channels]`: إغلاق القناة أو كافة قنوات السيرفر.
- `/unlock [all_channels]`: إعادة فتح القنوات للكتابة.

### ⚙️ الإشراف التلقائي (AutoMod)
- `/automod setup`: ضبط خيارات منع الروابط والدعوات والسبام والمنشن الجماعي.
- `/automod badwords`: إضافة/حذف كلمات من قائمة المحظورات.
- `/automod status`: استعراض الفلاتر القائمة.

### 🔨 الإشراف الإداري (Moderation & Warn Ladder)
- `/warn <user> <reason>`: توجيه تحذير وتطبيق عقوبة السلم التلقائي (3 warns -> Timeout, 5 -> Kick, 7 -> Ban).
- `/warnings <user>`: استعراض جميع تحذيرات العضو ومعرفاتها.
- `/unwarn <warning_id>`: حذف تحذير محدد باستخدام الـ ID.
- `/timeout <user> <duration> [reason]`: عزل العضو مؤقتًا (مثال: `10m`, `1h`, `1d`).
- `/untimeout <user>`: إلغاء العزل.
- `/kick <user> [reason]`: طرد عضو.
- `/ban <user> [reason]`: حظر عضو.
- `/unban <user_id>`: فك حظر عضو.
- `/softban <user>`: حظر ثم فك حظر لتطهير رسائل العضو.
- `/purge <amount>`: مسح الرسائل.
- `/slowmode <seconds>`: ضبط الوضع البطيء.

### 🔐 التوثيق والتحقق (Verification Panel)
- `/verification setup`: إرسال بنل التوثيق بزر تفاعلي يمنح رتبة الموثق Verified تلقائيًا.
- `/verification status`: استعراض إعدادات بنل التوثيق.

### 📋 السجلات واللوجز (Logs)
- `/logs setup`: تخصيص قنوات محددة لكل نوع من السجلات (Member, Message, Moderation, Role, Channel, Server, Security).
- `/logs status`: عرض خريطة قنوات اللوجز.

### ⚪ الاستثناءات (Whitelist)
- `/whitelist user`: إضافة/حذف عضو موثوق معفى من الحماية.
- `/whitelist role`: إضافة/حذف رتبة موثوقة.
- `/whitelist list`: استعراض القائمة البيضاء.

---

## 🛠️ التشغيل المحلي والتطوير (Local Development)

```bash
# 1. إنشاء البيئة الافتراضية
python -m venv venv
source venv/bin/activate  # في Linux/macOS
# venv\Scripts\activate   # في Windows

# 2. تثبيت المكتبات
pip install -r requirements.txt

# 3. نسخ ملف المتغيرات وإدخال التوكن ورابط الداتا بيز
cp .env.example .env

# 4. تشغيل البوت
python -m bot.main
```

---

## 🎯 المميزات الأمنية المتقدمة

1. **فحص تسلسل الرتب (Role Hierarchy Check)**: يمنع أي مشرف من اتخاذ إجراء ضد عضو أعلى منه أو مساوٍ له في الرتب، ويمنع اتخاذ أي إجراء ضد مالك السيرفر أو البوت نفسه.
2. **عزل بيانات السيرفرات (Multi-Guild Data Isolation)**: كل سيرفر يمتلك سجلاته وإعداداته المستقلة كليًا عبر مفاتيح `guild_id`.
3. **فصل المعالجات (Service & Repository Pattern)**: جميع استعلامات قاعدة البيانات معزولة تمامًا عن أوامر ديسكورد، مما يتيح ربطها مستقبلاً بشرائح REST API أو Web Dashboard دون إعادة كتابة الكود.
