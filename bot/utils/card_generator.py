import io
import os
import logging
from typing import Optional
from datetime import datetime
import aiohttp
import discord

logger = logging.getLogger("discord_bot.card_generator")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow is not installed. Profile Card will fall back to embed display.")

from bot.utils.arabic_text import process_bidi_text

def get_system_font(size: int, bold: bool = False, italic: bool = False) -> Optional[ImageFont.ImageFont]:
    """Safely retrieves available system TTF font with complete Unicode & Arabic support."""
    if not PIL_AVAILABLE:
        return None

    # Base font directory in project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "assets", "fonts")

    font_candidates = [
        # 1. Robust FreeSans & DejaVuSans (supports Arabic, Latin, numbers, symbols without tofu boxes)
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # 2. Bundled Noto Arabic fonts
        os.path.join(fonts_dir, "NotoSansArabic-Bold.ttf" if bold else "NotoSansArabic-Regular.ttf"),
        os.path.join(fonts_dir, "NotoNaskhArabic-Bold.ttf" if bold else "NotoNaskhArabic-Regular.ttf"),
        # 3. Bundled Cairo fonts
        os.path.join(fonts_dir, "Cairo-Bold.ttf" if bold else "Cairo-Regular.ttf"),
        # 4. System Noto Arabic & Kacst
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/kacst/KacstTitle.ttf" if bold else "/usr/share/fonts/truetype/kacst/KacstBook.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arial.ttf"
    ]
    for path in font_candidates:
        try:
            if os.path.exists(path) or not os.path.isabs(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def get_latin_font(size: int, bold: bool = False, italic: bool = False) -> Optional[ImageFont.ImageFont]:
    """Safely retrieves robust Latin/English TTF font (DejaVuSans / LiberationSans) for error-free rendering of numbers, usernames, and English text."""
    if not PIL_AVAILABLE:
        return None
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf" if italic else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else ("/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf" if italic else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else ("/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf" if italic else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arial.ttf"
    ]
    for path in font_candidates:
        try:
            if os.path.exists(path) or not os.path.isabs(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    return get_system_font(size, bold, italic)

async def fetch_image(url: str) -> Optional[bytes]:
    """Fetches image bytes from URL asynchronously."""
    if not url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        logger.debug(f"Failed to fetch image from {url}: {e}")
    return None

def make_circle_avatar(avatar_img: Image.Image, size: int) -> Image.Image:
    """Crops an image into a circle with anti-aliasing."""
    avatar_img = avatar_img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size * 4, size * 4), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size * 4, size * 4), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(avatar_img, (0, 0), mask)
    return output

