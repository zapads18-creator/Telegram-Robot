import os

# Railway'da Variables bo'limida shu nomlar bilan kiritasiz:
#   BOT_TOKEN          -> @BotFather dan olingan token
#   ADMIN_IDS           -> adminlarning Telegram ID raqamlari, vergul bilan ajratilgan
#                          masalan: 123456789,987654321
#   SUPPORT_PHONE       -> qo'llab-quvvatlash telefon raqami, masalan: +998901234567
#   SUPPORT_USERNAME    -> qo'llab-quvvatlash Telegram username, masalan: @support_user (@ siz ham bo'ladi)
#   ADMIN_CARD_NUMBER   -> komissiya to'lovlari uchun karta raqami, masalan: 8600 1234 5678 9012
#   ADMIN_CARD_OWNER    -> karta egasining F.I.Sh, masalan: BOTIR BOTIROV
#   COMMISSION_PERCENT  -> komissiya foizi (ixtiyoriy, standart 1)

BOT_TOKEN = os.getenv("BOT_TOKEN")

_raw_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _raw_admin_ids.split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN topilmadi! Railway -> Variables bo'limiga BOT_TOKEN qo'shing."
    )

if not ADMIN_IDS:
    print("OGOHLANTIRISH: ADMIN_IDS o'rnatilmagan. Adminlar bron xabarlarini olmaydi.")

SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "Kiritilmagan")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Kiritilmagan")

ADMIN_CARD_NUMBER = os.getenv("ADMIN_CARD_NUMBER", "Kiritilmagan")
ADMIN_CARD_OWNER = os.getenv("ADMIN_CARD_OWNER", "Kiritilmagan")

COMMISSION_PERCENT = float(os.getenv("COMMISSION_PERCENT", "1"))

DB_PATH = os.getenv("DB_PATH", "dacha_bot.db")
