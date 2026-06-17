import asyncio
import sqlite3
import random
import os
from pyrogram import Client
from pyrogram.errors import FloodWait, UserPrivacyRestricted, UserAlreadyParticipant

# --- البيانات الخاصة بك ---
API_ID = 36472385
API_HASH = "ce35a173b6e58ee45ac703dfbcd76138"
BOT_TOKEN = "8838892412:AAEqHINTvqtJKx6FfFGXLQPy19MIZAHHZVE"

SOURCE_CHAT = "C725C2"    # الجروب المنقول منه
TARGET_CHAT = "C263C"     # الجروب المنقول إليه

# --- إعداد قاعدة بيانات الحفظ الذكي ---
conn = sqlite3.connect("members_database.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS added_members (
        user_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

# تشغيل العميل كـ Userbot مستقر وثابت
app = Client("adder_userbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def is_already_added(user_id):
    cursor.execute("SELECT 1 FROM added_members WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO added_members (user_id) VALUES (?)", (user_id,))
    conn.commit()

async def main():
    async with app:
        print("[+] تم الاتصال بنجاح. جاري فحص تفاعلات الأعضاء...")
        
        try:
            source_peer = await app.get_chat(SOURCE_CHAT)
            target_peer = await app.get_chat(TARGET_CHAT)
        except Exception as e:
            print(f"[❌] خطأ في الوصول للجروبات. تأكد أن البوت/الحساب عضو فيها ومشرف: {e}")
            return
        
        # جلب آخر 100 منشور لفحص التفاعلات
        async for message in app.get_chat_history(source_peer.id, limit=100):
            if message.reactions:
                try:
                    async for peers in app.get_media_reaction_users(source_peer.id, message.id):
                        if not peers.user:
                            continue
                        
                        user_id = peers.user.id
                        user_name = peers.user.username or peers.user.first_name
                        
                        if is_already_added(user_id):
                            continue
                            
                        print(f"[*] تم العثور على عضو متفاعل جديد: {user_name} ({user_id})")
                        
                        try:
                            # إضافة العضو للجروب المستهدف
                            await app.add_chat_members(target_peer.id, user_id)
                            print(f"[✅] تم إضافة {user_name} بنجاح.")
                            save_user(user_id)
                            
                            # فاصل زمني عشوائي آمن لمنع الحظر وضمان إضافة أكبر عدد
                            sleep_time = random.randint(35, 65)
                            print(f"[💤] انتظار آمن لمدة {sleep_time} ثانية...")
                            await asyncio.sleep(sleep_time)
                            
                        except FloodWait as e:
                            print(f"[⚠️] تلجرام يطلب التوقف المؤقت. انتظار {e.value} ثانية...")
                            await asyncio.sleep(e.value)
                        except UserPrivacyRestricted:
                            print(f"[❌] تعذر إضافة {user_name} بسبب خصوصية حسابه.")
                            save_user(user_id)
                        except UserAlreadyParticipant:
                            print(f"[ℹ️] العضو {user_name} موجود بالفعل هناك.")
                            save_user(user_id)
                        except Exception as e:
                            print(f"[💥] تعذر إضافة {user_name}: {e}")
                            
                except Exception as e:
                    # تخطي المنشور إذا حدث خطأ في جلب تفاعلاته
                    continue

if __name__ == "__main__":
    app.run(main())

