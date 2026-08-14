import io
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
    Generates a Profile Card PNG:
    - Banner as background
    - Member Avatar at top left
    - Member Display Name
    - Aura balance
    - Level, Rank, XP Progress bar
    - Joined Server Date
    """
    if not PIL_AVAILABLE:
        return None

    card_w, card_h = 800, 320

    # 1. Background Banner
    bg_bytes = await fetch_image(banner_url) if banner_url else None
    if bg_bytes:
        try:
            bg_image = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
            bg_image = ImageOps.fit(bg_image, (card_w, card_h), method=Image.Resampling.LANCZOS)
        except Exception:
            bg_image = Image.new("RGBA", (card_w, card_h), (25, 28, 44, 255))
    else:
        bg_image = Image.new("RGBA", (card_w, card_h), (25, 28, 44, 255))

    # 2. Add Dark Gradient / Glass Overlay on the banner for high text legibility
    overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Semi-transparent dark rounded container
    draw_overlay.rounded_rectangle(
        [(15, 15), (card_w - 15, card_h - 15)],
        radius=20,
        fill=(12, 14, 24, 195),
        outline=(114, 137, 218, 120),
        width=2
    )

    card = Image.alpha_composite(bg_image, overlay)
    draw = ImageDraw.Draw(card)

    # 3. Avatar Processing
    avatar_size = 120
    avatar_x, avatar_y = 35, 35
    avatar_bytes = await fetch_image(member.display_avatar.url)
    if avatar_bytes:
        try:
            raw_av = Image.open(io.BytesIO(avatar_bytes))
            circle_av = make_circle_avatar(raw_av, avatar_size)
            
            # Glowing avatar border
            border_size = avatar_size + 6
            glow_mask = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            draw_glow = ImageDraw.Draw(glow_mask)
            draw_glow.ellipse(
                [(avatar_x - 3, avatar_y - 3), (avatar_x + avatar_size + 3, avatar_y + avatar_size + 3)],
                fill=(88, 101, 242, 255)
            )
            card = Image.alpha_composite(card, glow_mask)
            card.paste(circle_av, (avatar_x, avatar_y), circle_av)
            draw = ImageDraw.Draw(card)
        except Exception as e:
            logger.debug(f"Avatar draw error: {e}")

    # 4. Member Name & Discriminator
    name_x = avatar_x + avatar_size + 25
    name_y = 40
    
    # We use default PIL font or scalable bitmap
    try:
        font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        font_medium = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 14)
        font_status = ImageFont.truetype("DejaVuSans-Oblique.ttf", 14)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
        font_status = font_large

    # Clean display name
    clean_name = member.display_name[:20]
    draw.text((name_x, name_y), clean_name, fill=(255, 255, 255, 255), font=font_large)

    # Join date badge
    join_str = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown"
    draw.text((name_x, name_y + 32), f"Joined: {join_str} • ID: {member.id}", fill=(180, 190, 210, 230), font=font_small)

    # Bio / Status
    clean_bio = f'"{bio[:50]}..."' if len(bio) > 50 else f'"{bio}"'
    draw.text((name_x, name_y + 54), clean_bio, fill=(200, 215, 240, 200), font=font_status)

    # 5. Stats Cards (Level, Rank, Aura Balance)
    # Box 1: Level & Rank
    draw.rounded_rectangle([(35, 175), (265, 245)], radius=12, fill=(20, 24, 40, 220), outline=(88, 101, 242, 100), width=1)
    draw.text((48, 185), "LEVEL", fill=(140, 160, 200, 255), font=font_small)
    draw.text((48, 205), f"Level {level}", fill=(255, 215, 0, 255), font=font_medium)
    draw.text((170, 185), "RANK", fill=(140, 160, 200, 255), font=font_small)
    draw.text((170, 205), f"#{rank}", fill=(255, 255, 255, 255), font=font_medium)

    # Box 2: Total Aura Balance
    draw.rounded_rectangle([(280, 175), (510, 245)], radius=12, fill=(20, 24, 40, 220), outline=(255, 180, 0, 100), width=1)
    draw.text((295, 185), f"{currency_name.upper()} BALANCE", fill=(255, 200, 80, 255), font=font_small)
    draw.text((295, 205), f"{total_balance:,} Aura", fill=(255, 255, 255, 255), font=font_medium)

    # Box 3: XP Stats
    draw.rounded_rectangle([(525, 175), (765, 245)], radius=12, fill=(20, 24, 40, 220), outline=(100, 200, 255, 100), width=1)
    draw.text((540, 185), "XP PROGRESS", fill=(140, 200, 255, 255), font=font_small)
    draw.text((540, 205), f"{cur_xp:,} / {needed_xp:,} XP", fill=(255, 255, 255, 255), font=font_medium)

    # 6. XP Progress Bar at the bottom
    bar_x1, bar_y1 = 35, 265
    bar_x2, bar_y2 = 765, 285
    bar_w = bar_x2 - bar_x1
    
    # Background bar
    draw.rounded_rectangle([(bar_x1, bar_y1), (bar_x2, bar_y2)], radius=10, fill=(35, 40, 60, 255))
    
    # Fill bar
    fill_w = max(10, int(bar_w * (progress_percent / 100.0)))
    if fill_w > 0:
        draw.rounded_rectangle(
            [(bar_x1, bar_y1), (min(bar_x2, bar_x1 + fill_w), bar_y2)],
            radius=10,
            fill=(88, 101, 242, 255)
        )

    # Progress text centered on bar
    prog_text = f"{progress_percent}% to Level {level + 1}"
    draw.text((bar_x1 + (bar_w // 2) - 50, bar_y1 + 2), prog_text, fill=(255, 255, 255, 230), font=font_small)

    # Convert to BytesIO
    output = io.BytesIO()
    card.convert("RGB").save(output, format="PNG", quality=95)
    output.seek(0)
    return output
