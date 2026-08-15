import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.utils.time import utc_now
from bot.config.settings import settings
from bot.database.models.economy import ShopProduct, UserInventory, Wallet, Transaction

logger = logging.getLogger("discord_bot.shop_repository")

DEFAULT_BANNERS = [
    {
        "name": "🌌 بانر الفضاء الكوني (Cosmic Galaxy)",
        "price": 10000,
        "description": "بانر فلكي نقي من أعماق الفضاء الخارجي لملفك الشخصي.",
        "emoji": "🌌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "⚡ بانر السايبربانك النيون (Neon Cyberpunk)",
        "price": 12500,
        "description": "بانر مستقبلي بأضواء نيون سايبربانك مشعة.",
        "emoji": "⚡",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌅 بانر الشفق الذهبي (Golden Twilight)",
        "price": 15000,
        "description": "بانر ساحر لشفق الغروب الذهبي الفاخر.",
        "emoji": "🌅",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🐉 بانر التنين الملكي (Imperial Dragon)",
        "price": 17500,
        "description": "بانر أسطوري بقوة وهيبة التنين الإمبراطوري.",
        "emoji": "🐉",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "👑 بانر الفخامة المظلمة (Dark Luxury Aura)",
        "price": 20000,
        "description": "بانر فخم ونادر مرصع بهالة مظلمة وملكية لا تضاهى.",
        "emoji": "👑",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌸 بانر أزهار الساكورا (Sakura Blossom)",
        "price": 6000,
        "description": "بانر طبيعي ساحر لتساقط بتلات أزهار الساكورا الوردية.",
        "emoji": "🌸",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌌 بانر الشفق القطبي (Aurora Borealis)",
        "price": 8000,
        "description": "أضواء الأورورا الخضراء والبنفسجية المتراقصة في سماء القطب.",
        "emoji": "🌌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🏮 بانر ليالي طوكيو (Tokyo Neon Nights)",
        "price": 9500,
        "description": "أزقة طوكيو المضيئة بالفوانيس التقليدية ولوحات النيون الساحرة.",
        "emoji": "🏮",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌊 بانر أعماق المحيط (Deep Ocean Waves)",
        "price": 7500,
        "description": "أمواج المحيط الزرقاء الهادئة وأعماق المياه النقية.",
        "emoji": "🌊",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🏜️ بانر الصحراء القمرية (Desert Starlight)",
        "price": 8500,
        "description": "كثبان رملية ذهبية تحت قبة سماء مرصعة بالنجوم اللامعة.",
        "emoji": "🏜️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "⚔️ بانر الساموراي الملحمي (Epic Samurai)",
        "price": 14000,
        "description": "بانر بطولي مستوحى من دروع الساموراي ونصل السيوف الأسطورية.",
        "emoji": "⚔️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🔮 بانر البلورات السحرية (Crystal Caverns)",
        "price": 11000,
        "description": "بلورات كريستالية مشعة بطاقة سحرية غامضة في كهوف نادرة.",
        "emoji": "🔮",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1519751138087-5bf79df62d5b?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌆 بانر السنثويف والريترو (Synthwave 80s)",
        "price": 10500,
        "description": "خطوط أفق ثمانينية بألوان البنفسجي والوردي والمربعات الرقمية.",
        "emoji": "🌆",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌑 بانر خسوف القمر الدموي (Blood Moon Eclipse)",
        "price": 16000,
        "description": "قمر أحمر دموي في ليلة خسوف أسطورية تحبس الأنفاس.",
        "emoji": "🌑",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌲 بانر الغابة الضبابية (Misty Mystic Forest)",
        "price": 7000,
        "description": "أشجار الصنوبر الشامخة وسط ضباب الصباح الهادئ والنقي.",
        "emoji": "🌲",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🕹️ بانر البكسل آرت (Retro Pixel Horizon)",
        "price": 9000,
        "description": "مشهد بكسل كلاسيكي مستوحى من ألعاب الأركيد والريترو جيمز.",
        "emoji": "🕹️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🪐 بانر حلقات زحل (Saturn Rings)",
        "price": 13000,
        "description": "دوران حلقات كوكب زحل الرائعة في الفضاء السحيق.",
        "emoji": "🪐",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "❄️ بانر الجليد الأزلي (Frozen Glacier)",
        "price": 8500,
        "description": "جبال جليدية متلألئة تحت أشعة الشمس القطبية النقية.",
        "emoji": "❄️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🏙️ بانر ناطحات السحاب المطرية (Rainy City Skyline)",
        "price": 9000,
        "description": "أفق المدينة الحديثة تحت قطرات المطر وأضواء الشوارع المنعكسة.",
        "emoji": "🏙️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🦋 بانر الفراشات المضيئة (Luminous Butterflies)",
        "price": 11500,
        "description": "فراشات مشعة بضوء حيوي ساحر في ليلة هادئة.",
        "emoji": "🦋",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌋 بانر الحمم البركانية (Volcanic Fury)",
        "price": 15500,
        "description": "طاقة الحمم المتوهجة والشرار المتطاير من فوهة البركان.",
        "emoji": "🌋",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🍂 بانر الخريف الذهبي (Golden Autumn Leaves)",
        "price": 6500,
        "description": "أوراق الخريف المتساقطة بألوان ذهبية وبرتقالية دافئة.",
        "emoji": "🍂",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "💻 بانر شفرات الماتريكس (Matrix Digital Rain)",
        "price": 12000,
        "description": "شلال من الشفرات البرمجية والأكواد الخضراء المشفرة.",
        "emoji": "💻",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🏰 بانر القلعة الخيالية (Fantasy Sky Castle)",
        "price": 18000,
        "description": "قلعة أسطورية محلقة فوق الغيوم في عالم الفانتازيا الساحر.",
        "emoji": "🏰",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "💎 بانر الألماس الملكي (Royal Diamond Lux)",
        "price": 25000,
        "description": "انعكاسات ألماسة نادرة مشعة ببريق وفخامة فائقة.",
        "emoji": "💎",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&auto=format&fit=crop&q=80"
    },
    # --- ULTRA LUXURY EXCLUSIVE TIER (> 30,000 Aura) ---
    {
        "name": "🌟 بانر عرش الذهب الخالص (Imperial Golden Throne)",
        "price": 35000,
        "description": "بانر فاخر ونادر مرصع بزخارف الذهب الخالص وهيبة الملوك.",
        "emoji": "🌟",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🌌 بانر السديم الكوني الأعظم (Celestial Nebula Sovereign)",
        "price": 40000,
        "description": "قوة السدم والمجرات الكونية بألوان أرجوانية وزرقاء عميقة.",
        "emoji": "🌌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🦅 بانر أجنحة النور المقدس (Ethereal Divine Radiance)",
        "price": 45000,
        "description": "قمم جبلية ساحرة تعانق سديم الضوء السماوي الخارق.",
        "emoji": "🦅",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🔥 بانر طائر الفينيق الأسطوري (Astral Phoenix Rebirth)",
        "price": 50000,
        "description": "طيف ألوان الفينيق الأسطوري وطاقته المتجددة من رماد النجوم.",
        "emoji": "🔥",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🏛️ بانر القصر الإمبراطوري الشامخ (Imperial Grand Palace)",
        "price": 55000,
        "description": "معالم القصور الإمبراطورية التاريخية ذات الهيبة والفخامة.",
        "emoji": "🏛️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "💚 بانر الزمرد الملكي الخالد (Royal Emerald Dynasty)",
        "price": 60000,
        "description": "طاقة أحجار الزمرد الأخضر النادرة بانعكاسات ساحرة تخطف الأبصار.",
        "emoji": "💚",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "👑 بانر إمبراطور السايبر الخارق (Cyberpunk Overlord)",
        "price": 70000,
        "description": "قمة التطور المستقبلي وقيادة العالم الرقمي بهالة النيون.",
        "emoji": "👑",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1515260268569-9271009adfdb?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "💥 بانر انفجار السوبرنوفا الأعظم (Cosmic Supernova Prime)",
        "price": 80000,
        "description": "طاقة ولادة وانفجار النجوم العظمى في الفضاء الفلكي السحيق.",
        "emoji": "💥",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "🕳️ بانر ثقب الفضاء الأسود الأزلي (Singularity Black Hole)",
        "price": 90000,
        "description": "جاذبية الثقب الأسود المطلقة وانحناء الضوء والزمكان.",
        "emoji": "🕳️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1000&auto=format&fit=crop&q=80"
    },
    {
        "name": "⚜️ بانر السيادة المطلقة (Supreme Obsidian Sovereign)",
        "price": 100000,
        "description": "البانر الأسطوري الأعلى قيمة — هيبة ونفوذ النخبة المطلقة.",
        "emoji": "⚜️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1000&auto=format&fit=crop&q=80"
    },
    # --- ISLAMIC DARK BANNERS (10 Banners) ---
    {
        "name": "🕌 بانر المسجد العباسي الليلي (Dark Abbasid Mosque)",
        "price": 10000,
        "description": "بانر إسلامي داكن لعمارة المساجد التاريخية تحت سماء الليل الهادئة.",
        "emoji": "🕌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🕋 بانر السكينة الحرم المكي (Makkah Holy Serenity)",
        "price": 12000,
        "description": "أجواء إيمانية روحانية هادئة وعميقة تمس القلوب.",
        "emoji": "🕋",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "✨ بانر الفانوس الرمضاني الفاخر (Dark Ramadan Lantern)",
        "price": 9000,
        "description": "إضاءة دافئة لفانوس عربي تقليدي في خلفية داكنة فاخرة.",
        "emoji": "✨",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌕 بانر البدر الساطع المكتمل (Full Moon Radiance)",
        "price": 9500,
        "description": "قمر بدر متلألئ ومكتمل في سماء ليلية مظلمة وساحرة.",
        "emoji": "🌕",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1532767153582-b1a0e5145009?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌿 بانر المروج الخضراء اليانعة (Lush Green Meadows)",
        "price": 11000,
        "description": "طبيعة خضراء يانعة ومروج واسعة تناسب عشاق الخضرة والجمال.",
        "emoji": "🌿",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🕯️ بانر الفوانيس والمصابيح التراثية (Traditional Lanterns Glow)",
        "price": 10500,
        "description": "إضاءة المصابيح التقليدية الدافئة وسط أجواء تراثية ساحرة.",
        "emoji": "🕯️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🕌 بانر المسجد الأزرق العثماني (Ottoman Blue Mosque Night)",
        "price": 11500,
        "description": "روعة العمارة العثمانية والمآذن الشامخة ليلاً.",
        "emoji": "🕌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌌 بانر السديم الفلكي الهادئ (Calm Astral Nebula)",
        "price": 12500,
        "description": "أجواء فلكية هادئة وعميقة مليئة بالنجوم والسدم المضيئة.",
        "emoji": "🌌",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🏛️ بانر القصور التاريخية المهيبة (Majestic Historic Palace)",
        "price": 13000,
        "description": "عمارة القصور التاريخية العريقة وسط عتمة الليل الساحرة.",
        "emoji": "🏛️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🎨 بانر الفنون التراثية الأصيلة (Authentic Heritage Art)",
        "price": 10000,
        "description": "لوحات وفنون تراثية أصيلة بتصاميم تاريخية فاخرة.",
        "emoji": "🎨",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&h=600&fit=crop&q=80"
    },

    # --- NATURE SCENIC BANNERS (10 Banners) ---
    {
        "name": "🌲 بانر الغابات الخضراء العميقة (Deep Emerald Forest)",
        "price": 8500,
        "description": "مشهد طبيعي أفقي لأشجار الصنوبر الكثيفة والخضرة النقية.",
        "emoji": "🌲",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🏔️ بانر قمم الجبال الثلجية الكبرى (Majestic Alpine Peaks)",
        "price": 9000,
        "description": "سلسلة جبال شامخة مغطاة بالثلوج الناصعة تحت سماء صافية.",
        "emoji": "🏔️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🏞️ بانر الوديان الخضراء الساحرة (Serene Green Valley)",
        "price": 8000,
        "description": "وادي أخضر رحب يتوسطه نهر هادئ وطبيعة بكر خلابة.",
        "emoji": "🏞️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌊 بانر الشلالات الغابية المنسابة (Enchanted Forest Waterfall)",
        "price": 9500,
        "description": "تدفق مياه الشلالات النقية وسط أحضان الغابات الخضراء.",
        "emoji": "🌊",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌅 بانر شروق الشمس فوق البحيرة (Lake Sunrise Mirror)",
        "price": 9000,
        "description": "انعكاس ألوان الشروق الساحرة على سطح بحيرة جبلية ساكنة.",
        "emoji": "🌅",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌾 بانر حقول القمح الذهبية المترامية (Golden Wheat Horizon)",
        "price": 8500,
        "description": "سهوب وحقول قمح ذهبية تمتد حتى أفق السماء الفسيحة.",
        "emoji": "🌾",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌸 بانر حديقة الورود الربيعية (Spring Blooming Garden)",
        "price": 8000,
        "description": "تفتح أزهار الربيع الزاهية في لوحة طبيعية مبهجة.",
        "emoji": "🌸",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🍂 بانر خريف الغابات الدافئ (Warm Autumn Canopy)",
        "price": 8500,
        "description": "أوراق الأشجار البرتقالية والذهبية في فصل الخريف الساحر.",
        "emoji": "🍂",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🏝️ بانر الجزر الاستوائية الهادئة (Tropical Paradise Coast)",
        "price": 9500,
        "description": "رمال بيضاء ناعمة ومياه تركوازية صافية في جزيرة استوائية.",
        "emoji": "🏝️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌿 بانر السراخس والأدغال الاستوائية (Tropical Fern Jungle)",
        "price": 9000,
        "description": "أدغال استوائية كثيفة بنقاط ضوء الشمس المتسللة عبر الأشجار.",
        "emoji": "🌿",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=1200&h=600&fit=crop&q=80"
    },

    # --- NATURAL PHENOMENA & DISASTERS (10 Banners: Lightning, Volcanoes, Floods, Storms) ---
    {
        "name": "⚡ بانر عاصفة البرق والرعد الكبرى (Cataclysmic Lightning Storm)",
        "price": 13500,
        "description": "صواعق برق عملاقة تشق سماء عاصفة مظلمة وعنيفة.",
        "emoji": "⚡",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌋 بانر ثوران بركان الحمم الغاضبة (Raging Volcanic Eruption)",
        "price": 14000,
        "description": "انفجار بركاني مهيب يطلق حمماً متوهجة وسحب رماد عملاقة.",
        "emoji": "🌋",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌊 بانر فيضان التسونامي الهادر (Tsunami Oceanic Surge)",
        "price": 14500,
        "description": "أمواج عملاقة وهادرة تعكس قوة الطبيعة الجارفة.",
        "emoji": "🌊",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌪️ بانر إعصار التورنادو المدمر (Destructive Tornado Vortex)",
        "price": 14000,
        "description": "دوامة إعصار قمعية هائلة تجتاح السهوب بقوة فائقة.",
        "emoji": "🌪️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1527482797697-8795b05813fe?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "⚡ بانر صواعق العاصفة الليلية (Night Lightning Strikes)",
        "price": 12500,
        "description": "ضربات برق متفرقة تضيء السحاب الأسود في جو عاصف.",
        "emoji": "⚡",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "☄️ بانر سقوط النيازك المشتعلة (Burning Meteor Shower)",
        "price": 13500,
        "description": "نيزك ملتهب يشق الغلاف الجوي بكتلة من النار والشرار.",
        "emoji": "☄️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌊 بانر طوفان السيول العارمة (Torrential Flash Flood)",
        "price": 13000,
        "description": "اندفاع مياه السيول الجارفة عبر الوديان والصخور.",
        "emoji": "🌊",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌋 بانر أنهار الحمم المنصهِرة (Molten Lava Rivers)",
        "price": 14000,
        "description": "تيارات الحمم البركانية المتوهجة تشق طريقها وسط الصخور.",
        "emoji": "🌋",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌪️ بانر عاصفة الغبار والرياح الكبرى (Catastrophic Dust Storm)",
        "price": 12500,
        "description": "جدار عملاق من الأتربة والعواصف الرملية الهائجة.",
        "emoji": "🌪️",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&h=600&fit=crop&q=80"
    },
    {
        "name": "🌀 بانر الدوامة المائية المحيطية (Oceanic Whirlpool Abyss)",
        "price": 13500,
        "description": "دووامة بحرية عميقة ومرعبة في قلب المحيط الهائج.",
        "emoji": "🌀",
        "type": "BANNER",
        "data": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&h=600&fit=crop&q=80"
    }
]

class ShopRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_default_banner_products(self):
        """Seeds default customizable profile banners if not present and updates URLs if modified"""
        for banner in DEFAULT_BANNERS:
            stmt = select(ShopProduct).where(ShopProduct.name == banner["name"])
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                p = ShopProduct(
                    name=banner["name"],
                    price=banner["price"],
                    description=banner["description"],
                    emoji=banner["emoji"],
                    type=banner["type"],
                    data=banner["data"],
                    stock=-1,
                    max_per_user=1,
                    enabled=True,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self.session.add(p)
            else:
                existing.data = banner["data"]
                existing.price = banner["price"]
                existing.description = banner["description"]
                existing.emoji = banner["emoji"]
                existing.updated_at = utc_now()
        try:
            await self.session.commit()
        except Exception as e:
            logger.warning(f"Failed to seed default banners: {e}")
            await self.session.rollback()

    async def get_product(self, product_id: int) -> Optional[ShopProduct]:
        stmt = select(ShopProduct).where(ShopProduct.product_id == product_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_products(self, enabled_only: bool = True) -> List[ShopProduct]:
        stmt = select(ShopProduct)
        if enabled_only:
            stmt = stmt.where(ShopProduct.enabled == True)
        stmt = stmt.order_by(ShopProduct.product_id.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_product(
        self,
        name: str,
        price: int,
        description: Optional[str] = None,
        emoji: Optional[str] = "📦",
        stock: int = -1,
        max_per_user: int = -1,
        type: str = "ROLE",
        role_id: Optional[int] = None,
        data: Optional[str] = None,
        enabled: bool = True
    ) -> ShopProduct:
        product = ShopProduct(
            name=name,
            price=price,
            description=description,
            emoji=emoji or "📦",
            stock=stock,
            max_per_user=max_per_user,
            type=type.upper().strip(),
            role_id=role_id,
            data=data,
            enabled=enabled,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_product(self, product_id: int, **kwargs) -> Optional[ShopProduct]:
        product = await self.get_product(product_id)
        if not product:
            return None

        for key, val in kwargs.items():
            if hasattr(product, key) and val is not None:
                setattr(product, key, val)
        product.updated_at = utc_now()
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete_product(self, product_id: int) -> bool:
        product = await self.get_product(product_id)
        if not product:
            return False
        await self.session.delete(product)
        await self.session.commit()
        return True

    async def get_user_inventory(self, user_id: int) -> List[Tuple[ShopProduct, int]]:
        stmt = select(ShopProduct, UserInventory.quantity).join(
            UserInventory, ShopProduct.product_id == UserInventory.product_id
        ).where(UserInventory.user_id == user_id)
        res = await self.session.execute(stmt)
        return list(res.all())

    async def get_user_item_count(self, user_id: int, product_id: int) -> int:
        stmt = select(UserInventory.quantity).where(
            UserInventory.user_id == user_id,
            UserInventory.product_id == product_id
        )
        res = await self.session.execute(stmt)
        qty = res.scalar_one_or_none()
        return qty or 0

    async def purchase_product_atomic(self, user_id: int, product_id: int) -> Tuple[bool, str, Optional[ShopProduct]]:
        """
        Atomically handles wallet deduction, stock decrement, inventory increment, and transaction recording.
        """
        try:
            # Lock product and wallet
            stmt_p = select(ShopProduct).where(ShopProduct.product_id == product_id).with_for_update()
            res_p = await self.session.execute(stmt_p)
            product = res_p.scalar_one_or_none()

            if not product or not product.enabled:
                await self.session.rollback()
                return False, "هذا المنتج غير متاح في المتجر حاليًا!", None

            if product.stock == 0:
                await self.session.rollback()
                return False, "عذرًا، نفد مخزون هذا المنتج بالكامل!", product

            # Check max per user
            current_qty = await self.get_user_item_count(user_id, product_id)
            if product.max_per_user > 0 and current_qty >= product.max_per_user:
                await self.session.rollback()
                return False, f"لقد وصلت للحد الأقصى المسموح بشرائه لهذا المنتج (`{product.max_per_user}` قطعة)!", product

            # Check wallet
            stmt_w = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
            res_w = await self.session.execute(stmt_w)
            wallet = res_w.scalar_one_or_none()

            if not wallet or wallet.balance < product.price:
                curr_bal = wallet.balance if wallet else 0
                await self.session.rollback()
                return False, f"رصيدك الحالي (`{curr_bal}` {settings.CURRENCY_NAME}) غير كافٍ لشراء هذا المنتج (`{product.price}` {settings.CURRENCY_NAME})!", product

            # Deduct wallet
            b_before = wallet.balance
            wallet.balance -= product.price
            wallet.updated_at = datetime.now(timezone.utc)

            # Decrement stock if not unlimited (-1)
            if product.stock > 0:
                product.stock -= 1

            # Update inventory
            stmt_inv = select(UserInventory).where(
                UserInventory.user_id == user_id,
                UserInventory.product_id == product_id
            ).with_for_update()
            res_inv = await self.session.execute(stmt_inv)
            inv_item = res_inv.scalar_one_or_none()

            if inv_item:
                inv_item.quantity += 1
                inv_item.updated_at = datetime.now(timezone.utc)
            else:
                inv_item = UserInventory(user_id=user_id, product_id=product_id, quantity=1)
                self.session.add(inv_item)

            # Record transaction
            tx = Transaction(
                user_id=user_id,
                guild_id=None,
                type="PURCHASE",
                amount=-product.price,
                balance_before=b_before,
                balance_after=wallet.balance,
                reason=f"Bought item #{product.product_id}: {product.name}"
            )
            self.session.add(tx)
            await self.session.commit()

            return True, f"تم شراء `{product.name}` بنجاح بسعر `{product.price}` {settings.CURRENCY_NAME}!", product
        except Exception as e:
            logger.error(f"Error in purchase: {e}")
            await self.session.rollback()
            return False, "حدث خطأ أثناء إتمام عملية الشراء.", None
