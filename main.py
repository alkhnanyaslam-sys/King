import asyncio
import sqlite3
import random
import os
import binascii
from pyrogram import Client, errors
from pyrogram.raw import functions

# --- البيانات ---
API_ID = 36472385
API_HASH = "ce35a173b6e58ee45ac703dfbcd76138"

SOURCE_CHAT = "@C725C2"
TARGET_CHAT = "@C263C"

# تحميل الـ session من الـ Secret
SESSION_HEX = os.environ.get("SESSION_HEX", "")

# تحويل الـ hex لملف session
if SESSION_HEX:
    session_data = binascii.unhexlify(SESSION_HEX)
    with open("adder_userbot.session", "wb") as f:
        f.write(session_data)
    print("[✅] تم تحميل الـ session بنجاح!")
else:
    print("[❌] SESSION_HEX غير موجود في الـ Secrets!")
    exit(1)

# قاعدة البيانات
conn = sqlite3.connect("members_database.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS added_members (
        user_id INTEGER PRIMARY KEY
    )
""")
conn.commit()

app = Client("adder_userbot", api_id=API_ID, api_hash=API_HASH)

def is_already_added(user_id):
    cursor.execute("SELECT 1 FROM added_members WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO added_members (user_id) VALUES (?)", (user_id,))
    conn.commit()

async def get_reactor_ids(chat_id, message_id):
    user_ids = []
    try:
        peer = await app.resolve_peer(chat_id)
        result = await app.invoke(
            functions.messages.GetMessageReactionsList(
                peer=peer,
                id=message_id,
                limit=100
            )
        )
        for user in result.users:
            user_ids.append(user.id)
    except Exception as e:
        print(f"[⚠️] فشل جلب تفاعلات الرسالة {message_id}: {e}")
    return user_ids

async def main():
    async with app:
        print("[+] تم الاتصال بنجاح!")

        try:
            source_chat = await app.get_chat(SOURCE_CHAT)
            target_chat = await app.get_chat(TARGET_CHAT)
            print(f"[✅] جروب المصدر: {source_chat.title}")
            print(f"[✅] جروب الهدف: {target_chat.title}")
        except Exception as e:
            print(f"[❌] خطأ في الجروبات: {e}")
            return

        total_added = 0
        total_skipped = 0

        async for message in app.get_chat_history(source_chat.id, limit=100):
            if not message.reactions:
                continue

            reactor_ids = await get_reactor_ids(source_chat.id, message.id)

            for u_id in reactor_ids:
                if is_already_added(u_id):
                    total_skipped += 1
                    continue

                try:
                    await app.add_chat_members(target_chat.id, u_id)
                    total_added += 1
                    save_user(u_id)
                    print(f"[✅] تم إضافة {u_id} | المجموع: {total_added}")

                    sleep_time = random.randint(45, 90)
                    print(f"[💤] انتظار {sleep_time} ثانية...")
                    await asyncio.sleep(sleep_time)

                except errors.FloodWait as e:
                    print(f"[⚠️] انتظار {e.value} ثانية...")
                    await asyncio.sleep(e.value)

                except errors.UserPrivacyRestricted:
                    print(f"[🔒] {u_id} خصوصيته مغلقة")
                    save_user(u_id)

                except errors.UserAlreadyParticipant:
                    print(f"[ℹ️] {u_id} موجود بالفعل")
                    save_user(u_id)

                except errors.PeerFlood:
                    print("[🚨] خطر حظر! توقف الآن!")
                    return

                except Exception as e:
                    if "Peer id invalid" in str(e):
                        save_user(u_id)
                    else:
                        print(f"[💥] خطأ: {e}")

        print(f"\n[🏁] انتهى! تم إضافة: {total_added} | تم تخطي: {total_skipped}")

if __name__ == "__main__":
    app.run(main())
