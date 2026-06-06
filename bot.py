#!/usr/bin/env python3
"""
WarungKu Store Bot v2 — FULL OTOMATIS
Product selection → Payment → Auto-deliver → Auto-tutorial → Auto-FAQ
Zero manual intervention needed.
"""
import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ============ CONFIG ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7145398431"))
STORE_NAME = "WarungKu Store"

# Products with auto-tutorial
PRODUCTS = {
    "pkg_excel": {
        "name": "Template HPP Excel",
        "price": 49000,
        "desc": "📊 Template HPP + Kalkulator Otomatis",
        "file": "Template_HPP_WarungKu.xlsx",
        "features": [
            "✅ Auto hitung HPP per porsi",
            "✅ Rekomendasi harga jual (30/50/70%)",
            "✅ Dashboard profit bulanan",
        ],
        "tutorial": """📖 *CARA PAKAI — Template HPP Excel*

*Step 1: Buka file*
Download → buka di Excel atau Google Sheets

*Step 2: Isi data bahan (kolom kuning)*
• Nama Bahan: contoh "Kopi bubuk"
• Harga Beli: harga per kemasan (contoh: 45000)
• Isi Kemasan: berat/isi (contoh: 500 gram)
• Pakai/Porsi: berapa dipakai per porsi (contoh: 15 gram)

*Step 3: Lihat hasil otomatis*
• HPP per porsi = auto hitung ✅
• Harga jual = auto rekomendasi ✅

*Step 4: Copy sheet untuk produk baru*
Klik kanan sheet "Kalkulator HPP" → Move or Copy → Create Copy

*Tips:*
• Margin 50% = sweet spot untuk kebanyakan warung
• Jangan lupa hitung biaya operasional juga
• Review harga bahan tiap bulan (harga naik/turun)

❓ Ada masalah? Ketik /faq"""
    },
    "pkg_pro": {
        "name": "WarungKu Pro",
        "price": 149000,
        "desc": "⚡ Aplikasi Kasir + HPP + Stok Lengkap",
        "file": "warungku-pro.zip",
        "features": [
            "✅ Kasir lengkap (struk, QRIS)",
            "✅ HPP otomatis per produk",
            "✅ Manajemen stok & restock",
            "✅ Laporan harian & grafik",
            "✅ Multi-kasir (tim)",
        ],
        "tutorial": """📖 *CARA PAKAI — WarungKu Pro*

*Step 1: Extract file*
Download → unzip warungku-pro.zip

*Step 2: Install & Jalankan*
```bash
npm install
npm run dev
```
Buka http://localhost:3000

*Step 3: Setup awal*
1. Login: teguh@warung.com / warung123
2. Buka Settings → ganti nama warung
3. Buka Bahan → input semua bahan baku
4. Buka Produk → buat produk + resep

*Step 4: Pakai Kasir*
1. Buka halaman Kasir
2. Pilih produk yang dijual
3. Input uang bayar → auto hitung kembalian
4. Cetak struk / kirim QRIS

*Step 5: Pantau Laporan*
• Buka Laporan → lihat grafik harian
• Export data kapan aja

*Hosting (opsional):*
• Gratis di Vercel: `npx vercel --prod`
• Atau di VPS sendiri

❓ Ada masalah? Ketik /faq"""
    },
    "pkg_bundle": {
        "name": "Bundle Lengkap",
        "price": 299000,
        "desc": "🎓 Semua tools + video tutorial",
        "file": "warungku-bundle.zip",
        "features": [
            "✅ Template HPP Excel",
            "✅ WarungKu Pro (full source)",
            "✅ Video tutorial (2 jam)",
            "✅ Grup WhatsApp eksklusif",
            "✅ Update gratis selamanya",
        ],
        "tutorial": """📖 *CARA PAKAI — Bundle Lengkap*

Paket ini berisi SEMUA tools + video tutorial.

*Isi Bundle:*
1. 📊 Template_HPP_WarungKu.xlsx
2. ⚡ warungku-pro.zip (aplikasi kasir)
3. 🎥 video-tutorial/ (2 jam)
4. 📄 panduan-lengkap.pdf

*Step 1: Extract semua*
Download warungku-bundle.zip → extract

*Step 2: Tonton video tutorial*
Buka folder video-tutorial/ → tonton urut:
1. Pengenalan HPP (15 menit)
2. Setup Template Excel (20 menit)
3. Setup WarungKu Pro (30 menit)
4. Tips pricing & margin (25 menit)
5. Studi kasus warung nyata (30 menit)

*Step 3: Praktek langsung*
Ikuti video sambil praktek di usaha lu

*Step 4: Join grup WhatsApp*
Link ada di file "grup-wa.txt"

❓ Ada masalah? Ketik /faq"""
    }
}

# Auto-FAQ responses
FAQ = {
    "hpp": {
        "question": "Apa itu HPP?",
        "answer": """*HPP = Harga Pokok Penjualan*

HPP = total biaya bahan baku untuk bikin 1 porsi produk.

*Contoh:*
Kopi Susu:
• Kopi: Rp 45.000/500gr × 15gr = Rp 1.350
• Susu: Rp 18.000/1ltr × 200ml = Rp 3.600
• Gula: Rp 15.000/1kg × 20gr = Rp 300
• Cup: Rp 35.000/50pcs × 1 = Rp 700
• Total HPP = Rp 5.950

*Harga Jual = HPP ÷ (1 - margin)*
Kalau mau margin 50%: Rp 5.950 ÷ 0.5 = Rp 11.900

Dibuletin jadi Rp 12.000 ✅"""
    },
    "margin": {
        "question": "Berapa margin yang bagus?",
        "answer": """*Rekomendasi Margin:*

• 30% — Budget-friendly, volume tinggi
• 50% — Sweet spot, cocok untuk kebanyakan warung ✅
• 70% — Premium, untuk produk unik/branded

*Tips:*
• Cek harga kompetitor di sekitar lu
• Kalau margin 50% tapi harga lebih mahal dari tetangga → turunin margin
• Kalau produk lu beda/lebih enak → boleh naikin margin

*Jangan lupa:* HPP belum termasuk biaya operasional (listrik, sewa, dll). Tambahin ke harga jual kalau perlu."""
    },
    "stok": {
        "question": "Gimana cara hitung stok?",
        "answer": """*Hitung Stok dari Bahan:*

Rumus: *Stok = Isi Kemasan ÷ Pakai per Porsi*

*Contoh:*
Kopi bubuk 500gr, pakai 15gr/porsi
Stok = 500 ÷ 15 = 33 porsi

*Tips:*
• Cek stok setiap hari
• Set alarm kalau stok < 10 porsi
• Restock sebelum habis (minimal 2 hari sebelum)
• Catat semua restock di sheet Dashboard"""
    },
    "kasir": {
        "question": "Gimana cara pakai kasir?",
        "answer": """*Cara Pakai Kasir WarungKu:*

1. Buka http://localhost:3000/kasir
2. Set saldo awal kasir (berapa uang di laci)
3. Pilih produk yang dibeli customer
4. Masukkan uang bayar → auto hitung kembalian
5. Klik "Bayar" → struk muncul
6. Cetak struk atau kirim QRIS

*Fitur:*
• Auto kurangi stok setelah jual
• Catat semua transaksi
• Laporan harian otomatis"""
    },
    "qris": {
        "question": "Gimana cara pakai QRIS?",
        "answer": """*Setup QRIS di WarungKu:*

1. Buka Settings
2. Upload foto QRIS lu (dari bank/e-wallet)
3. Saat kasir, klik "QRIS" → QR muncul di layar
4. Customer scan → bayar
5. Lu klik "Konfirmasi Bayar"

*Catatan:*
Ini QRIS statis (bukan payment gateway). Lu perlu cek manual kalau uang masuk. Cocok untuk warung kecil."""
    },
    "backup": {
        "question": "Gimana cara backup data?",
        "answer": """*Backup Data WarungKu:*

1. Buka Settings
2. Klik "Export Data" → download file JSON
3. Simpan file backup di tempat aman

*Restore Data:*
1. Buka Settings
2. Klik "Import Data"
3. Pilih file backup JSON

*Tips:*
• Backup seminggu sekali
• Simpan di Google Drive / email
• Sebelum update app, backup dulu"""
    },
    "error": {
        "question": "Aplikasi error/crash?",
        "answer": """*Troubleshooting:*

1. *App nggak jalan*
   → Cek Node.js terinstall: `node -v`
   → Install ulang: `npm install`

2. *Halaman blank*
   → Clear browser cache
   → Coba browser lain

3. *Data hilang*
   → Restore dari backup (Settings → Import)
   → Data tersimpan di browser (localStorage)

4. *Port 3000 dipake*
   → Ganti port: `npm run dev -- -p 3001`

Masih error? Ketik pesan error-nya, admin bantu."""
    }
}

ORDERS_FILE = "/home/ubuntu/hpp-store/orders.json"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_orders():
    try:
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_orders(orders):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

# ============ HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    
    if args and args[0] in PRODUCTS:
        await show_product(update, context, args[0])
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Template HPP Excel — Rp 49rb", callback_data="pkg_excel")],
        [InlineKeyboardButton("⚡ WarungKu Pro — Rp 149rb", callback_data="pkg_pro")],
        [InlineKeyboardButton("🎓 Bundle Lengkap — Rp 299rb", callback_data="pkg_bundle")],
        [InlineKeyboardButton("❓ FAQ / Bantuan", callback_data="faq_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""👋 Halo {user.first_name}!

Selamat datang di *{STORE_NAME}* 🔥

Tools HPP & keuangan untuk UMKM Indonesia.

*Pilih produk di bawah 👇*"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str):
    product = PRODUCTS[product_id]
    features = "\n".join(product["features"])
    
    text = f"""*{product['desc']}*

{features}

💰 *Harga: Rp {product['price']:,}*
(Sekali bayar, pakai selamanya)

📦 Langsung kirim file + tutorial otomatis!"""
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 Beli Sekarang — Rp {product['price']:,}", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    
    if data == "back":
        keyboard = [
            [InlineKeyboardButton("📊 Template HPP Excel — Rp 49rb", callback_data="pkg_excel")],
            [InlineKeyboardButton("⚡ WarungKu Pro — Rp 149rb", callback_data="pkg_pro")],
            [InlineKeyboardButton("🎓 Bundle Lengkap — Rp 299rb", callback_data="pkg_bundle")],
            [InlineKeyboardButton("❓ FAQ / Bantuan", callback_data="faq_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🔥 *{STORE_NAME}*\n\nPilih produk:",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return
    
    if data == "faq_menu":
        keyboard = [
            [InlineKeyboardButton("📊 Apa itu HPP?", callback_data="faq_hpp")],
            [InlineKeyboardButton("💰 Berapa margin yang bagus?", callback_data="faq_margin")],
            [InlineKeyboardButton("📦 Gimana hitung stok?", callback_data="faq_stok")],
            [InlineKeyboardButton("🛒 Gimana pakai kasir?", callback_data="faq_kasir")],
            [InlineKeyboardButton("📱 Gimana pakai QRIS?", callback_data="faq_qris")],
            [InlineKeyboardButton("💾 Gimana backup data?", callback_data="faq_backup")],
            [InlineKeyboardButton("⚠️ Aplikasi error?", callback_data="faq_error")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❓ *FAQ — Pertanyaan Umum*\n\nPilih pertanyaan:",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return
    
    if data.startswith("faq_"):
        faq_key = data.replace("faq_", "")
        if faq_key in FAQ:
            faq = FAQ[faq_key]
            keyboard = [
                [InlineKeyboardButton("❓ FAQ Lainnya", callback_data="faq_menu")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="back")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"*{faq['question']}*\n\n{faq['answer']}",
                reply_markup=reply_markup, parse_mode="Markdown"
            )
        return
    
    if data.startswith("buy_"):
        product_id = data.replace("buy_", "")
        product = PRODUCTS[product_id]
        order_id = f"ORD-{user.id}-{int(datetime.now().timestamp())}"
        
        orders = load_orders()
        orders[order_id] = {
            "user_id": user.id,
            "username": user.username or user.first_name,
            "product_id": product_id,
            "product_name": product["name"],
            "price": product["price"],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        save_orders(orders)
        
        text = f"""🛒 *Pesanan: {product['name']}*

💰 Total: *Rp {product['price']:,}*
📋 Order ID: `{order_id}`

*Transfer ke:*
🏦 BCA: 1234567890 a/n Teguh
📱 Dana: 081234567890

*Atau scan QRIS:*
_(kirim foto QRIS lu ke bot ini, nanti muncul di sini)_

Setelah bayar, kirim bukti transfer 👇"""
        
        keyboard = [
            [InlineKeyboardButton("❌ Batal", callback_data="back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data["current_order"] = order_id
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 *Order Baru!*\n\nUser: @{user.username or user.first_name}\nProduk: {product['name']}\nHarga: Rp {product['price']:,}\nID: `{order_id}`",
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("confirm_"):
        order_id = data.replace("confirm_", "")
        orders = load_orders()
        if order_id in orders:
            order = orders[order_id]
            order["status"] = "paid"
            order["paid_at"] = datetime.now().isoformat()
            save_orders(orders)
            
            product = PRODUCTS[order["product_id"]]
            file_path = f"/home/ubuntu/hpp-store/files/{product['file']}"
            
            # Send product file
            try:
                with open(file_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=order["user_id"],
                        document=f,
                        caption=f"✅ *Pembayaran Dikonfirmasi!*\n\n📦 Produk: {product['name']}\n📋 Order: `{order_id}`\n\n⬇️ Tutorial lengkap ada di bawah 👇",
                        parse_mode="Markdown"
                    )
            except FileNotFoundError:
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"✅ Pembayaran dikonfirmasi! Admin kirim produk lu sebentar lagi."
                )
            
            # Auto-send tutorial
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=product["tutorial"],
                parse_mode="Markdown"
            )
            
            # Auto-send FAQ menu
            keyboard = [
                [InlineKeyboardButton("❓ FAQ / Bantuan", callback_data="faq_menu")],
                [InlineKeyboardButton("🛒 Beli Lagi", callback_data="back")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=order["user_id"],
                text="💡 *Butuh bantuan?*\n\nKlik tombol di bawah atau ketik pertanyaan lu langsung.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            await query.edit_message_text(f"✅ Order {order_id} dikonfirmasi! File + tutorial terkirim.")
        return
    
    if data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "rejected"
            save_orders(orders)
            await context.bot.send_message(
                chat_id=orders[order_id]["user_id"],
                text="❌ Pembayaran tidak valid. Kirim ulang bukti transfer yang benar."
            )
            await query.edit_message_text(f"❌ Order {order_id} ditolak.")
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order_id = context.user_data.get("current_order")
    
    if not order_id:
        await update.message.reply_text("📸 Foto diterima! Tapi belum ada order aktif. Ketik /start untuk mulai.")
        return
    
    orders = load_orders()
    if order_id not in orders:
        await update.message.reply_text("❌ Order tidak ditemukan. Ketik /start untuk mulai baru.")
        return
    
    order = orders[order_id]
    order["status"] = "proof_sent"
    order["proof_file_id"] = update.message.photo[-1].file_id
    save_orders(orders)
    
    await update.message.reply_text(
        "✅ *Bukti bayar diterima!*\n\nAdmin verifikasi 1-5 menit. Produk + tutorial langsung dikirim otomatis.",
        parse_mode="Markdown"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{order_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    product = PRODUCTS[order["product_id"]]
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📸 *Bukti Bayar!*\n\nUser: @{user.username or user.first_name}\nProduk: {product['name']}\nHarga: Rp {product['price']:,}\nID: `{order_id}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower()
    
    # Auto-respond to common questions
    for key, faq in FAQ.items():
        if any(word in text for word in faq["question"].lower().split()[:3]):
            keyboard = [
                [InlineKeyboardButton("❓ FAQ Lainnya", callback_data="faq_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"*{faq['question']}*\n\n{faq['answer']}",
                reply_markup=reply_markup, parse_mode="Markdown"
            )
            return
    
    # Forward to admin if no auto-answer
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💬 *Pesan dari @{user.username or user.first_name}:*\n\n{update.message.text}",
        parse_mode="Markdown"
    )
    await update.message.reply_text("💬 Pesan diteruskan ke admin. Tunggu balesan ya!")

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    orders = load_orders()
    if not orders:
        await update.message.reply_text("📋 Belum ada order.")
        return
    text = "📋 *Order Terakhir:*\n\n"
    for oid, order in list(orders.items())[-10:]:
        emoji = {"pending": "⏳", "proof_sent": "📸", "paid": "✅", "rejected": "❌"}.get(order["status"], "❓")
        text += f"{emoji} `{oid}`\n   {order['product_name']} — Rp {order['price']:,}\n   @{order['username']} — {order['status']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Apa itu HPP?", callback_data="faq_hpp")],
        [InlineKeyboardButton("💰 Berapa margin yang bagus?", callback_data="faq_margin")],
        [InlineKeyboardButton("📦 Gimana hitung stok?", callback_data="faq_stok")],
        [InlineKeyboardButton("🛒 Gimana pakai kasir?", callback_data="faq_kasir")],
        [InlineKeyboardButton("📱 Gimana pakai QRIS?", callback_data="faq_qris")],
        [InlineKeyboardButton("💾 Gimana backup data?", callback_data="faq_backup")],
        [InlineKeyboardButton("⚠️ Aplikasi error?", callback_data="faq_error")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "❓ *FAQ — Pertanyaan Umum*\n\nAtau ketik pertanyaan lu langsung!",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

# ============ MAIN ============

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("faq", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print(f"🤖 {STORE_NAME} Bot v2 started!")
    print(f"Admin: {ADMIN_ID}")
    print(f"Products: {len(PRODUCTS)}")
    print(f"FAQ entries: {len(FAQ)}")
    print("Full auto-pilot mode! 🚀")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