async def generate_profile_card(
    member: discord.Member,
    banner_url: Optional[str],
    bio: str,
    level: int,
    rank: int,
    cur_xp: int,
    needed_xp: int,
    progress_percent: float,
    total_balance: int,
    currency_name: str,
    currency_emoji: str = "✨"
) -> Optional[io.BytesIO]:
    """
    Generates a high-definition, standalone Profile Card PNG containing:
    - Equipped Background Banner with sleek glass overlay
    - User Avatar with circular anti-aliased crop and status indicator badge
    - Display Name, Username, Join Date & ID
    - Dedicated Status & Bio panel
    - Level, Rank, Aura Balance, and XP Progress Bar
    """
    if not PIL_AVAILABLE:
        return None

    card_w, card_h = 840, 330

    # 1. Background Banner
    bg_bytes = await fetch_image(banner_url) if banner_url else None
    if bg_bytes:
        try:
            bg_image = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
            bg_image = ImageOps.fit(bg_image, (card_w, card_h), method=Image.Resampling.LANCZOS)
        except Exception:
            bg_image = Image.new("RGBA", (card_w, card_h), (20, 24, 38, 255))
    else:
        bg_image = Image.new("RGBA", (card_w, card_h), (20, 24, 38, 255))

    # 2. Add Sleek Semi-Transparent Glass Overlay (Highlighting the Banner)
    overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Outer subtle dark glass framing - allows the banner art to shine through brightly with no harsh boxes
    draw_overlay.rounded_rectangle(
        [(10, 10), (card_w - 10, card_h - 10)],
        radius=18,
        fill=(10, 12, 20, 25),
        outline=None
    )

    card = Image.alpha_composite(bg_image, overlay)
    draw = ImageDraw.Draw(card)

    # 3. Avatar & Status Processing
    avatar_size = 110
    avatar_x, avatar_y = 35, 30
    avatar_bytes = await fetch_image(member.display_avatar.url)
    if avatar_bytes:
        try:
            raw_av = Image.open(io.BytesIO(avatar_bytes))
            circle_av = make_circle_avatar(raw_av, avatar_size)
            
            # Glowing avatar border
            glow_mask = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            draw_glow = ImageDraw.Draw(glow_mask)
            draw_glow.ellipse(
                [(avatar_x - 3, avatar_y - 3), (avatar_x + avatar_size + 3, avatar_y + avatar_size + 3)],
                fill=(88, 101, 242, 255)
            )
            card = Image.alpha_composite(card, glow_mask)
            card.paste(circle_av, (avatar_x, avatar_y), circle_av)
            draw = ImageDraw.Draw(card)

            # Discord Presence Indicator (Online / Idle / DND / Offline)
            status_colors = {
                discord.Status.online: (67, 181, 129, 255),    # Green
                discord.Status.idle: (250, 166, 26, 255),      # Orange/Yellow
                discord.Status.dnd: (240, 71, 71, 255),        # Red/Crimson
                discord.Status.offline: (116, 127, 141, 255),  # Gray
                discord.Status.invisible: (116, 127, 141, 255)
            }
            member_status = getattr(member, "status", discord.Status.online)
            dot_color = status_colors.get(member_status, (67, 181, 129, 255))

            dot_x = avatar_x + avatar_size - 22
            dot_y = avatar_y + avatar_size - 22
            dot_r = 12
            # Dark border around presence dot
            draw.ellipse([(dot_x - 3, dot_y - 3), (dot_x + dot_r * 2 + 3, dot_y + dot_r * 2 + 3)], fill=(12, 15, 26, 255))
            draw.ellipse([(dot_x, dot_y), (dot_x + dot_r * 2, dot_y + dot_r * 2)], fill=dot_color)

        except Exception as e:
            logger.debug(f"Avatar draw error: {e}")

    # Fonts
    font_name = get_system_font(23, bold=True)
    font_medium = get_latin_font(16, bold=True)
    font_small = get_system_font(13, bold=False)
    font_label = get_system_font(12, bold=True)
    font_bio = get_system_font(16, bold=True)

    # 4. Member Name, Tag, and Join Date (With subtle text shadow for crisp contrast over banner)
    info_x = avatar_x + avatar_size + 25
    clean_name = member.name[:24]
    reshaped_name = process_bidi_text(clean_name)
    draw.text((info_x + 1, 29), reshaped_name, fill=(0, 0, 0, 200), font=font_name)
    draw.text((info_x, 28), reshaped_name, fill=(255, 255, 255, 255), font=font_name)

    join_str = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown"
    username_str = f"@{member.name}" if hasattr(member, "name") else ""
    info_sub = f"{username_str}  •  Joined: {join_str}  •  ID: {member.id}"
    draw.text((info_x + 1, 59), info_sub, fill=(0, 0, 0, 180), font=font_small)
    draw.text((info_x, 58), info_sub, fill=(210, 225, 245, 240), font=font_small)

    # 5. Prominent Glass Status & Bio Box (الحالة)
    bio_box_x1, bio_box_y1 = info_x, 82
    bio_box_x2, bio_box_y2 = card_w - 35, 142
    
    # Glassy background for bio (transparent, no box outline)
    bio_overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_bio_overlay = ImageDraw.Draw(bio_overlay)
    draw_bio_overlay.rounded_rectangle(
        [(bio_box_x1, bio_box_y1), (bio_box_x2, bio_box_y2)],
        radius=10,
        fill=(14, 18, 32, 35),
        outline=None
    )
    card = Image.alpha_composite(card, bio_overlay)
    draw = ImageDraw.Draw(card)
    
    # Status Tag / Header inside the box
    # Draw presence status indicator inside header
    presence_label_map = {
        discord.Status.online: ("Online", (67, 181, 129, 255)),
        discord.Status.idle: ("Idle", (250, 166, 26, 255)),
        discord.Status.dnd: ("Do Not Disturb", (240, 71, 71, 255)),
        discord.Status.offline: ("Offline", (116, 127, 141, 255)),
    }
    p_text, p_color = presence_label_map.get(member_status, ("Online", (67, 181, 129, 255)))

    # Header text
    status_header_reshaped = process_bidi_text("STATUS / الحالة")
    draw.text((bio_box_x1 + 12, bio_box_y1 + 8), status_header_reshaped, fill=(255, 215, 95, 255), font=font_label)
    
    # Small presence status tag on right side of header
    p_tag_text = f"• {p_text}"
    draw.text((bio_box_x2 - 110, bio_box_y1 + 8), p_tag_text, fill=p_color, font=font_small)

    # Bio Text
    raw_bio = (bio[:60] + "...") if len(bio) > 60 else (bio if bio and bio.strip() else "لا توجد حالة مخصصة بعد")
    display_bio = process_bidi_text(raw_bio)
    draw.text((bio_box_x1 + 13, bio_box_y1 + 29), display_bio, fill=(0, 0, 0, 180), font=font_bio)
    draw.text((bio_box_x1 + 12, bio_box_y1 + 28), display_bio, fill=(245, 250, 255, 255), font=font_bio)

    # 6. Stats Cards Row (Level & Rank, Aura Balance, XP Progress) with Glassmorphism
    stat_y1, stat_y2 = 158, 228
    
    stat_overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_stat_overlay = ImageDraw.Draw(stat_overlay)

    # Box 1: Level & Rank (transparent, no outline)
    draw_stat_overlay.rounded_rectangle([(35, stat_y1), (275, stat_y2)], radius=12, fill=(14, 18, 30, 30), outline=None)
    # Box 2: Balance (transparent, no outline)
    draw_stat_overlay.rounded_rectangle([(290, stat_y1), (535, stat_y2)], radius=12, fill=(14, 18, 30, 30), outline=None)
    # Box 3: XP Stats (transparent, no outline)
    draw_stat_overlay.rounded_rectangle([(550, stat_y1), (805, stat_y2)], radius=12, fill=(14, 18, 30, 30), outline=None)
    
    # Bottom Progress Bar Container Glass
    bar_x1, bar_y1 = 35, 248
    bar_x2, bar_y2 = 805, 274
    bar_w = bar_x2 - bar_x1
    draw_stat_overlay.rounded_rectangle([(bar_x1, bar_y1), (bar_x2, bar_y2)], radius=10, fill=(14, 18, 30, 35), outline=None)
    
    card = Image.alpha_composite(card, stat_overlay)
    draw = ImageDraw.Draw(card)

    # Text inside Stat Boxes
    # Level & Rank
    draw.text((48, stat_y1 + 10), "⭐ LEVEL", fill=(170, 190, 230, 255), font=font_small)
    draw.text((48, stat_y1 + 32), f"Level {level}", fill=(255, 215, 0, 255), font=font_medium)
    draw.text((170, stat_y1 + 10), "🏆 RANK", fill=(170, 190, 230, 255), font=font_small)
    draw.text((170, stat_y1 + 32), f"#{rank}", fill=(255, 255, 255, 255), font=font_medium)

    # Aura Balance
    draw.text((305, stat_y1 + 10), f"✨ {currency_name.upper()} BALANCE", fill=(255, 205, 90, 255), font=font_small)
    draw.text((305, stat_y1 + 32), f"{total_balance:,} Aura", fill=(255, 255, 255, 255), font=font_medium)

    # XP Progress
    draw.text((565, stat_y1 + 10), "📊 XP PROGRESS", fill=(160, 220, 255, 255), font=font_small)
    draw.text((565, stat_y1 + 32), f"{cur_xp:,} / {needed_xp:,} XP", fill=(255, 255, 255, 255), font=font_medium)

    # 7. XP Progress Bar Fill
    fill_w = max(10, int(bar_w * (progress_percent / 100.0)))
    if fill_w > 0:
        draw.rounded_rectangle(
            [(bar_x1, bar_y1), (min(bar_x2, bar_x1 + fill_w), bar_y2)],
            radius=10,
            fill=(88, 101, 242, 230)
        )

    # Progress text inside the bar
    prog_text = f"{progress_percent}%  •  {cur_xp:,} / {needed_xp:,} XP to Level {level + 1}"
    draw.text((bar_x1 + (bar_w // 2) - 80, bar_y1 + 4), prog_text, fill=(255, 255, 255, 245), font=font_small)

    # 8. Output as BytesIO
    output = io.BytesIO()
    card.convert("RGB").save(output, format="PNG", quality=95)
    output.seek(0)
    return output

