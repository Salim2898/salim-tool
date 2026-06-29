import sqlite3
import telebot
from telebot import types
import requests
from datetime import datetime, timedelta

# কনফিগারেশন
API_TOKEN = '8798075735:AAGR6xVl_at6nHqPxJZAxTW11vatfVtZGqk'
ADMIN_ID = 7712500256  
DB_NAME = 'market_v2.db'
bot = telebot.TeleBot(API_TOKEN)

# ডাটাবেজ টেবিল স্ট্রাকচার (রিলিজ টাইমের কলামসহ)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS accounts') # পুরনো ডাটাবেজ মুছে নতুন তৈরি করা
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, hold_balance REAL DEFAULT 0.0, referred_by INTEGER DEFAULT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, platform TEXT, details TEXT, price REAL, status TEXT DEFAULT 'pending', release_time TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# বাটন এবং অন্যান্য ফাংশনগুলো এখানে আপনার আগের কোড অনুযায়ী সেট করবেন...

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_save_'))
def approve_account(call):
    db_id = call.data.split('_')[2]
    # ৩ দিন পরের সময় নির্ধারণ
    release_date = datetime.now() + timedelta(days=3)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE accounts SET status = "approved_hidden", release_time = ? WHERE id = ?', (release_date, db_id))
    cursor.execute('SELECT seller_id, price FROM accounts WHERE id = ?', (db_id,))
    seller_id, price = cursor.fetchone()
    cursor.execute('UPDATE users SET hold_balance = hold_balance + ? WHERE user_id = ?', (price, seller_id))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, "✅ আইডি ৩ দিনের জন্য হোল্ডে রাখা হয়েছে।")
    bot.send_message(ADMIN_ID, f"Item #{db_id} is now on 3-day hold.")

# অটোমেটিক চেক ফাংশন
def check_releases():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('SELECT id, seller_id, price FROM accounts WHERE status = "approved_hidden" AND release_time < ?', (now,))
    items = cursor.fetchall()
    for item in items:
        db_id, seller_id, price = item
        cursor.execute('UPDATE users SET hold_balance = hold_balance - ?, balance = balance + ? WHERE user_id = ?', (price, price, seller_id))
        cursor.execute('UPDATE accounts SET status = "live" WHERE id = ?', (db_id,))
    conn.commit()
    conn.close()

# মূল লুপ
if __name__ == '__main__':
    print("Bot is running perfectly...")
    bot.infinity_polling()