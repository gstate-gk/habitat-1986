"""Mailbox. From class_mailbox.pl1"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class MailboxHandler(BaseObject):
    class_name = "mailbox"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """Check mailbox for messages."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        messages = obj.extra.get("messages", [])
        return {
            "success": True,
            "type": "MAIL_CHECK",
            "noid": noid,
            "count": len(messages),
            "messages": messages[-5:],  # last 5
        }

    async def handle_PUT(self, region: "RegionProcessor",
                         noid: int, args: dict) -> dict:
        """Send mail — put paper into mailbox."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        text = args.get("text", "")
        sender = args.get("sender", "Anonymous")
        recipient = args.get("recipient", "")
        if not obj.extra.get("messages"):
            obj.extra["messages"] = []
        obj.extra["messages"].append({
            "from": sender, "to": recipient, "text": text,
        })
        return {"success": True, "type": "MAIL_SENT"}

    async def handle_GRAB(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """Retrieve mail."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        messages = obj.extra.get("messages", [])
        if not messages:
            return {"success": False, "error": "no mail"}
        msg = messages.pop(0)
        return {"success": True, "type": "MAIL_RECEIVED", "message": msg}
