import os
import time
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

# Kimga qachon bandlik xabari yuborilganini vaqt bilan birga saqlash uchun lug'at (Dictionary)
# Format: {chat_id: oxirgi_yuborilgan_vaqt_sekundda}
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

    if not event.is_private:
        return

    sender = await event.get_sender()
    if sender and sender.bot:
        return

    # Agar oxirgi xabarni o'zingiz yozgan bo'lsangiz, bot aralashmaydi
    messages_iter = client.iter_messages(event.chat_id, limit=1)
    async for last_msg in messages_iter:
        if last_msg.out:
            return

    incoming_message = event.raw_text
    chat_id = event.chat_id
    current_time = time.time() # Hozirgi vaqt sekundlarda

    print(f"Kelgan xabar: {incoming_message} (Chat ID: {chat_id})")

    try:
        # 1 kundan qancha sekund o'tishini hisoblaymiz (24 soat * 60 minut * 60 sekund = 86400 sekund)
        ONE_DAY_SECONDS = 24 * 60 * 60
        
        # Bu odamga oldin bandlik xabari yuborilganmi va 24 soat o'tganmi?
        needs_welcome = False
        
        if chat_id not in welcomed_chats:
            needs_welcome = True
        else:
            # Agar oxirgi yuborilgan vaqtdan 24 soat (1 kun) o'tgan bo'lsa, yana bandlik xabarini yuboramiz
            if current_time - welcomed_chats[chat_id] > ONE_DAY_SECONDS:
                needs_welcome = True

        if needs_welcome:
            welcome_text = (
                "Hozirda **Soibnazarov Ro'zimurod** bandlar, lekin **tez orada yana aloqaga chiqadilar**.\n"
                "🤖 Ungacha ularning o'rniga men — sun'iy intellekt (**AI**) yordamchisi javob beryapman.\n\n"
                "💬 Biz bilan istalgan mavzuda bemalol suhbatlashishingiz va savollaringizni berishingiz mumkin. Sizga qanday yordam bera olaman?"
            )
            await event.reply(welcome_text)
            welcomed_chats[chat_id] = current_time # Hozirgi vaqtni saqlab qo'yamiz
            print("Bandlik matni yuborildi (1 kunlik muddat yangilandi).")
            return

        # Agar 1 kun o'tmagan bo'lsa, AI orqali javob beramiz
        system_prompt = (
            "Siz Soibnazarov Ro'zimurodning sun'iy intellekt (AI) yordamchisiz. "
            "O'zbek tilida imlo xatolarisiz, savodli va ravon yozing. "
            "MUHIM: Ro'zimurod band ekanligi va tez orada qaytishi haqida allaqachon birinchi xabarda aytilgan, shuning uchun buni qaytarib o'tirmang. "
            "Faqat har bir javobingizda qisqacha 'Men Ro'zimurodning AI yordamchisiman' deb eslatib o'ting va suhbatdoshga istalgan mavzuda suhbatni davom ettirishi mumkinligini bildirib, savoliga chiroyli emojilar bilan javob bering."
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": incoming_message}
            ]
        )
        
        ai_reply = response.choices[0].message.content
        await event.reply(ai_reply)
        print(f"AI javobi yuborildi: {ai_reply}")
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await event.reply("Hozirda Soibnazarov Ro'zimurod bandlar, lekin tez orada yana aloqaga chiqadilar. Men ularning AI yordamchisiman! 🤖")

def main():
    print("AI yordamchi 1 kunlik xotira bilan ishga tushdi...")
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
