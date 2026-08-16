import io
import os
import logging
from typing import Optional, List, Dict, Any, Tuple
import aiohttp
import discord

logger = logging.getLogger("discord_bot.leaderboard_card")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    Image = ImageDraw = ImageFont = ImageFilter = ImageOps = None  # type: ignore
    PIL_AVAILABLE = False
    logger.warning("Pillow is not installed. Leaderboard will fall back to embed display.")

from bot.utils.card_generator import get_latin_font, fetch_image, make_circle_avatar

def draw_rounded_glass_box(
    draw: Any,
    bounds: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int, int],
    outline: Optional[Tuple[int, int, int, int]] = None,
    width: int = 1
):
    """Draws a smooth rounded rectangle with optional border."""
    draw.rounded_rectangle(bounds, radius=radius, fill=fill, outline=outline, width=width)

def draw_hexagon_badge(
    draw: Any,
    center: Tuple[int, int],
    size: int,
    fill: Tuple[int, int, int, int],
    outline: Tuple[int, int, int, int],
    width: int = 2
):
    """Draws a futuristic tech hexagon badge."""
    cx, cy = center
    r = size
    # 6 points of hexagon
    points = [
        (cx, cy - r),
        (cx + int(r * 0.866), cy - int(r * 0.5)),
        (cx + int(r * 0.866), cy + int(r * 0.5)),
        (cx, cy + r),
        (cx - int(r * 0.866), cy + int(r * 0.5)),
        (cx - int(r * 0.866), cy - int(r * 0.5)),
    ]
    draw.polygon(points, fill=fill, outline=outline, width=width)

