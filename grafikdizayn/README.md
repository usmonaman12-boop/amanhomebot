# Maktab bal tizimi (Django)

Admin → o'qituvchi qo'shadi → o'qituvchi guruh va o'quvchi qo'shadi → har kuni
davomat va uy vazifasi belgilanadi, ballar avtomatik hisoblanadi, Telegram
guruhiga natijalar yuboriladi.

## Ball tizimi
- Davomat: **Bor** = +3 ball (avtomatik), **Yo'q** = +0
- Uy vazifasi: **Bor** = +5, **Chala** = +3, **Yo'q** = +0 (va "vazifa qilinmadi" sanaladi)
- Qo'shimcha ball: o'qituvchi qo'lda kiritadi
- "✅ Tayyor" tugmasi bosilganda kunlik ballar saqlanadi, umumiy balga qo'shiladi
  va bog'langan bo'lsa Telegram guruhiga yuboriladi

## Lokal ishga tushirish

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # va qiymatlarni to'ldiring
python manage.py migrate
python manage.py create_admin --username admin --password parolingiz123
python manage.py runserver
```

`create_admin` — Admin panelga kiradigan foydalanuvchi yaratadi
(`/login/` sahifasidan shu login-parol bilan kiring, keyin `/admin-panel/`).

Django'ning o'zining `/django-admin/` paneli ham mavjud — barcha
ma'lumotlarni (guruh, o'quvchi, kunlik yozuvlar) shu yerdan ham boshqarish mumkin.

## Rollar va yo'nalishlar

| Rol | Login qilgach | Nima qiladi |
|---|---|---|
| Admin | `/admin-panel/` | O'qituvchilar qo'shadi/o'chiradi |
| O'qituvchi | `/teacher/` | Guruh yaratadi, guruhga o'quvchi qo'shadi, kunlik baholash sahifasidan davomat/uy vazifasi/qo'shimcha ball qo'yadi |
| O'quvchi | `/student/` | Umumiy ballini va kunlik tarixini ko'radi |

## Telegram bot sozlash

1. [@BotFather](https://t.me/BotFather) orqali bot yarating, tokenni `TELEGRAM_BOT_TOKEN` ga qo'ying.
2. Webhookni o'rnating (server ishga tushgandan keyin, bitta marta):

   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<domeningiz>/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>/"
   ```

3. Botni kerakli Telegram guruhiga qo'shing.
4. O'qituvchi panelida guruh ichida **"Telegramga ulash"** tugmasini bosing —
   u yerda `/link KOD` buyrug'i ko'rsatiladi. Shu buyruqni Telegram guruhida
   yuboring — bot javob berib, o'sha guruhni bog'laydi.
5. Shundan keyin har safar "✅ Tayyor" bosilganda, o'sha kunning barcha
   o'quvchilar balli (ism familiya, bugungi ball, nimaga qo'shilgani, umumiy
   ball) Telegram guruhiga avtomatik yuboriladi.

## Railway'ga deploy qilish

1. Ushbu papkani (yoki zip ichidagi fayllarni) GitHub repo qilib yuklang,
   yoki Railway CLI orqali to'g'ridan-to'g'ri deploy qiling.
2. Railway'da yangi loyiha yarating, repo/papkani ulang.
3. **Plugin sifatida Postgres qo'shing** — Railway avtomatik `DATABASE_URL`
   environment variable'ini beradi (`dj-database-url` shuni o'qiydi).
4. Quyidagi environment variable'larni sozlang (Railway → Variables):
   - `SECRET_KEY` — uzun tasodifiy satr
   - `DEBUG` = `False`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_WEBHOOK_SECRET`
   - (ixtiyoriy) `CSRF_TRUSTED_ORIGINS` = `https://sizning-domeningiz.up.railway.app`
5. Railway `Procfile`'ni o'qib avtomatik `release` bosqichida migratsiyalarni
   ishga tushiradi va `web` bosqichida `gunicorn`ni ishga tushiradi
   (`railway.json` ham buni belgilaydi, agar Procfile o'qilmasa).
6. Deploy tugagach, Railway shell/terminal orqali (yoki `railway run`):

   ```bash
   python manage.py create_admin --username admin --password kuchli_parol
   ```

7. `https://<domeningiz>/login/` orqali admin sifatida kiring.

## Statik fayllar

`whitenoise` statik fayllarni ishlab chiqarishda (production) to'g'ridan-to'g'ri
gunicorn orqali xizmat qiladi — alohida sozlash shart emas. Deploydan avval
kerak bo'lsa:

```bash
python manage.py collectstatic --noinput
```
