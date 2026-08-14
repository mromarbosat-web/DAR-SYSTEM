import io
import logging
from typing import Optional, List, Dict, Any, Tuple
import aiohttp
import discord

logger = logging.getLogger("discord_bot.leaderboard_card")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow is not installed. Leaderboard will fall back to embed display.")

from bot.utils.arabic_text import process_bidi_text
from bot.utils.card_generator import get_system_font, fetch_image, make_circle_avatar

def format_activity_score(activity_type: str, score: int) -> str:
    """Formats raw score into an elegant Arabic display string."""
    if activity_type == "text":
        if score == 1:
            return "1 رسالة"
        elif score == 2:
            return "رسالتان"
        elif 3 <= score <= 10:
            return f"{score} رسائل"
        else:
            return f"{score:,} رسالة"
    else: # voice seconds
        if score < 60:
            return f"{score} ثانية"
        minutes = score // 60
        if minutes < 60:
            return f"{minutes} دقيقة"
        hours = minutes // 60
        rem_mins = minutes % 60
        if rem_mins == 0:
            return f"{hours} ساعة"
        return f"{hours}س {rem_mins}د"

def draw_rounded_glass_rect(
    draw: ImageDraw.ImageDraw,
    bounds: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int, int],
    outline: Optional[Tuple[int, int, int, int]] = None,
    width: int = 1
):
    """Draws a smooth rounded rectangle with optional border."""
    draw.rounded_rectangle(bounds, radius=radius, fill=fill, outline=outline, width=width)

