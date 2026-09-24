# -*- coding: utf-8 -*-
"""ارسال آموزش اتصال قدم‌به‌قدم به‌تفکیک دستگاه (قابلیت ۸۴).

دستگاه‌ها و مراحل هرکدام (متن/عکس/ویدیو) توسط ادمین در پنل مدیریت تعریف
می‌شوند (database.py: tutorial_devices/tutorial_steps). این ماژول فقط
مسئول نمایش آن‌ها به کاربر است - هم به‌صورت دستی (دکمه‌ی «📚 آموزش اتصال»
روی صفحه‌ی جزئیات سرویس) و هم خودکار بلافاصله بعد از خرید موفق.
"""

import asyncio
import logging

_log = logging.getLogger("tutorial")


async def send_device_steps(bot, chat_id: int, db, device_id: int) -> bool:
    """مراحل آموزش یک دستگاه را به‌ترتیب برای کاربر می‌فرستد.
    اگر دستگاه مرحله‌ای نداشته باشد False برمی‌گرداند."""
    steps = await asyncio.to_thread(db.get_tutorial_steps, device_id)
    if not steps:
        return False
    for s in steps:
        try:
            if s["video_file_id"]:
                await bot.send_video(chat_id, s["video_file_id"], caption=s["text"] or None)
            elif s["photo_file_id"]:
                await bot.send_photo(chat_id, s["photo_file_id"], caption=s["text"] or None)
            elif s["text"]:
                await bot.send_message(chat_id, s["text"])
        except Exception:
            _log.exception("ارسال مرحله #%s آموزش دستگاه #%s ناموفق بود.", s["id"], device_id)
    return True


async def send_device_picker(bot, chat_id: int, db, intro: str = None) -> bool:
    """اگر حداقل یک دستگاه فعال ثبت شده باشد، منوی انتخاب دستگاه را می‌فرستد
    و True برمی‌گرداند؛ در غیر این صورت (هیچ دستگاهی تعریف نشده) کاری نمی‌کند
    و False برمی‌گرداند - برای فراخوانی بی‌خطر بلافاصله بعد از هر خرید."""
    import keyboards as kb
    devices = await asyncio.to_thread(db.get_tutorial_devices, True)
    if not devices:
        return False
    text = intro or "📚 برای مشاهده‌ی آموزش اتصال، دستگاه خود را انتخاب کنید:"
    try:
        await bot.send_message(chat_id, text, reply_markup=kb.tutorial_devices_user_kb(devices))
    except Exception:
        _log.exception("ارسال منوی انتخاب دستگاه برای chat_id=%s ناموفق بود.", chat_id)
        return False
    return True