async def generate_leaderboard_card(
    guild: discord.Guild,
    activity_type: str,  # "text" or "voice"
    period: str,         # "daily", "weekly", "monthly", "all_time"
    entries: List[Dict[str, Any]],  # list of {"rank": int, "user_id": int, "name": str, "avatar_url": str, "score": int, "level": int, "xp": int}
    total_participants: int = 0
) -> Optional[io.BytesIO]:
    """
    Generates a premium Cyberpunk / Dark UI Leaderboard Card PNG matching the visual reference:
    - 1500 x 1000 px high-definition canvas.
    - All LTR, English only, Discord `user.name` only.
    - Top 3 Podium: #1 in center (large & prominent), #2 on left (silver/ice blue), #3 on right (bronze/copper).
    - Table for ranks #4 to #10: Rank, Avatar + Username, Level, XP.
    - Bottom pill footer: ★ KEEP ACTIVE, CLIMB HIGHER ///
    """
    if not PIL_AVAILABLE:
        return None

    card_w, card_h = 1500, 1000

    # 1. Base Dark Cyberpunk Canvas
    card = Image.new("RGBA", (card_w, card_h), (9, 12, 22, 255))
    
    # Glow / Ambient Lighting Layer
    ambient = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_amb = ImageDraw.Draw(ambient)

    # Ambient Top Glows (Golden Center, Cyan Left, Orange Right, Violet Corners)
    draw_amb.ellipse([(card_w // 2 - 300, -100), (card_w // 2 + 300, 400)], fill=(255, 200, 40, 30))   # Gold #1 Glow
    draw_amb.ellipse([(60, 40), (520, 500)], fill=(0, 200, 255, 25))                                   # Cyan #2 Glow
    draw_amb.ellipse([(card_w - 520, 40), (card_w - 60, 500)], fill=(255, 120, 50, 22))               # Bronze #3 Glow
    draw_amb.ellipse([(-150, -150), (350, 350)], fill=(138, 43, 226, 35))                             # Purple Top-Left
    draw_amb.ellipse([(card_w - 350, -150), (card_w + 150, 350)], fill=(75, 0, 130, 35))              # Deep Violet Top-Right

    # Subtle Cyber Grid Lines & Tech Crosshairs
    for y_pos in range(120, card_h - 60, 60):
        draw_amb.line([(40, y_pos), (card_w - 40, y_pos)], fill=(255, 255, 255, 5), width=1)
    for x_pos in range(100, card_w, 150):
        draw_amb.line([(x_pos, 100), (x_pos, card_h - 60)], fill=(255, 255, 255, 4), width=1)

    # Outer Cyber Container Frame
    draw_amb.rounded_rectangle(
        [(18, 18), (card_w - 18, card_h - 18)],
        radius=20,
        fill=(11, 14, 26, 210),
        outline=(60, 75, 125, 90),
        width=2
    )

    card = Image.alpha_composite(card, ambient)
    draw = ImageDraw.Draw(card)

    # Fonts
    font_crown = get_latin_font(26, bold=True)
    font_title = get_latin_font(38, bold=True)
    font_subtitle = get_latin_font(14, bold=True)
    font_badge_num = get_latin_font(18, bold=True)
    font_badge_num_lg = get_latin_font(22, bold=True)
    
    font_p1_name = get_latin_font(22, bold=True)
    font_p_name = get_latin_font(19, bold=True)
    
    font_label = get_latin_font(12, bold=True)
    font_val_lg = get_latin_font(18, bold=True)
    font_val = get_latin_font(15, bold=True)
    
    font_th = get_latin_font(14, bold=True)
    font_row_rank = get_latin_font(16, bold=True)
    font_row_name = get_latin_font(16, bold=True)
    font_row_lvl = get_latin_font(15, bold=True)
    font_row_xp = get_latin_font(15, bold=True)
    font_footer = get_latin_font(13, bold=True)

    # 2. Header Section
    # Crown icon
    draw.text((card_w // 2, 40), "👑", fill=(255, 215, 0, 255), font=font_crown, anchor="mm")
    
    # Title: TOP USERS
    title_y = 75
    draw.text((card_w // 2 + 1, title_y + 1), "TOP USERS", fill=(0, 0, 0, 200), font=font_title, anchor="mm")
    draw.text((card_w // 2, title_y), "TOP USERS", fill=(255, 255, 255, 255), font=font_title, anchor="mm")

    # Subtitle: LEADERBOARD with glowing side wings
    sub_y = 112
    draw.line([(card_w // 2 - 210, sub_y), (card_w // 2 - 95, sub_y)], fill=(168, 85, 247, 180), width=2)
    draw.line([(card_w // 2 + 95, sub_y), (card_w // 2 + 210, sub_y)], fill=(168, 85, 247, 180), width=2)
    draw.ellipse([(card_w // 2 - 215, sub_y - 3), (card_w // 2 - 209, sub_y + 3)], fill=(168, 85, 247, 255))
    draw.ellipse([(card_w // 2 + 209, sub_y - 3), (card_w // 2 + 215, sub_y + 3)], fill=(168, 85, 247, 255))
    draw.text((card_w // 2, sub_y), "LEADERBOARD", fill=(192, 132, 252, 255), font=font_subtitle, anchor="mm")

    # 3. Top 3 Podium Configuration
    # Find entries for rank 1, 2, 3
    top_entries = {e["rank"]: e for e in entries if e["rank"] <= 3}

    podium_configs = [
        # Rank 2 (Left)
        {
            "rank": 2,
            "cx": 310,
            "card_w": 320,
            "y1": 170,
            "y2": 500,
            "av_size": 98,
            "av_y": 210,
            "theme_color": (0, 215, 255, 255),         # Ice Cyan / Silver Blue
            "theme_glow": (0, 215, 255, 120),
            "frame_border": (70, 160, 230, 200),
            "card_fill": (14, 20, 36, 235),
            "badge_color": (0, 215, 255, 255),
            "accent": "🔹"
        },
        # Rank 1 (Center - Largest)
        {
            "rank": 1,
            "cx": 750,
            "card_w": 380,
            "y1": 150,
            "y2": 515,
            "av_size": 118,
            "av_y": 190,
            "theme_color": (255, 215, 0, 255),         # Gold
            "theme_glow": (255, 215, 0, 160),
            "frame_border": (255, 215, 0, 230),
            "card_fill": (24, 22, 18, 245),
            "badge_color": (255, 215, 0, 255),
            "accent": "👑"
        },
        # Rank 3 (Right)
        {
            "rank": 3,
            "cx": 1190,
            "card_w": 320,
            "y1": 170,
            "y2": 500,
            "av_size": 98,
            "av_y": 210,
            "theme_color": (245, 145, 80, 255),        # Bronze / Copper Orange
            "theme_glow": (245, 145, 80, 120),
            "frame_border": (210, 120, 65, 200),
            "card_fill": (24, 18, 16, 235),
            "badge_color": (245, 145, 80, 255),
            "accent": "🔸"
        }
    ]

    for cfg in podium_configs:
        cx = cfg["cx"]
        rank_num = cfg["rank"]
        pw = cfg["card_w"]
        px1 = cx - pw // 2
        px2 = cx + pw // 2
        py1 = cfg["y1"]
        py2 = cfg["y2"]
        is_p1 = rank_num == 1
        entry = top_entries.get(rank_num)

        # Card Box
        draw_rounded_glass_box(
            draw,
            (px1, py1, px2, py2),
            radius=18,
            fill=cfg["card_fill"],
            outline=cfg["frame_border"],
            width=2 if is_p1 else 1
        )

        # Inner subtle bevel
        draw_rounded_glass_box(
            draw,
            (px1 + 4, py1 + 4, px2 - 4, py2 - 4),
            radius=15,
            fill=(0, 0, 0, 0),
            outline=(255, 255, 255, 18),
            width=1
        )

        # Top Badge: Hexagon with Rank Number (#1, #2, #3)
        badge_cy = py1 + 2
        draw_hexagon_badge(
            draw,
            center=(cx, badge_cy),
            size=22 if is_p1 else 18,
            fill=(16, 18, 30, 255),
            outline=cfg["theme_color"],
            width=2
        )
        draw.text(
            (cx, badge_cy),
            str(rank_num),
            fill=cfg["badge_color"],
            font=font_badge_num_lg if is_p1 else font_badge_num,
            anchor="mm"
        )

        # Circular Avatar
        av_size = cfg["av_size"]
        av_y = cfg["av_y"]
        av_x = cx - av_size // 2

        # Glowing ring behind avatar
        ring_pad = 4
        draw.ellipse(
            [(av_x - ring_pad, av_y - ring_pad), (av_x + av_size + ring_pad, av_y + av_size + ring_pad)],
            fill=cfg["theme_color"]
        )

        if entry and entry.get("avatar_url"):
            av_bytes = await fetch_image(entry["avatar_url"])
            if av_bytes:
                try:
                    raw_av = Image.open(io.BytesIO(av_bytes))
                    circ_av = make_circle_avatar(raw_av, av_size)
                    card.paste(circ_av, (av_x, av_y), circ_av)
                    draw = ImageDraw.Draw(card)
                except Exception:
                    draw.ellipse([(av_x, av_y), (av_x + av_size, av_y + av_size)], fill=(28, 32, 50, 255))
            else:
                draw.ellipse([(av_x, av_y), (av_x + av_size, av_y + av_size)], fill=(28, 32, 50, 255))
        else:
            draw.ellipse([(av_x, av_y), (av_x + av_size, av_y + av_size)], fill=(24, 28, 44, 255))
            draw.text((cx, av_y + av_size // 2), cfg["accent"], font=font_crown, anchor="mm")

        # User Name (Discord username: `user.name` only, strictly LTR)
        name_y = av_y + av_size + 24
        if entry:
            username = entry.get("name", "Unknown")
            # Truncate gracefully if excessively long
            if len(username) > 16:
                username = username[:15] + "…"
            name_color = (255, 255, 255, 255)
            draw.text((cx, name_y), username, fill=name_color, font=font_p1_name if is_p1 else font_p_name, anchor="mm")

            # Stat Box (LEVEL & XP)
            stat_box_y1 = name_y + 20
            stat_box_y2 = py2 - 20
            box_inner_w = pw - 36
            sb_x1 = cx - box_inner_w // 2
            sb_x2 = cx + box_inner_w // 2

            draw_rounded_glass_box(
                draw,
                (sb_x1, stat_box_y1, sb_x2, stat_box_y2),
                radius=10,
                fill=(12, 15, 26, 220),
                outline=(255, 255, 255, 25),
                width=1
            )

            # Two columns: Left = LEVEL, Right = XP
            mid_divider_x = cx
            draw.line([(mid_divider_x, stat_box_y1 + 8), (mid_divider_x, stat_box_y2 - 8)], fill=(255, 255, 255, 25), width=1)

            col1_cx = (sb_x1 + mid_divider_x) // 2
            col2_cx = (mid_divider_x + sb_x2) // 2
            
            # Level Column
            lvl_val = entry.get("level", 1)
            draw.text((col1_cx, stat_box_y1 + 14), "LEVEL", fill=(140, 155, 185, 255), font=font_label, anchor="mm")
            draw.text((col1_cx, stat_box_y1 + 34), str(lvl_val), fill=cfg["theme_color"], font=font_val_lg if is_p1 else font_val, anchor="mm")

            # XP Column
            xp_val = entry.get("xp", entry.get("score", 0))
            xp_str = f"{xp_val:,}"
            draw.text((col2_cx, stat_box_y1 + 14), "XP", fill=(140, 155, 185, 255), font=font_label, anchor="mm")
            draw.text((col2_cx, stat_box_y1 + 34), xp_str, fill=(245, 250, 255, 255), font=font_val_lg if is_p1 else font_val, anchor="mm")

        else:
            # Empty / Vacant slot placeholder
            draw.text((cx, name_y), "— VACANT —", fill=(110, 125, 155, 180), font=font_subtitle, anchor="mm")
            draw.text((cx, name_y + 36), "No record yet", fill=(80, 95, 125, 160), font=font_label, anchor="mm")

    # 4. Bottom Table (#4 to #10)
    table_x1 = 60
    table_x2 = card_w - 60
    table_y1 = 540
    table_y2 = 925

    # Glass Table Container
    draw_rounded_glass_box(
        draw,
        (table_x1, table_y1, table_x2, table_y2),
        radius=16,
        fill=(12, 15, 28, 220),
        outline=(70, 90, 150, 65),
        width=1
    )

    # Table Header Row
    th_y = table_y1 + 22
    draw.text((table_x1 + 45, th_y), "🏆  RANK", fill=(140, 160, 200, 255), font=font_th, anchor="lm")
    draw.text((table_x1 + 180, th_y), "👤  USER", fill=(140, 160, 200, 255), font=font_th, anchor="lm")
    draw.text((table_x2 - 420, th_y), "📈  LEVEL", fill=(140, 160, 200, 255), font=font_th, anchor="mm")
    draw.text((table_x2 - 160, th_y), "XP", fill=(140, 160, 200, 255), font=font_th, anchor="mm")

    # Header Bottom Divider Line
    draw.line([(table_x1 + 20, table_y1 + 44), (table_x2 - 20, table_y1 + 44)], fill=(255, 255, 255, 20), width=1)

    # Table Rows for #4 to #10
    bottom_entries = {e["rank"]: e for e in entries if 4 <= e["rank"] <= 10}
    row_height = 46
    start_row_y = table_y1 + 50

    for idx, rank_val in enumerate(range(4, 11)):
        row_y = start_row_y + idx * row_height
        entry = bottom_entries.get(rank_val)

        # Subtle zebra striping
        if idx % 2 == 1:
            draw.rectangle(
                [(table_x1 + 10, row_y + 2), (table_x2 - 10, row_y + row_height - 2)],
                fill=(255, 255, 255, 6)
            )

        mid_y = row_y + row_height // 2

        # 1. Rank Number (in soft neon violet)
        draw.text((table_x1 + 60, mid_y), str(rank_val), fill=(167, 139, 250, 255), font=font_row_rank, anchor="mm")

        # 2. Avatar & Username
        av_dia = 32
        av_left = table_x1 + 140
        av_top = mid_y - av_dia // 2

        if entry:
            av_url = entry.get("avatar_url")
            if av_url:
                av_bytes = await fetch_image(av_url)
                if av_bytes:
                    try:
                        raw_av = Image.open(io.BytesIO(av_bytes))
                        circ_av = make_circle_avatar(raw_av, av_dia)
                        draw.ellipse([(av_left - 1, av_top - 1), (av_left + av_dia + 1, av_top + av_dia + 1)], fill=(59, 130, 246, 200))
                        card.paste(circ_av, (av_left, av_top), circ_av)
                        draw = ImageDraw.Draw(card)
                    except Exception:
                        draw.ellipse([(av_left, av_top), (av_left + av_dia, av_top + av_dia)], fill=(32, 38, 60, 255))
                else:
                    draw.ellipse([(av_left, av_top), (av_left + av_dia, av_top + av_dia)], fill=(32, 38, 60, 255))
            else:
                draw.ellipse([(av_left, av_top), (av_left + av_dia, av_top + av_dia)], fill=(32, 38, 60, 255))

            # Username (Strictly LTR, real Discord user.name)
            u_name = entry.get("name", "Unknown")
            if len(u_name) > 24:
                u_name = u_name[:23] + "…"
            draw.text((av_left + av_dia + 14, mid_y), u_name, fill=(255, 255, 255, 255), font=font_row_name, anchor="lm")

            # 3. Level (in bright cyan/blue)
            u_lvl = entry.get("level", 1)
            draw.text((table_x2 - 420, mid_y), str(u_lvl), fill=(56, 189, 248, 255), font=font_row_lvl, anchor="mm")

            # 4. XP value + XP badge
            u_xp = entry.get("xp", entry.get("score", 0))
            xp_formatted = f"{u_xp:,}"
            draw.text((table_x2 - 160, mid_y), xp_formatted, fill=(240, 245, 255, 255), font=font_row_xp, anchor="mm")
        else:
            # Empty row placeholder
            draw.ellipse([(av_left, av_top), (av_left + av_dia, av_top + av_dia)], fill=(22, 26, 40, 200), outline=(255, 255, 255, 15))
            draw.text((av_left + av_dia + 14, mid_y), "— Empty Slot —", fill=(90, 100, 125, 180), font=font_subtitle, anchor="lm")
            draw.text((table_x2 - 420, mid_y), "—", fill=(90, 100, 125, 180), font=font_row_lvl, anchor="mm")
            draw.text((table_x2 - 160, mid_y), "—", fill=(90, 100, 125, 180), font=font_row_xp, anchor="mm")

    # 5. Bottom Footer Bar: ★  KEEP ACTIVE, CLIMB HIGHER  ///
    footer_cy = 962
    foot_pill_w = 340
    draw_rounded_glass_box(
        draw,
        (card_w // 2 - foot_pill_w // 2, footer_cy - 14, card_w // 2 + foot_pill_w // 2, footer_cy + 14),
        radius=14,
        fill=(14, 17, 30, 240),
        outline=(168, 85, 247, 90),
        width=1
    )
    draw.text((card_w // 2, footer_cy), "★  KEEP ACTIVE, CLIMB HIGHER  ///", fill=(216, 180, 254, 255), font=font_footer, anchor="mm")

    # Output PNG Buffer
    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
