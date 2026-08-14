import os
import time
import urllib.request
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from openai import OpenAI

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
SESSION_STRING = os.environ["SESSION_STRING"]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

bot_active = True
welcomed_chats = {}

@client.on(events.NewMessage(pattern='/stop', outgoing=True))
async def stop_bot(event):
    global bot_active
    bot_active = False
    await event.edit("🔴 **AI yordamchi vaqtincha o'chirildi!**")

@client.on(events.NewMessage(pattern='/start_bot', outgoing=True))
async def start_bot(event):
    global bot_active
    bot_active = True
    await event.edit("🟢 **AI yordamchi qaytadan yoqildi!**")

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global bot_active
    
    if not bot_active:
        return

    sender = await event.get_sender()
    if sender and sender.bot:
        return

    is_group = event.is_group or event.is_channel
    
    # Guruhda bo'lsa: faqat @mention qilinganda yoki sizning xabaringizga reply qilingandagina ishlaydi
    if is_group:
        is_mentioned = event.mentioned
        is_reply_to_me = False
        
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.out: # Agar siz yozgan xabarga reply qilingan bo'lsa
                is_reply_to_me = True
                
        if not is_mentioned and not is_reply_to_me:
            return # Guruhdagi boshqa xabarlarga e'tibor bermaydi

    # Shaxsiy chatda o'zingiz yozgan bo'lsangiz to'xtaydi
    if not is_group:
        messages_iter = client.iter_messages(event.chat_id, limit=1)
        async for last_msg in messages_iter:
            if last_msg.out:
                return

    incoming_message = event.raw_text or ""
    chat_id = event.chat_id
    current_time = time.time()

    try:
        # --- 1. OVOZLI XABARNI MATNGA O'GIRISH ---
        if event.voice or event.audio:
            await event.reply("🎤 *Ovozli xabar qabul qilindi, tinglab matnga o'giryapman...*")
            file_path = await event.download_media(file="temp_audio.ogg")
            
            with open(file_path, "rb") as audio_file:
                transcript = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file
                )
            incoming_message = transcript.text
            os.remove(file_path) # Faylni o'chirib tashlaymiz

        # --- 2. RASMLAR BILAN ISHLASH ---
        image_url = None
        if event.photo:
            file_path = await event.download_media(file="temp_image.jpg")
            # Groq hozircha Vision uchun internetga yuklangan rasm linkini yoki base64 ishlatadi. 
            # Sodda usulda: rasm kelganini bildirib, AI'ga matn yuboramiz
            incoming_message = "[Foydalanuvchi rasm yubordi va shunday dedi: " + (incoming_message or "Rasm bo'yicha fikringizni bildiring") + "]"
            if os.path.exists(file_path):
                os.remove(file_path)

        # --- 3. BANDLIK XABARI (Faqat shaxsiy chat uchun 1 kunda 1 marta) ---
        if not is_group:
            ONE_DAY_SECONDS = 24 * 60 * 60
            needs_welcome = False
            
            if chat_id not in welcomed_chats:
                needs_welcome = True
            else:
                if current_time - welcomed_chats[chat_id] > ONE_DAY_SECONDS:
                    needs_welcome = True

            if needs_welcome:
                welcome_text = (
                    "Hozirda **Soibnazarov Ro'zimurod** bandlar, lekin **tez orada yana aloqaga chiqadilar**.\n"
                    "🤖 Ungacha ularning o'rniga men — sun'iy intellekt (**AI**) yordamchisi javob beryapman.\n\n"
                    "💬 Menga xohlagan matnli, ovozli yoki rasm ko'rinishidagi savollaringizni yuborishingiz mumkin. Qanday yordam bera olaman?"
                )
                await event.reply(welcome_text)
                welcomed_chats[chat_id] = current_time
                return

        # --- 4. AI JAVOB QAYTARISH ---
        system_prompt = (
            "Siz Soibnazarov Ro'zimurodning sun'iy intellekt (AI) yordamchisiz. "
            "O'zbek tilida imlo xatolarisiz, savodli va ravon yozing. "
            "Faqat har bir javobingizda qisqacha 'Men Ro'zimurodning AI yordamchisiman' deb eslatib o'ting va savoliga chiroyli emojilar bilan javob bering."
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": incoming_message or "Salom"}
            ]
        )
        
        ai_reply = response.choices[0].message.content
        await event.reply(ai_reply)
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await event.reply("Hozirda Soibnazarov Ro'zimurod bandlar. Men ularning AI yordamchisiman! 🤖")

def main():
    print("Mukammal AI yordamchi ishga tushdi...")
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
