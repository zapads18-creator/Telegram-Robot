# 🏡 Dacha Bron Bot

O'zbekiston aholisi uchun dachalarni ko'rish va bron qilish imkonini beruvchi Telegram bot.

## Imkoniyatlari

- Foydalanuvchilar mavjud dachalar ro'yxatini ko'radi
- Har bir dacha uchun batafsil ma'lumot (narx, manzil, tavsif, aloqa)
- Sanalarni tanlab bron so'rovi yuborish
- Admin yangi dacha qo'shishi va barcha bronlarni ko'rishi mumkin
- Yangi bron kelganda admin darhol xabar oladi

## O'rnatish

### 1. Bot yaratish
Telegram'da [@BotFather](https://t.me/BotFather) ga o'ting:
- `/newbot` buyrug'ini yuboring
- Bot nomini va username kiriting
- Sizga beriladigan **tokenni** saqlab qo'ying

### 2. O'z Telegram ID'ingizni bilib oling
[@userinfobot](https://t.me/userinfobot) ga `/start` yozing — u sizga ID raqamingizni beradi.

### 3. Kodni sozlash
`bot.py` faylida quyidagi qatorlarni o'zgartiring:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # BotFather'dan olgan tokeningiz
ADMIN_ID = 123456789                 # Sizning Telegram ID'ingiz
```

### 4. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 5. Botni ishga tushirish

```bash
python bot.py
```

## Foydalanish

**Oddiy foydalanuvchi uchun:**
- `/start` — botni boshlash
- `/dachalar` — mavjud dachalarni ko'rish → "Batafsil" → "Bron qilish"

**Admin uchun (faqat ADMIN_ID egasi):**
- `/dacha_qoshish` — yangi dacha qo'shish (bot savol-javob tarzida ma'lumot so'raydi)
- `/bronlar` — so'nggi 20 ta bron so'rovini ko'rish

## Keyingi qadamlar (bot rivojlantirilganda qo'shsa bo'ladigan narsalar)

- 📸 Dacha rasmlarini yuklash imkoniyati
- 🔍 Hudud/narx bo'yicha filtr va qidiruv
- 💳 Onlayn to'lov integratsiyasi (Click, Payme)
- ⭐️ Baholash va sharh tizimi
- 📅 Kalendar orqali band/bo'sh kunlarni ko'rsatish
- 🌐 Web-app versiyasi (Telegram Mini App)

## Serverga joylashtirish (hosting)

Botni doim ishlab turishi uchun uni serverga joylashtirish kerak. Tavsiya etiladi:
- **Railway.app** — oson va tez (siz allaqachon undan foydalanyapsiz)
- **PythonAnywhere**
- Oddiy VPS (masalan DigitalOcean, Timeweb) + `systemd` yoki `screen`/`tmux` orqali doimiy ishga tushirish

⚠️ **Muhim eslatma:** `BOT_TOKEN`ni hech qachon ochiq joyda (GitHub'ning ochiq reposida) qoldirmang — buni environment variable sifatida saqlash tavsiya etiladi.
