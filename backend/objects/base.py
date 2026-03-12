"""
Base object handler.

Replaces PL/I Class_Table dispatch:
    Class_Table(I).actions->a(request) = handler_function;
    call Class_Table(obj.class).actions->a(current_request);

In Python, each class has a handler with handle_ACTION methods.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..region_processor import RegionProcessor

# PL/I: declare 1 Class_Table(0:255) external;
OBJECT_REGISTRY: dict[int, "BaseObject"] = {}


class BaseObject:
    """Base handler for all Habitat objects.
    Replaces the common action dispatch pattern in PL/I."""

    class_name: str = "object"
    capacity: int = 0
    opaque_container: bool = False

    async def dispatch(self, action: str, region: "RegionProcessor",
                       noid: int, args: dict) -> dict:
        """Dispatch action to handler method.
        PL/I: call Class_Table(obj.class).actions->a(current_request);"""
        method_name = f"handle_{action}"
        method = getattr(self, method_name, None)
        if method:
            return await method(region, noid, args)
        return await self.handle_default(region, noid, action, args)

    async def handle_default(self, region: "RegionProcessor",
                             noid: int, action: str, args: dict) -> dict:
        return {"success": False, "error": f"illegal action: {action}"}

    async def handle_HELP(self, region: "RegionProcessor",
                          noid: int, args: dict) -> dict:
        """PL/I: generic_IDENTIFY — all objects support HELP."""
        obj = region.get_object(noid)
        if not obj:
            return {"success": False}
        return {
            "success": True,
            "type": "identify",
            "class_name": self.class_name,
            "noid": noid,
            "class_id": obj.class_id,
        }
