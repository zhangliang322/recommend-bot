from __future__ import annotations

from product_reco_bot.models import PushMessage


class DryRunPushService:
    def push(self, message: PushMessage) -> str:
        return (
            f"[DRY-RUN] group={message.target_group} "
            f"image={message.card_image_path} link={message.product_link}"
        )