async def generate_leaderboard_card(
    guild: discord.Guild,
    activity_type: str, # "text" or "voice"
    period: str, # "daily", "weekly", "monthly", "all_time"
    entries: List[Dict[str, Any]], # list of {"rank": int, "user_id": int, "name": str, "avatar_url": str, "score": int}
    total_participants: int = 0
) -> Optional[io.BytesIO]:
    """
    Generates a ultra-luxury, high-definition Leaderboard Card PNG containing:
    1. Grand Header with activity type & time-period badges.
    2. Honors Podium for Top 3 (🥇 Gold, 🥈 Silver, 🥉 Bronze) with large avatars, crowns, podium platforms, and stats.
    3. Sleek horizontal list cards for Ranks #4 to #10 with small avatars, rank tags, and stat pills.
    """
    if not PIL_AVAILABLE:
        return None

    card_w, card_h = 1000, 1180

    # Base Background Canvas (Deep luxury space nebula gradient)
    card = Image.new("RGBA", (card_w, card_h), (11, 13, 23, 255))
    
    # Create subtle ambient glow gradient overlay
    overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # Ambient Top Glow
    if activity_type == "text":
        glow_color = (88, 101, 242, 60) # Discord Blurple / Blue Glow
        accent_color = (114, 137, 218, 255)
        type_title = "💬 توب الكتابة والرسائل (Chat Activity)"
        icon_symbol = "💬"
    else:
        glow_color = (46, 204, 113, 60) # Emerald / Green Glow
        accent_color = (46, 204, 113, 255)
        type_title = "🎙️ توب الرومات الصوتية (Voice Activity)"
        icon_symbol = "🎙️"

    period_titles = {
        "daily": "📅 المتصدرين اليوم (Daily Top)",
        "weekly": "📆 متصدري الأسبوع (Weekly Top)",
        "monthly": "🗓️ متصدري الشهر (Monthly Top)",
        "all_time": "🌐 المتصدرين الكلي (All-Time Top)"
    }
    period_title = period_titles.get(period, "📅 المتصدرين")

    # Draw Top Radial Light Effect
    draw_ov.ellipse([(-100, -100), (card_w + 100, 350)], fill=glow_color)
    draw_ov.ellipse([(card_w // 2 - 250, 150), (card_w // 2 + 250, 450)], fill=(255, 215, 0, 25))

    # Outer decorative frame
    draw_ov.rounded_rectangle(
        [(14, 14), (card_w - 14, card_h - 14)],
        radius=24,
        fill=(15, 18, 30, 225),
        outline=(255, 255, 255, 35),
        width=2
    )

    card = Image.alpha_composite(card, overlay)
    draw = ImageDraw.Draw(card)

    # Fonts
    font_title = get_system_font(34, bold=True)
    font_subtitle = get_system_font(18, bold=True)
    font_podium_name = get_system_font(20, bold=True)
    font_podium_score = get_system_font(17, bold=True)
    font_rank = get_system_font(18, bold=True)
    font_list_name = get_system_font(19, bold=True)
    font_list_score = get_system_font(17, bold=True)
    font_footer = get_system_font(14, bold=False)

    # 1. Header Section
    header_y = 36
    main_title_text = process_bidi_text(f"🏆 {guild.name} • لوحة الشرف")
    draw.text((card_w // 2, header_y), main_title_text, fill=(255, 255, 255, 255), font=font_title, anchor="mm")

    # Header Subtitle Pill Badges
    badge_y = 82
    cat_text = process_bidi_text(f"{type_title}  |  {period_title}")
    # Draw pill container for subtitle
    pill_w = min(680, int(len(cat_text) * 11 + 60))
    pill_x1 = (card_w - pill_w) // 2
    draw_rounded_glass_rect(draw, (pill_x1, badge_y - 14, pill_x1 + pill_w, badge_y + 16), radius=15, fill=(25, 30, 50, 200), outline=(255, 255, 255, 45), width=1)
    draw.text((card_w // 2, badge_y), cat_text, fill=accent_color, font=font_subtitle, anchor="mm")

    # Separate Header from Podium
    draw.line([(60, 118), (card_w - 60, 118)], fill=(255, 255, 255, 25), width=1)

    # 2. Top 3 Honors Podium Section (مراتب الشرف)
    # Entry map by rank: 1, 2, 3
    top_entries = {e["rank"]: e for e in entries if e["rank"] <= 3}

    # Configuration for Top 3 podium slots
    # #2 is on left, #1 in center (taller/larger), #3 on right
    podium_configs = [
        {
            "rank": 2,
            "center_x": 210,
            "box_top": 195,
            "box_bottom": 445,
            "av_size": 94,
            "av_y": 140,
            "border_color": (192, 192, 192, 255), # Silver
            "ring_color": (220, 225, 235, 255),
            "platform_color": (35, 42, 65, 210),
            "badge_text": "🥈 #2",
            "crown": "🥈"
        },
        {
            "rank": 1,
            "center_x": 500,
            "box_top": 165,
            "box_bottom": 455,
            "av_size": 112,
            "av_y": 105,
            "border_color": (255, 215, 0, 255), # Gold
            "ring_color": (255, 223, 70, 255),
            "platform_color": (45, 40, 25, 230),
            "badge_text": "👑 🥇 #1",
            "crown": "👑"
        },
        {
            "rank": 3,
            "center_x": 790,
            "box_top": 215,
            "box_bottom": 445,
            "av_size": 94,
            "av_y": 160,
            "border_color": (205, 127, 50, 255), # Bronze
            "ring_color": (225, 155, 95, 255),
            "platform_color": (40, 32, 28, 210),
            "badge_text": "🥉 #3",
            "crown": "🥉"
        }
    ]

    for cfg in podium_configs:
        cx = cfg["center_x"]
        rank_num = cfg["rank"]
        entry = top_entries.get(rank_num)

        # Draw Podium Platform Card
        p_w = 240 if rank_num != 1 else 270
        p_x1 = cx - p_w // 2
        p_x2 = cx + p_w // 2
        p_y1 = cfg["box_top"]
        p_y2 = cfg["box_bottom"]

        # Platform pedestal
        draw_rounded_glass_rect(
            draw,
            (p_x1, p_y1, p_x2, p_y2),
            radius=18,
            fill=cfg["platform_color"],
            outline=cfg["border_color"],
            width=2 if rank_num == 1 else 1
        )

        # Draw Avatar
        av_s = cfg["av_size"]
        av_y = cfg["av_y"]
        av_x = cx - av_s // 2

        if entry and entry.get("avatar_url"):
            av_bytes = await fetch_image(entry["avatar_url"])
        else:
            av_bytes = None

        if av_bytes:
            try:
                raw_av = Image.open(io.BytesIO(av_bytes))
                circ_av = make_circle_avatar(raw_av, av_s)
                
                # Glowing ring
                ring_pad = 4
                draw.ellipse(
                    [(av_x - ring_pad, av_y - ring_pad), (av_x + av_s + ring_pad, av_y + av_s + ring_pad)],
                    fill=cfg["border_color"]
                )
                card.paste(circ_av, (av_x, av_y), circ_av)
                draw = ImageDraw.Draw(card)
            except Exception:
                draw.ellipse([(av_x, av_y), (av_x + av_s, av_y + av_s)], fill=(50, 55, 75, 255), outline=cfg["border_color"], width=3)
        else:
            # Fallback circle placeholder
            draw.ellipse([(av_x, av_y), (av_x + av_s, av_y + av_s)], fill=(40, 45, 65, 255), outline=cfg["border_color"], width=3)
            placeholder_symbol = "👑" if rank_num == 1 else ("🥈" if rank_num == 2 else "🥉")
            draw.text((cx, av_y + av_s // 2), placeholder_symbol, fill=(255, 255, 255, 200), font=font_subtitle, anchor="mm")

        # Podium Rank Badge Pill
        badge_y = av_y + av_s + 14
        b_w = 110 if rank_num == 1 else 86
        draw_rounded_glass_rect(
            draw,
            (cx - b_w // 2, badge_y - 12, cx + b_w // 2, badge_y + 14),
            radius=12,
            fill=(15, 18, 28, 240),
            outline=cfg["border_color"],
            width=2 if rank_num == 1 else 1
        )
        draw.text((cx, badge_y), cfg["badge_text"], fill=cfg["border_color"], font=font_subtitle, anchor="mm")

        # User Name
        name_y = badge_y + 36
        if entry:
            disp_name = entry["name"]
            if len(disp_name) > 14:
                disp_name = disp_name[:13] + "…"
            name_text = process_bidi_text(disp_name)
            name_color = (255, 235, 160, 255) if rank_num == 1 else (240, 243, 250, 255)
            draw.text((cx, name_y), name_text, fill=name_color, font=font_podium_name, anchor="mm")

            # Score Pill
            score_y = name_y + 36
            formatted_score = format_activity_score(activity_type, entry["score"])
            score_text = process_bidi_text(formatted_score)
            
            sc_pill_w = min(p_w - 24, int(len(formatted_score) * 10 + 36))
            draw_rounded_glass_rect(
                draw,
                (cx - sc_pill_w // 2, score_y - 12, cx + sc_pill_w // 2, score_y + 14),
                radius=10,
                fill=(20, 24, 38, 230),
                outline=(255, 255, 255, 30),
                width=1
            )
            draw.text((cx, score_y), score_text, fill=(255, 215, 0, 255) if rank_num == 1 else (160, 220, 255, 255), font=font_podium_score, anchor="mm")
        else:
            empty_text = process_bidi_text("— شاغر —")
            draw.text((cx, name_y), empty_text, fill=(130, 140, 160, 200), font=font_subtitle, anchor="mm")

    # Divider between Top 3 and List (#4 - #10)
    list_start_y = 475
    draw.line([(50, list_start_y - 12), (card_w - 50, list_start_y - 12)], fill=(255, 255, 255, 25), width=1)

    # 3. List Section for Ranks #4 to #10 (المراكز من الرابع للعاشر)
    bottom_entries = [e for e in entries if 4 <= e["rank"] <= 10]
    row_h = 80
    row_pad = 10
    row_x1 = 50
    row_x2 = card_w - 50

    # Ensure 7 slots for #4 to #10
    for idx, slot_rank in enumerate(range(4, 11)):
        curr_y = list_start_y + idx * (row_h + row_pad)
        if curr_y + row_h > card_h - 45:
            break

        # Find entry for this rank
        entry = next((e for e in bottom_entries if e["rank"] == slot_rank), None)

        # Row Background Card
        row_bg_fill = (22, 26, 42, 190) if idx % 2 == 0 else (28, 33, 52, 190)
        draw_rounded_glass_rect(
            draw,
            (row_x1, curr_y, row_x2, curr_y + row_h),
            radius=14,
            fill=row_bg_fill,
            outline=(255, 255, 255, 25),
            width=1
        )

        # Rank Number Badge on the Left
        rank_pill_x = row_x1 + 42
        rank_pill_y = curr_y + row_h // 2
        draw_rounded_glass_rect(
            draw,
            (rank_pill_x - 24, rank_pill_y - 16, rank_pill_x + 24, rank_pill_y + 16),
            radius=10,
            fill=(15, 18, 30, 240),
            outline=(255, 255, 255, 40),
            width=1
        )
        draw.text((rank_pill_x, rank_pill_y), f"#{slot_rank}", fill=(180, 195, 220, 255), font=font_rank, anchor="mm")

        # Mini Avatar (diameter ~50px)
        av_d = 50
        av_x = row_x1 + 82
        av_y = curr_y + (row_h - av_d) // 2

        if entry:
            av_bytes = await fetch_image(entry.get("avatar_url", "")) if entry.get("avatar_url") else None
            if av_bytes:
                try:
                    raw_av = Image.open(io.BytesIO(av_bytes))
                    circ_av = make_circle_avatar(raw_av, av_d)
                    draw.ellipse([(av_x - 2, av_y - 2), (av_x + av_d + 2, av_y + av_d + 2)], fill=(70, 80, 110, 255))
                    card.paste(circ_av, (av_x, av_y), circ_av)
                    draw = ImageDraw.Draw(card)
                except Exception:
                    draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(45, 52, 75, 255), outline=(255, 255, 255, 40))
            else:
                draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(45, 52, 75, 255), outline=(255, 255, 255, 40))
                draw.text((av_x + av_d // 2, av_y + av_d // 2), f"{slot_rank}", fill=(200, 210, 230, 200), font=font_rank, anchor="mm")

            # User Name
            name_x = av_x + av_d + 18
            name_y = curr_y + row_h // 2
            raw_name = entry["name"]
            if len(raw_name) > 22:
                raw_name = raw_name[:21] + "…"
            name_text = process_bidi_text(raw_name)
            draw.text((name_x, name_y), name_text, fill=(245, 248, 255, 255), font=font_list_name, anchor="lm")

            # Activity Stat Badge on the Right
            stat_pill_w = 175
            stat_pill_x2 = row_x2 - 20
            stat_pill_x1 = stat_pill_x2 - stat_pill_w
            stat_pill_y1 = curr_y + 18
            stat_pill_y2 = curr_y + row_h - 18

            draw_rounded_glass_rect(
                draw,
                (stat_pill_x1, stat_pill_y1, stat_pill_x2, stat_pill_y2),
                radius=12,
                fill=(16, 20, 32, 230),
                outline=(255, 255, 255, 30),
                width=1
            )
            formatted_stat = format_activity_score(activity_type, entry["score"])
            stat_text = process_bidi_text(f"{icon_symbol} {formatted_stat}")
            draw.text(((stat_pill_x1 + stat_pill_x2) // 2, (stat_pill_y1 + stat_pill_y2) // 2), stat_text, fill=accent_color, font=font_list_score, anchor="mm")

        else:
            # Empty slot
            draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(32, 38, 55, 180), outline=(255, 255, 255, 20))
            name_x = av_x + av_d + 18
            name_y = curr_y + row_h // 2
            draw.text((name_x, name_y), process_bidi_text("— لا يوجد متصدر بعد —"), fill=(110, 120, 145, 180), font=font_subtitle, anchor="lm")

    # 4. Footer Branding
    footer_text = process_bidi_text("⚡ نظام إحصائيات التوب الفائق • يتم التحديث دورياً كل 3 ثوانٍ")
    draw.text((card_w // 2, card_h - 24), footer_text, fill=(130, 140, 165, 200), font=font_footer, anchor="mm")

    # Output to BytesIO buffer
    buffer = io.BytesIO()
    card.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
