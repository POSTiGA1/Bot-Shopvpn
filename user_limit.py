# -*- coding: utf-8 -*-
"""محدودیت تعداد کاربر همزمان (limitIp) برای محصولات متصل به پنل: قیمت پایه شامل ۱ کاربر است."""

from panel_providers import PROVIDERS


def _field(row, key, default=0):
    if row is None:
        return default
    return row[key] if key in row.keys() and row[key] is not None else default


def configured_max_users(product) -> int:
    extra = int(_field(product, "extra_user_price"))
    max_users = int(_field(product, "max_users"))
    if not _field(product, "is_auto_provision") or extra <= 0 or max_users < 2:
        return 0
    return max_users


def server_supports(server) -> bool:
    if not server:
        return False
    provider_cls = PROVIDERS.get(server["panel_type"])
    return bool(provider_cls and getattr(provider_cls, "supports_user_limit", False))


def resolve_server(db, product):
    server_id = _field(product, "provision_server_id", None)
    if server_id:
        return db.get_panel_server(server_id)
    try:
        from config import DB_PATH as MAIN_DB_PATH
        from database import Database

        owner_id = db.get_owner_telegram_id()
        if not owner_id:
            return None
        return Database(MAIN_DB_PATH).get_reseller_panel(owner_id)
    except Exception:
        return None


def selectable_max_users(db, product) -> int:
    max_users = configured_max_users(product)
    if not max_users:
        return 0
    server = resolve_server(db, product)
    if not server or not _field(server, "is_active", 1) or not server_supports(server):
        return 0
    return max_users


def price_for_users(product, users: int) -> int:
    price = int(product["price"])
    if users and users > 1:
        price += int(_field(product, "extra_user_price")) * (users - 1)
    return price


def order_user_limit(order) -> int:
    value = _field(order, "user_limit", None)
    return int(value) if value else 0


def provider_kwargs(provider, user_limit) -> dict:
    if user_limit and getattr(provider, "supports_user_limit", False):
        return {"user_limit": int(user_limit)}
    return {}


def upgrade_price(product, current: int, users: int) -> int:
    return int(_field(product, "extra_user_price")) * max(users - current, 0)


def service_upgrade_info(db, cc):
    current = int(_field(cc, "user_limit", 0))
    if current < 1 or _field(cc, "source", "") == "test" or not _field(cc, "enabled", 1):
        return None
    order_id = _field(cc, "order_id", None)
    order = db.get_order(order_id) if order_id else None
    product = db.get_product(order["product_id"]) if order and order["product_id"] else None
    max_users = configured_max_users(product) if product else 0
    server = db.get_panel_server(cc["panel_server_id"])
    if not max_users or current >= max_users:
        return None
    if not server or not _field(server, "is_active", 1) or not server_supports(server):
        return None
    return {"product": product, "current": current, "max_users": max_users}
