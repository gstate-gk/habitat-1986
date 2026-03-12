"""ATM (bank). From class_atm.pl1
PL/I: atm_DEPOSIT, atm_WITHDRAW"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor


class ATMHandler(BaseObject):
    class_name = "atm"

    async def handle_DO(self, region: "RegionProcessor",
                        noid: int, args: dict) -> dict:
        """ATM interaction — deposit or withdraw."""
        action_type = args.get("atm_action", "balance")
        avatar_noid = args.get("avatar_noid")
        avatar = region.get_avatar(avatar_noid)
        if not avatar:
            return {"success": False}

        if action_type == "deposit":
            amount = args.get("amount", 0)
            if amount <= 0 or avatar.tokens_in_hand < amount:
                return {"success": False, "error": "insufficient tokens"}
            avatar.tokens_in_hand -= amount
            avatar.bank_account += amount
            return {
                "success": True,
                "type": "ATM_RESULT",
                "action": "deposit",
                "amount": amount,
                "balance": avatar.bank_account,
                "tokens": avatar.tokens_in_hand,
            }

        elif action_type == "withdraw":
            amount = args.get("amount", 0)
            if amount <= 0 or avatar.bank_account < amount:
                return {"success": False, "error": "insufficient funds"}
            avatar.bank_account -= amount
            avatar.tokens_in_hand += amount
            return {
                "success": True,
                "type": "ATM_RESULT",
                "action": "withdraw",
                "amount": amount,
                "balance": avatar.bank_account,
                "tokens": avatar.tokens_in_hand,
            }

        else:  # balance
            return {
                "success": True,
                "type": "ATM_RESULT",
                "action": "balance",
                "balance": avatar.bank_account,
                "tokens": avatar.tokens_in_hand,
            }
