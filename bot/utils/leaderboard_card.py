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
    PIL_AVAILABLE = False
    logger.warning("Pillow is not installed. Leaderboard will fall back to embed display.")

from bot.utils.card_generator import get_system_font, fetch_image, make_circle_avatar

def format_activity_score(activity_type: str, score: int) -> str:
    """Formats raw score into an English activity string."""
    if activity_type == "text":
        if score == 1:
            return "1 Msg"
        return f"{score:,} Msgs"
    else:  # voice seconds
        if score < 60:
            return f"{score}s"
        minutes = score // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        rem_mins = minutes % 60
        if rem_mins == 0:
            return f"{hours}h"
        return f"{hours}h {rem_mins}m"

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
    activity_type: str,  # "text" or "voice"
    period: str,         # "daily", "weekly", "monthly", "all_time"
    entries: List[Dict[str, Any]],  # list of {"rank": int, "user_id": int, "name": str, "avatar_url": str, "score": int, "level": int, "xp": int}
    total_participants: int = 0
) -> Optional[io.BytesIO]:
    """
    Generates a premium Cyberpunk / Dark UI Leaderboard Card PNG matching the /profile card:
    - English only (no Arabic text).
    - Title: 🏆 TOP PLAYERS
    - Subtitle: DAR SYSTEM • LEADERBOARD
    - Top 3 Players: #1 in center (larger), #2 on left, #3 on right with circular avatar, username, level, and XP.
    - Players #4 to #10 in a clean vertical list with rank, circular avatar, username, level, and XP.
    - Integrated full-width cyberpunk dark background with subtle purple & blue neon accents.
    """
    if not PIL_AVAILABLE:
        return None

    card_w, card_h = 1000, 1180

    # 1. Base Deep Cyberpunk Dark Background
    card = Image.new("RGBA", (card_w, card_h), (11, 13, 23, 255))
    
    # Ambient Light & Glow Layer
    overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # Ambient Top Cyberpunk Neon Radial Glows (Purple & Blue)
    draw_ov.ellipse([(card_w // 2 - 360, -120), (card_w // 2 + 360, 420)], fill=(139, 92, 246, 45))  # Neon Violet Top Center
    draw_ov.ellipse([(-120, 120), (360, 560)], fill=(59, 130, 246, 35))                                # Cyber Blue Left
    draw_ov.ellipse([(card_w - 360, 120), (card_w + 120, 560)], fill=(147, 51, 234, 30))             # Purple Right
    draw_ov.ellipse([(card_w // 2 - 180, 140), (card_w // 2 + 180, 460)], fill=(255, 215, 0, 22))    # Gold Champion Accent

    # Subtle Cyberpunk Tech Grid Lines
    grid_y = 160
    while grid_y < card_h - 60:
        draw_ov.line([(25, grid_y), (card_w - 25, grid_y)], fill=(255, 255, 255, 6), width=1)
        grid_y += 65

    # Outer Framed Glass Container (Matching Profile Card styling)
    draw_ov.rounded_rectangle(
        [(14, 14), (card_w - 14, card_h - 14)],
        radius=24,
        fill=(13, 16, 28, 230),
        outline=(255, 255, 255, 38),
        width=2
    )

    card = Image.alpha_composite(card, overlay)
    draw = ImageDraw.Draw(card)

    # Fonts (English & Unicode support)
    font_title = get_system_font(32, bold=True)
    font_subtitle = get_system_font(13, bold=True)
    font_podium_name = get_system_font(19, bold=True)
    font_podium_lvl = get_system_font(13, bold=True)
    font_podium_xp = get_system_font(15, bold=True)
    font_rank_tag = get_system_font(15, bold=True)
    font_list_name = get_system_font(18, bold=True)
    font_list_lvl = get_system_font(13, bold=True)
    font_list_xp = get_system_font(15, bold=True)
    font_footer = get_system_font(13, bold=False)

    # 2. Header Section
    header_y = 44
    title_text = "🏆 TOP PLAYERS"
    draw.text((card_w // 2 + 1, header_y + 1), title_text, fill=(0, 0, 0, 180), font=font_title, anchor="mm")
    draw.text((card_w // 2, header_y), title_text, fill=(255, 255, 255, 255), font=font_title, anchor="mm")

    # Header Subtitle Badge: DAR SYSTEM • LEADERBOARD
    badge_y = 86
    sub_text = "DAR SYSTEM • LEADERBOARD"
    sub_pill_w = 260
    draw_rounded_glass_rect(
        draw,
        (card_w // 2 - sub_pill_w // 2, badge_y - 13, card_w // 2 + sub_pill_w // 2, badge_y + 13),
        radius=12,
        fill=(20, 24, 44, 230),
        outline=(139, 92, 246, 140),
        width=1
    )
    draw.text((card_w // 2, badge_y), sub_text, fill=(196, 181, 253, 255), font=font_subtitle, anchor="mm")

    # Divider line
    draw.line([(55, 118), (card_w - 55, 118)], fill=(255, 255, 255, 28), width=1)

    # 3. Top 3 Podium Section
    top_entries = {e["rank"]: e for e in entries if e["rank"] <= 3}

    # Configuration for Top 3 slots (#2 Left, #1 Center larger, #3 Right)
    podium_configs = [
        {
            "rank": 2,
            "center_x": 215,
            "box_top": 178,
            "box_bottom": 472,
            "av_size": 94,
            "av_y": 140,
            "border_color": (192, 210, 240, 255),    # Silver / Ice Cyan
            "ring_color": (192, 210, 240, 255),
            "platform_fill": (20, 26, 46, 215),
            "badge_text": "🥈 #2",
            "crown": "🥈"
        },
        {
            "rank": 1,
            "center_x": 500,
            "box_top": 150,
            "box_bottom": 484,
            "av_size": 112,
            "av_y": 106,
            "border_color": (255, 215, 0, 255),      # Gold Champion
            "ring_color": (255, 220, 60, 255),
            "platform_fill": (32, 28, 16, 235),
            "badge_text": "👑 #1",
            "crown": "👑"
        },
        {
            "rank": 3,
            "center_x": 785,
            "box_top": 178,
            "box_bottom": 472,
            "av_size": 94,
            "av_y": 140,
            "border_color": (235, 150, 95, 255),     # Bronze / Copper
            "ring_color": (235, 150, 95, 255),
            "platform_fill": (28, 22, 20, 215),
            "badge_text": "🥉 #3",
            "crown": "🥉"
        }
    ]

    for cfg in podium_configs:
        cx = cfg["center_x"]
        rank_num = cfg["rank"]
        entry = top_entries.get(rank_num)

        # Draw Podium Platform Card Box
        p_w = 250 if rank_num != 1 else 275
        p_x1 = cx - p_w // 2
        p_x2 = cx + p_w // 2
        p_y1 = cfg["box_top"]
        p_y2 = cfg["box_bottom"]

        draw_rounded_glass_rect(
            draw,
            (p_x1, p_y1, p_x2, p_y2),
            radius=18,
            fill=cfg["platform_fill"],
            outline=cfg["border_color"],
            width=2 if rank_num == 1 else 1
        )

        # Draw Avatar
        av_s = cfg["av_size"]
        av_y = cfg["av_y"]
        av_x = cx - av_s // 2

        av_bytes = await fetch_image(entry["avatar_url"]) if (entry and entry.get("avatar_url")) else None
        if av_bytes:
            try:
                raw_av = Image.open(io.BytesIO(av_bytes))
                circ_av = make_circle_avatar(raw_av, av_s)
                
                # Glowing Avatar Ring
                ring_pad = 4
                draw.ellipse(
                    [(av_x - ring_pad, av_y - ring_pad), (av_x + av_s + ring_pad, av_y + av_s + ring_pad)],
                    fill=cfg["border_color"]
                )
                card.paste(circ_av, (av_x, av_y), circ_av)
                draw = ImageDraw.Draw(card)
            except Exception:
                draw.ellipse([(av_x, av_y), (av_x + av_s, av_y + av_s)], fill=(40, 48, 70, 255), outline=cfg["border_color"], width=3)
        else:
            draw.ellipse([(av_x, av_y), (av_x + av_s, av_y + av_s)], fill=(32, 38, 58, 255), outline=cfg["border_color"], width=3)
            placeholder_sym = "👑" if rank_num == 1 else ("🥈" if rank_num == 2 else "🥉")
            draw.text((cx, av_y + av_s // 2), placeholder_sym, fill=(255, 255, 255, 200), font=font_subtitle, anchor="mm")

        # Rank Badge Pill
        badge_y = av_y + av_s + 15
        b_w = 98 if rank_num == 1 else 82
        draw_rounded_glass_rect(
            draw,
            (cx - b_w // 2, badge_y - 12, cx + b_w // 2, badge_y + 13),
            radius=12,
            fill=(14, 17, 28, 240),
            outline=cfg["border_color"],
            width=2 if rank_num == 1 else 1
        )
        draw.text((cx, badge_y), cfg["badge_text"], fill=cfg["border_color"], font=font_rank_tag, anchor="mm")

        # Username
        name_y = badge_y + 36
        if entry:
            disp_name = entry["name"]
            if len(disp_name) > 15:
                disp_name = disp_name[:14] + "…"
            name_color = (255, 240, 180, 255) if rank_num == 1 else (240, 245, 255, 255)
            draw.text((cx, name_y), disp_name, fill=name_color, font=font_podium_name, anchor="mm")

            # Level Badge Pill
            lvl_y = name_y + 34
            user_lvl = entry.get("level", 1)
            lvl_str = f"LVL {user_lvl}"
            lvl_pill_w = 90
            lvl_border = (255, 215, 0, 120) if rank_num == 1 else (139, 92, 246, 120)
            lvl_text_color = (255, 220, 70, 255) if rank_num == 1 else (196, 181, 253, 255)
            draw_rounded_glass_rect(
                draw,
                (cx - lvl_pill_w // 2, lvl_y - 11, cx + lvl_pill_w // 2, lvl_y + 11),
                radius=9,
                fill=(18, 22, 38, 230),
                outline=lvl_border,
                width=1
            )
            draw.text((cx, lvl_y), lvl_str, fill=lvl_text_color, font=font_podium_lvl, anchor="mm")

            # XP Pill
            xp_y = lvl_y + 34
            user_xp = entry.get("xp", entry.get("score", 0))
            xp_str = f"{user_xp:,} XP"
            xp_pill_w = min(p_w - 24, max(120, int(len(xp_str) * 9 + 36)))
            draw_rounded_glass_rect(
                draw,
                (cx - xp_pill_w // 2, xp_y - 12, cx + xp_pill_w // 2, xp_y + 13),
                radius=10,
                fill=(14, 18, 32, 240),
                outline=(255, 255, 255, 30),
                width=1
            )
            xp_color = (255, 245, 210, 255) if rank_num == 1 else (160, 220, 255, 255)
            draw.text((cx, xp_y), xp_str, fill=xp_color, font=font_podium_xp, anchor="mm")

        else:
            draw.text((cx, name_y), "— VACANT —", fill=(120, 130, 155, 200), font=font_subtitle, anchor="mm")

    # Divider between Top 3 and List (#4 - #10)
    list_start_y = 510
    draw.line([(50, list_start_y - 12), (card_w - 50, list_start_y - 12)], fill=(255, 255, 255, 25), width=1)

    # 4. Clean Vertical List for Players #4 to #10
    bottom_entries = [e for e in entries if 4 <= e["rank"] <= 10]
    row_h = 76
    row_gap = 9
    row_x1 = 50
    row_x2 = card_w - 50

    for idx, slot_rank in enumerate(range(4, 11)):
        curr_y = list_start_y + idx * (row_h + row_gap)
        if curr_y + row_h > card_h - 45:
            break

        entry = next((e for e in bottom_entries if e["rank"] == slot_rank), None)

        # Row Background Card (Subtle alternating dark glass)
        row_bg_fill = (18, 22, 38, 195) if idx % 2 == 0 else (24, 29, 48, 195)
        draw_rounded_glass_rect(
            draw,
            (row_x1, curr_y, row_x2, curr_y + row_h),
            radius=12,
            fill=row_bg_fill,
            outline=(255, 255, 255, 24),
            width=1
        )

        # Rank Number Badge (#04, #05, ...)
        rank_pill_x = row_x1 + 42
        rank_pill_y = curr_y + row_h // 2
        draw_rounded_glass_rect(
            draw,
            (rank_pill_x - 24, rank_pill_y - 15, rank_pill_x + 24, rank_pill_y + 15),
            radius=9,
            fill=(12, 15, 28, 240),
            outline=(139, 92, 246, 75),
            width=1
        )
        draw.text((rank_pill_x, rank_pill_y), f"#{slot_rank:02d}", fill=(185, 198, 225, 255), font=font_rank_tag, anchor="mm")

        # Circular Avatar
        av_d = 48
        av_x = row_x1 + 80
        av_y = curr_y + (row_h - av_d) // 2

        if entry:
            av_bytes = await fetch_image(entry.get("avatar_url", "")) if entry.get("avatar_url") else None
            if av_bytes:
                try:
                    raw_av = Image.open(io.BytesIO(av_bytes))
                    circ_av = make_circle_avatar(raw_av, av_d)
                    draw.ellipse([(av_x - 2, av_y - 2), (av_x + av_d + 2, av_y + av_d + 2)], fill=(88, 101, 242, 200))
                    card.paste(circ_av, (av_x, av_y), circ_av)
                    draw = ImageDraw.Draw(card)
                except Exception:
                    draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(40, 48, 70, 255), outline=(255, 255, 255, 40))
            else:
                draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(40, 48, 70, 255), outline=(255, 255, 255, 40))
                draw.text((av_x + av_d // 2, av_y + av_d // 2), f"{slot_rank}", fill=(200, 210, 230, 200), font=font_rank_tag, anchor="mm")

            # Username
            name_x = av_x + av_d + 16
            name_y = curr_y + row_h // 2
            raw_name = entry["name"]
            if len(raw_name) > 20:
                raw_name = raw_name[:19] + "…"
            draw.text((name_x, name_y), raw_name, fill=(245, 248, 255, 255), font=font_list_name, anchor="lm")

            # Level Pill
            lvl_pill_w = 88
            lvl_pill_x2 = row_x2 - 180
            lvl_pill_x1 = lvl_pill_x2 - lvl_pill_w
            lvl_pill_y = curr_y + row_h // 2
            user_lvl = entry.get("level", 1)
            draw_rounded_glass_rect(
                draw,
                (lvl_pill_x1, lvl_pill_y - 14, lvl_pill_x2, lvl_pill_y + 14),
                radius=9,
                fill=(24, 20, 44, 220),
                outline=(167, 139, 250, 90),
                width=1
            )
            draw.text(((lvl_pill_x1 + lvl_pill_x2) // 2, lvl_pill_y), f"LVL {user_lvl}", fill=(196, 181, 253, 255), font=font_list_lvl, anchor="mm")

            # XP Pill
            user_xp = entry.get("xp", entry.get("score", 0))
            xp_pill_w = 155
            xp_pill_x2 = row_x2 - 16
            xp_pill_x1 = xp_pill_x2 - xp_pill_w
            xp_pill_y = curr_y + row_h // 2
            draw_rounded_glass_rect(
                draw,
                (xp_pill_x1, xp_pill_y - 15, xp_pill_x2, xp_pill_y + 15),
                radius=10,
                fill=(14, 18, 32, 240),
                outline=(59, 130, 246, 85),
                width=1
            )
            draw.text(((xp_pill_x1 + xp_pill_x2) // 2, xp_pill_y), f"{user_xp:,} XP", fill=(147, 197, 253, 255), font=font_list_xp, anchor="mm")

        else:
            draw.ellipse([(av_x, av_y), (av_x + av_d, av_y + av_d)], fill=(28, 34, 50, 180), outline=(255, 255, 255, 20))
            name_x = av_x + av_d + 16
            name_y = curr_y + row_h // 2
            draw.text((name_x, name_y), "— EMPTY SLOT —", fill=(100, 110, 135, 180), font=font_subtitle, anchor="lm")

    # 5. Footer Branding (English Only)
    footer_text = "DAR SYSTEM • LEADERBOARD MATRIX • REAL-TIME SYNC"
    draw.text((card_w // 2, card_h - 25), footer_text, fill=(120, 130, 160, 190), font=font_footer, anchor="mm")

    # Output buffer
    buffer = io.BytesIO()
    card.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer

