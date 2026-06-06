#!/usr/bin/env python3
"""
WarungKu Store Bot — Telegram Bot for selling digital products
Handles: product selection → payment (QRIS) → auto-delivery
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
ADMIN_ID = int(os.getenv("ADMIN_ID", "7145398431"))  # Teguh's Telegram ID
QRIS_IMAGE = os.getenv("QRIS_IMAGE", "")  # Path to QRIS image
STORE_NAME = "WarungKu Store"

# Products
PRODUCTS = {
    "pkg_excel": {
        "name": "Template HPP Excel",
        "price": 49000,
        "description": "📊 Template HPP + Kalkulator Otomatis",
        "file": "Template_HPP_WarungKu.xlsx",
        "features": [
            "✅ Auto hitung HPP per porsi",
            "✅ Rekomendasi harga jual (30/50/70%)",
            "✅ Dashboard profit bulanan",
            "✅ Panduan penggunaan"
        ]
    },
    "pkg_pro": {
        "name": "WarungKu Pro",
        "price": 149000,
        "description": "⚡ Aplikasi Kasir + HPP + Stok Lengkap",
        "file": "warungku-pro.zip",
        "features": [
            "✅ Kasir lengkap (struk, QRIS)",
            "✅ HPP otomatis per produk",
            "✅ Manajemen stok & restock",
            "✅ Laporan harian & grafik",
            "✅ Multi-kasir (tim)",
            "✅ Source code milik lu",
            "✅ Setup & konsultasi 30 menit"
        ]
    },
    "pkg_bundle": {
        "name": "Bundle Lengkap",
        "price": 299000,
        "description": "🎓 Semua tools + tutorial + konsultasi",
        "file": "warungku-bundle.zip",
        "features": [
            "✅ Template HPP Excel",
            "✅ WarungKu Pro (full source)",
            "✅ Video tutorial (2 jam)",
            "✅ Konsultasi 1-on-1 (1 jam)",
            "✅ Grup WhatsApp eksklusif",
            "✅ Update gratis selamanya"
        ]
    }
}

# Pending orders storage
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
    """Handle /start command and deep links"""
    user = update.effective_user
    args = context.args
    
    # Check for deep link (product selection from landing page)
    if args and args[0] in PRODUCTS:
        await show_product(update, context, args[0])
        return
    
    # Welcome message
    keyboard = [
        [InlineKeyboardButton("📊 Template HPP Excel — Rp 49rb", callback_data="pkg_excel")],
        [InlineKeyboardButton("⚡ WarungKu Pro — Rp 149rb", callback_data="pkg_pro")],
        [InlineKeyboardButton("🎓 Bundle Lengkap — Rp 299rb", callback_data="pkg_bundle")],
        [InlineKeyboardButton("💬 Tanya Dulu", callback_data="ask")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""👋 Halo {user.first_name}!

Selamat datang di *{STORE_NAME}* 🔥

Kami jual tools HPP & keuangan untuk UMKM Indonesia.

*Yang bisa lu dapetin:*
• 📊 Template HPP Excel — auto hitung harga jual
• ⚡ WarungKu Pro — aplikasi kasir lengkap
• 🎓 Bundle — semua tools + konsultasi

*Pilih produk di bawah:*"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str):
    """Show product details"""
    product = PRODUCTS[product_id]
    
    features_text = "\n".join(product["features"])
    text = f"""*{product['description']}*

{features_text}

💰 *Harga: Rp {product['price']:,}*
(Sekali bayar, pakai selamanya)

📦 Langsung kirim file setelah bayar!"""
    
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
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    if data == "back":
        keyboard = [
            [InlineKeyboardButton("📊 Template HPP Excel — Rp 49rb", callback_data="pkg_excel")],
            [InlineKeyboardButton("⚡ WarungKu Pro — Rp 149rb", callback_data="pkg_pro")],
            [InlineKeyboardButton("🎓 Bundle Lengkap — Rp 299rb", callback_data="pkg_bundle")],
            [InlineKeyboardButton("💬 Tanya Dulu", callback_data="ask")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🔥 *{STORE_NAME}*\n\nPilih produk:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    if data == "ask":
        await query.edit_message_text(
            "💬 *Tanya aja langsung!*\n\nKetik pertanyaan lu di chat, gue bales secepetnya.",
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("buy_"):
        product_id = data.replace("buy_", "")
        product = PRODUCTS[product_id]
        
        # Create order
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
📱 QRIS: (klik tombol di bawah)

*Atau scan QRIS:*

Setelah bayar, kirim bukti transfer ke sini 👇"""
        
        keyboard = [
            [InlineKeyboardButton("📸 Kirim Bukti Bayar", callback_data=f"proof_{order_id}")],
            [InlineKeyboardButton("❌ Batal", callback_data="back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store order context
        context.user_data["current_order"] = order_id
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        
        # Notify admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 *Order Baru!*\n\nUser: @{user.username or user.first_name}\nProduk: {product['name']}\nHarga: Rp {product['price']:,}\nID: `{order_id}`",
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("proof_"):
        order_id = data.replace("proof_", "")
        await query.edit_message_text(
            "📸 *Kirim Bukti Bayar*\n\nSilahkan kirim foto/screenshot bukti transfer lu ke chat ini.\n\nGue akan verifikasi dan kirim produknya!",
            parse_mode="Markdown"
        )
        context.user_data["waiting_proof"] = order_id
        return
    
    if data.startswith("confirm_"):
        # Admin confirms payment
        order_id = data.replace("confirm_", "")
        orders = load_orders()
        if order_id in orders:
            order = orders[order_id]
            order["status"] = "paid"
            order["paid_at"] = datetime.now().isoformat()
            save_orders(orders)
            
            # Send product to buyer
            product = PRODUCTS[order["product_id"]]
            file_path = f"/home/ubuntu/hpp-store/files/{product['file']}"
            
            try:
                with open(file_path, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=order["user_id"],
                        document=f,
                        caption=f"✅ *Pembayaran Dikonfirmasi!*\n\n📦 Produk: {product['name']}\n📋 Order: `{order_id}`\n\nTerima kasih sudah beli! 🙏\n\nAda pertanyaan? Chat aja di sini.",
                        parse_mode="Markdown"
                    )
                await query.edit_message_text(f"✅ Order {order_id} dikonfirmasi! File terkirim ke buyer.")
            except FileNotFoundError:
                await query.edit_message_text(f"⚠️ File {product['file']} tidak ditemukan! Kirim manual ke buyer.")
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"✅ Pembayaran sudah dikonfirmasi! Admin akan kirim produk lu sebentar lagi."
                )
        return
    
    if data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        orders = load_orders()
        if order_id in orders:
            orders[order_id]["status"] = "rejected"
            save_orders(orders)
            await context.bot.send_message(
                chat_id=orders[order_id]["user_id"],
                text="❌ Pembayaran tidak valid. Silahkan kirim ulang bukti transfer yang benar."
            )
            await query.edit_message_text(f"❌ Order {order_id} ditolak.")
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment proof photos"""
    user = update.effective_user
    order_id = context.user_data.get("waiting_proof")
    
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
        "✅ *Bukti bayar diterima!*\n\nAdmin akan verifikasi dalam 1-5 menit. Produk langsung dikirim setelah konfirmasi.",
        parse_mode="Markdown"
    )
    
    # Notify admin with proof
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
    
    context.user_data.pop("waiting_proof", None)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user = update.effective_user
    text = update.message.text
    
    # Forward to admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💬 *Pesan dari @{user.username or user.first_name}:*\n\n{text}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("💬 Pesan lu udah diteruskan ke admin. Tunggu balesan ya!")

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: view orders"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    orders = load_orders()
    if not orders:
        await update.message.reply_text("📋 Belum ada order.")
        return
    
    text = "📋 *Daftar Order:*\n\n"
    for oid, order in list(orders.items())[-10:]:
        status_emoji = {"pending": "⏳", "proof_sent": "📸", "paid": "✅", "rejected": "❌"}.get(order["status"], "❓")
        text += f"{status_emoji} `{oid}`\n"
        text += f"   {order['product_name']} — Rp {order['price']:,}\n"
        text += f"   @{order['username']} — {order['status']}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ============ MAIN ============

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print(f"🤖 {STORE_NAME} Bot started!")
    print(f"Admin: {ADMIN_ID}")
    print(f"Products: {len(PRODUCTS)}")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
