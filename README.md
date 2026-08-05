# Dachalarni bronlash boti

## Railway'da sozlash

1. Loyihani GitHub repo'ga yuklang, Railway'da shu repo'ni ulang.
2. Railway loyihasida **Variables** bo'limiga o'ting va quyidagilarni qo'shing:

   | O'zgaruvchi | Tavsif | Namuna |
   |---|---|---|
   | `BOT_TOKEN` | @BotFather'dan olingan token | `123456:AAH...` |
   | `ADMIN_IDS` | Adminlar ID'lari, vergul bilan | `123456789,987654321` |
   | `SUPPORT_PHONE` | Qo'llab-quvvatlash telefon raqami | `+998901234567` |
   | `SUPPORT_USERNAME` | Qo'llab-quvvatlash Telegram username | `@support_user` |
   | `ADMIN_CARD_NUMBER` | Komissiya to'lovlari uchun karta raqami | `8600 1234 5678 9012` |
   | `ADMIN_CARD_OWNER` | Karta egasining F.I.Sh | `BOTIR BOTIROV` |
   | `COMMISSION_PERCENT` | Komissiya foizi (ixtiyoriy, standart 1) | `1` |

3. Railway avtomatik `Procfile`ni o'qib, `python bot.py` buyrug'ini ishga tushiradi.
4. Deploy tugagach, botga `/start` yozib tekshiring.

## Foydalanuvchi (mehmon) funksiyalari

- `/start` — bosh menyu
- **Dachalar ro'yxati** — viloyat → tuman tanlab, o'sha hududdagi dachalarni ko'rish
- Dacha tafsilotlari — rasm, tavsif, manzil, narx, egasining aloqa raqami
- **Bron qilish** — sana va telefon raqami so'raladi, umumiy narx avtomatik hisoblanadi
- **Mening bronlarim** — bron holatini kuzatish (kutilmoqda / tasdiqlangan / rad etilgan)
- **Qo'llab-quvvatlash** — admin telefon raqami va Telegram username'i

## Dacha egasi funksiyalari (adminsiz, o'zi joylashtiradi)

- **🏘 Dachamni joylashtirish** tugmasi orqali:
  1. Birinchi marta shartnoma matni ko'rsatiladi — har bir bron uchun umumiy summadan
     **1% komissiya** botga to'lash shartiga rozilik so'raladi (✅/❌)
  2. Rozi bo'lsa — ism-familiya va telefon raqami so'raladi, ro'yxatdan o'tadi
  3. Keyin istalgan vaqt "➕ Yangi dacha qo'shish" orqali: nomi, tavsifi, **viloyat → tuman**,
     aniq manzil, narx, aloqa raqami, rasm kiritiladi
- **🏠 Mening dachalarim** — o'zi joylashtirgan dachalar ro'yxati
- **💳 To'lanmagan komissiyalar** — tasdiqlangan bronlar bo'yicha to'lanishi kerak bo'lgan
  komissiya summasi va admin kartasi ko'rsatiladi; "✅ To'ladim" tugmasi bosilgach,
  admin tushumni tasdiqlagach yopiladi

## Admin funksiyalari

- `/admin` — admin panel haqida qisqacha ma'lumot
- `/add_dacha` — admin nomidan dacha qo'shish (bunday dachalar uchun komissiya hisoblanmaydi)
- `/pending` — hali tasdiqlanmagan bronlar ro'yxati
- `/dachas` — barcha faol dachalar ro'yxati
- Har bir yangi bron so'rovi barcha adminlarga avtomatik yuboriladi, ✅/❌ tugmalari bilan
- Bron **tasdiqlanganda**, agar dacha egasi bo'lsa — egaga komissiya summasi va to'lov
  ma'lumotlari (karta raqami) avtomatik yuboriladi
- Ega "To'ladim" tugmasini bosgach, admin "✅ Tushumni tasdiqlash" orqali tasdiqlaydi

## Ma'lumotlar bazasi

SQLite (`dacha_bot.db`) fayli avtomatik yaratiladi:
- `owners` — dacha egalari va ularning shartnomaga roziligi
- `dachas` — viloyat/tuman, narx, egasi, aloqa ma'lumotlari
- `bookings` — bron sanalari, umumiy narx, komissiya summasi va holati

Eslatma: Railway'da fayl tizimi har deploy'da tozalanishi mumkin — doimiy saqlash uchun
Railway'ning "Volume" funksiyasidan foydalaning yoki keyinchalik PostgreSQL'ga o'ting.

## Muhim eslatma to'lov tizimi haqida

Hozirgi versiyada komissiya to'lovi **qo'lda tasdiqlash** orqali ishlaydi: ega pul o'tkazadi,
"To'ladim" tugmasini bosadi, admin tushumni tekshirib tasdiqlaydi. Bu haqiqiy to'lov
shlyuzi (Click, Payme kabi) emas — ularni ulash uchun tegishli xizmatning merchant
hisobi va API kalitlari kerak bo'ladi, buni alohida so'rasangiz qo'shib beraman.
