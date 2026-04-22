# Telegram Kino Bot

Kino, multfilm va serial qidiruv boti. Foydalanuvchilar kinolarni raqam orqali topib, yopiq kanaldan olishlari mumkin.

## Xususiyatlar

- **Kino qidirish**: Foydalanuvchilar kinolarni raqam orqali qidirishadi
- **Yopiq kanal**: Barcha kinolar yopiq kanalda saqlanadi
- **Admin panel**: Statistika, broadcast, media boshqaruvi
- **Majburiy obuna**: Foydalanuvchilar kanallarga obuna bo'lishi shart

## Talablar

- Python 3.8+
- Telegram Bot Token (@BotFather dan oling)

## O'rnatish

1. Repo-ni kloning:
```bash
cd Telegram-Bot
```

2. Virtual environment yaratish:
```bash
python -m venv venv
venv\Scripts\activate  # Windows uchun
source venv/bin/activate  # Linux/Mac uchun
```

3. Dependensiyalarni o'rnatish:
```bash
pip install -r requirements.txt
```

4. `.env` faylini yaratish:
```bash
copy .env.example .env  # Windows
cp .env.example .env  # Linux/Mac
```

5. `.env` faylni to'ldiring:
```
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_IDS=123456789,987654321
CLOSED_CHANNEL_USERNAME=@sizning_yopiq_kanalingiz
MANDATORY_CHANNELS=@kanal1,@kanal2
DATABASE_PATH=bot_database.db
```

## Bot Token olish

1. [@BotFather](https://t.me/BotFather) ga murojaat qiling
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username kirit
4. Tokenni nusxalab `.env` fayliga joylashtiring

## Admin ID olish

1. [@userinfobot](https://t.me/userinfobot) ga murojaat qiling
2. O'z IDingizni `.env` fayliga joylashtiring

## Botni ishga tushurish

```bash
python bot.py
```

## Botdan foydalanish

### Foydalanuvchi uchun

1. `/start` - Botni boshlash
2. Kinoning raqamini yuboring (masalan: `1`)
3. Bot sizga kinoni yopiq kanaldan beradi

### Admin uchun

1. `/admin` - Admin panelni ochish
2. Admin panel orqali:
   - 📊 Statistikani ko'rish
   - 📢 Broadcast yuborish
   - 📺 Media qo'shish
   - 🗑️ Media o'chirish
   - 👥 Foydalanuvchilar ro'yxati
   - 🔗 Majburiy kanallar boshqaruvi

### Media qo'shish

```
/add <raqam> <nom> <turi> <janrlar> <channel_message_id>
```

Misol:
```
/add 1 Avatar Film Action,Sci-Fi 123
```

### Media o'chirish

```
/delete <raqam>
```

Misol:
```
/delete 1
```

### Majburiy kanal qo'shish

```
/addchannel @channelname
```

Misol:
```
/addchannel @mychannel
```

### Majburiy kanal o'chirish

```
/removechannel @channelname
```

Misol:
```
/removechannel @mychannel
```

## Yopiq kanalni sozlash

1. Telegramda yangi kanal yarating
2. Kanalni yopiq qiling (faqat a'zolar ko'ra oladi)
3. Kinolarni kanalga yuklang
4. Har bir kinoning message_id sini oling
5. Bot orqali media qo'shing

## Message ID olish

1. Kinoni kanalga yuklang
2. Xabarga o'ng tugma bosib "Copy Link" ni bosing
3. Linkdan message ID ni oling: `https://t.me/channelname/123` - 123 bu message_id

## Majburiy obuna kanallari

Majburiy kanallarni bot orqali boshqarish mumkin:

1. `/admin` buyrug'ini yuboring
2. "🔗 Majburiy Kanallar" tugmasini bosing
3. Kanal qo'shish uchun: `/addchannel @channelname`
4. Kanal o'chirish uchun: `/removechannel @channelname`

Foydalanuvchilar bu kanallarga obuna bo'lmaguncha botdan foydalana olmaydi.

## Database

Bot SQLite database ishlatadi. Quyidagi jadvallar mavjud:

- `media` - Kinolar ma'lumotlari
- `users` - Foydalanuvchilar ma'lumotlari
- `search_history` - Qidiruv tarixi
- `mandatory_channels` - Majburiy kanallar ro'yxati

## Muammolar va yechimlar

**Bot ishlamayapti:**
- `.env` fayl to'g'ri sozlanganligini tekshiring
- Bot token to'g'ri ekanligini tekshiring
- Python versiyasi 3.8+ ekanligini tekshiring

**Kinoni topmayapti:**
- Raqam to'g'ri ekanligini tekshiring
- Media database ga qo'shilganligini tekshiring
- Yopiq kanal username to'g'ri ekanligini tekshiring

**Broadcast ishlamayapti:**
- Admin ID to'g'ri ekanligini tekshiring
- Foydalanuvchilar botni block qilmaganligini tekshiring

## Qo'shimcha ma'lumotlar

- Bot python-telegram-bot kutubxonasidan foydalanadi
- Database aiosqlite kutubxonasidan foydalanadi
- Bot asinxron ishlaydi

## Yordam

Muammolar bo'lsa, admin bilan bog'laning yoki GitHub issues yarating.
