from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

from product_reco_bot.models import Recommendation


class CardRenderService:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.font_regular = self._load_font(34)
        self.font_small = self._load_font(25)
        self.font_title = self._load_font(46)

    def render(self, recommendation: Recommendation) -> Path:
        product = recommendation.product
        card = Image.new("RGB", (1080, 1440), "#f7f3ec")
        draw = ImageDraw.Draw(card)
        self._draw_header(draw, recommendation)
        image = self._load_product_image(product.image_url, product.product_name)
        card.paste(image, (90, 160))
        self._draw_body(draw, recommendation)
        path = self.output_dir / f"{product.product_id}-{self._slug(product.product_name)}.png"
        card.save(path, "PNG")
        recommendation.card_image_path = path
        return path

    def _draw_header(self, draw: ImageDraw.ImageDraw, recommendation: Recommendation) -> None:
        score = recommendation.score
        product = recommendation.product
        draw.rounded_rectangle((60, 48, 1020, 126), radius=28, fill="#1f2933")
        header = (
            f"{product.category} | 火热指数 {score.hot_score:.0f} | {score.hot_label}"
        )
        draw.text((90, 70), header, fill="white", font=self.font_regular)

    def _draw_body(self, draw: ImageDraw.ImageDraw, recommendation: Recommendation) -> None:
        product = recommendation.product
        y = 820
        draw.text((80, y), product.product_name, fill="#172026", font=self.font_title)
        y += 68
        for line in self._wrap(recommendation.one_line_selling_point, 25)[:2]:
            draw.text((84, y), line, fill="#39434d", font=self.font_regular)
            y += 46
        y += 10
        draw.text((84, y), "推荐理由", fill="#172026", font=self.font_regular)
        y += 48
        for reason in recommendation.reasons[:3]:
            for line in self._wrap(f"- {reason}", 31)[:2]:
                draw.text((88, y), line, fill="#39434d", font=self.font_small)
                y += 36
        y = 1270
        trend_source = product.fashion_source or product.social_platform
        source = f"来源：{product.source_platform} / {trend_source}"
        draw.text((84, y), self._truncate(source, 32), fill="#5c6670", font=self.font_small)
        y += 42
        risk = f"提示：{product.risk_note or '推送前确认价格、库存和链接'}"
        draw.text((84, y), self._truncate(risk, 36), fill="#8a4b2a", font=self.font_small)

    def _load_product_image(self, image_url: str, product_name: str = "PRODUCT") -> Image.Image:
        if image_url.startswith("placeholder://"):
            return self._placeholder_product_image(product_name)
        path = Path(image_url)
        if path.exists():
            image = Image.open(path).convert("RGB")
            return self._cover(image, (900, 620))
        try:
            with urlopen(image_url, timeout=8) as response:
                image = Image.open(response).convert("RGB")
        except Exception:
            return self._placeholder_product_image(product_name)
        image = self._cover(image, (900, 620))
        image = image.copy()
        return image

    def _placeholder_product_image(self, product_name: str) -> Image.Image:
        image = Image.new("RGB", (900, 620), "#efe7da")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (70, 70, 830, 550),
            radius=40,
            fill="#ffffff",
            outline="#d2c7b8",
            width=4,
        )
        draw.ellipse((350, 135, 550, 335), fill="#d9b98f", outline="#b88a55", width=5)
        draw.rounded_rectangle((300, 360, 600, 430), radius=24, fill="#1f2933")
        draw.text((348, 377), "PRODUCT", fill="white", font=self.font_small)
        y = 460
        for line in self._wrap(product_name, 18)[:2]:
            bbox = draw.textbbox((0, 0), line, font=self.font_regular)
            x = (900 - (bbox[2] - bbox[0])) / 2
            draw.text((x, y), line, fill="#172026", font=self.font_regular)
            y += 46
        return image

    @staticmethod
    def _cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
        target_w, target_h = size
        ratio = max(target_w / image.width, target_h / image.height)
        resized = image.resize((int(image.width * ratio), int(image.height * ratio)))
        left = (resized.width - target_w) // 2
        top = (resized.height - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
        for path in candidates:
            if path.exists():
                return ImageFont.truetype(str(path), size)
        return ImageFont.load_default()

    @staticmethod
    def _wrap(text: str, limit: int) -> list[str]:
        lines: list[str] = []
        current = ""
        width = 0
        for char in text:
            char_width = 2 if ord(char) > 127 else 1
            if width + char_width > limit:
                lines.append(current)
                current = char
                width = char_width
            else:
                current += char
                width += char_width
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        lines = CardRenderService._wrap(text, limit)
        return lines[0] + ("..." if len(lines) > 1 else "")

    @staticmethod
    def _slug(text: str) -> str:
        return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
