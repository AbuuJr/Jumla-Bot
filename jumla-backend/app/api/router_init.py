"""
app/api/router.py

Central router registration for all API sub-routers.
This file keeps main.py tidy: import and call include_api_routers(app).
Each sub-router is registered with a consistent prefix and tags.

Notes:
- Add additional v1 modules to the `v1_routers` list. Keep definitions idempotent.
- Prefer to expose only `include_api_routers` to main.
"""
from typing import Iterable

from fastapi import FastAPI

from app.config import settings

# Import v1 routers 
from app.api.v1 import (
    auth,
    leads,
    conversations,
    offers,
    buyers,
    enrichment,
    webhooks,
    admin,
)

# Mapping list of (router, subpath, tags) to register in order.
_v1_routers = [
    (auth.router, "auth", ["Authentication"]),
    (leads.router, "leads", ["Leads"]),
    (conversations.router, "conversations", ["Conversations"]),
    (offers.router, "offers", ["Offers"]),
    (buyers.router, "buyers", ["Buyers"]),
    (enrichment.router_enrichment, "enrichment", ["Enrichment"]),
    (webhooks.router, "webhooks", ["Webhooks"]),
    (admin.router_admin, "admin", ["Admin"]),
]


def include_api_routers(app: FastAPI) -> None:
    """
    Include all API routers under the configured API_V1_PREFIX.
    Call this once from app/main.py during app creation.
    """
    prefix = settings.API_V1_PREFIX.rstrip("/")  # e.g., "/api/v1"
    for router_obj, subpath, tags in _v1_routers:
        full_prefix = f"{prefix}/{subpath}"
        # Ensure router exists and is a proper APIRouter
        app.include_router(router_obj, prefix=full_prefix, tags=tags)
