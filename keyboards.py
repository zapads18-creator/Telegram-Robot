from aiogram.utils.keyboard import InlineKeyboardBuilder

from regions import REGIONS
from config import COMMISSION_PERCENT


def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏡 Dachalar ro'yxati", callback_data="list_dachas")
    kb.button(text="📋 Mening bronlarim", callback_data="my_bookings")
    kb.button(text="🏘 Dachamni joylashtirish", callback_data="owner_start")
    kb.button(text="🆘 Qo'llab-quvvatlash", callback_data="support")
    kb.button(text="ℹ️ Yordam", callback_data="help")
    kb.adjust(1)
    return kb.as_markup()


def regions_kb(callback_prefix="region_"):
    kb = InlineKeyboardBuilder()
    for region in REGIONS.keys():
        kb.button(text=region, callback_data=f"{callback_prefix}{region}")
    kb.button(text="⬅️ Orqaga", callback_data="back_to_menu")
    kb.adjust(1)
    return kb.as_markup()


def districts_kb(region, callback_prefix="district_", back_callback="list_dachas"):
    kb = InlineKeyboardBuilder()
    for district in REGIONS.get(region, []):
        kb.button(text=district, callback_data=f"{callback_prefix}{district}")
    kb.button(text="⬅️ Orqaga", callback_data=back_callback)
    kb.adjust(2)
    return kb.as_markup()


def dachas_list_kb(dachas):
    kb = InlineKeyboardBuilder()
    for d in dachas:
        kb.button(text=f"{d['name']} — {d['price_per_night']:,} so'm/kecha", callback_data=f"dacha_{d['id']}")
    kb.button(text="⬅️ Orqaga", callback_data="list_dachas")
    kb.adjust(1)
    return kb.as_markup()


def dacha_detail_kb(dacha_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Bron qilish", callback_data=f"book_{dacha_id}")
    kb.button(text="⬅️ Ro'yxatga qaytish", callback_data="list_dachas")
    kb.adjust(1)
    return kb.as_markup()


def confirm_booking_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data="confirm_booking")
    kb.button(text="❌ Bekor qilish", callback_data="cancel_booking")
    kb.adjust(2)
    return kb.as_markup()


def admin_decision_kb(booking_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"approve_{booking_id}")
    kb.button(text="❌ Rad etish", callback_data=f"reject_{booking_id}")
    kb.adjust(2)
    return kb.as_markup()


def cancel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Bekor qilish", callback_data="cancel_flow")
    kb.adjust(1)
    return kb.as_markup()


def skip_photo_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ Rasmsiz qoldirish", callback_data="skip_photo")
    kb.adjust(1)
    return kb.as_markup()


def contract_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Roziman", callback_data="owner_agree")
    kb.button(text="❌ Rozi emasman", callback_data="owner_disagree")
    kb.adjust(2)
    return kb.as_markup()


def owner_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi dacha qo'shish", callback_data="owner_add_dacha")
    kb.button(text="🏠 Mening dachalarim", callback_data="owner_my_dachas")
    kb.button(text="💳 To'lanmagan komissiyalar", callback_data="owner_commissions")
    kb.button(text="⬅️ Bosh menyu", callback_data="back_to_menu")
    kb.adjust(1)
    return kb.as_markup()


def commission_paid_kb(booking_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ To'ladim", callback_data=f"owner_paid_{booking_id}")
    kb.adjust(1)
    return kb.as_markup()


def admin_commission_confirm_kb(booking_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tushumni tasdiqlash", callback_data=f"confirm_commission_{booking_id}")
    kb.adjust(1)
    return kb.as_markup()
