import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from openai import OpenAI

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
SESSION_STRING = os.environ["SESSION_STRING"]  # Mana shu qator qo'shildi

# StringSession orqali ulanamiz (endi raqam so'ramaydi)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

bot_active = True

@client.on(events.NewMessage(pattern='/stop', outgoing=True))
async def stop_bot(event):
    global bot_active
    bot_active = False
    await event.edit("🔴 **AI yordamchi vaqtincha o'chirildi!** Endi xabarlarga javob bermaydi.")

@client.on(events.NewMessage(pattern='/start_bot', outgoing=True))
async def start_bot(event):
    global bot_active
    bot_active = True
    await event.edit("🟢 **AI yordamchi qaytadan yoqildi!** Xabarlarga javob berishni boshladi.")

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

    messages_iter = client.iter_messages(event.chat_id, limit=1)
    async for last_msg in messages_iter:
        if last_msg.out:
            return

    incoming_message = event.raw_text
    print(f"Kelgan xabar: {incoming_message}")

    try:
        has_our_message = False
        async for msg in client.iter_messages(event.chat_id, limit=15):
            if msg.out:
                has_our_message = True
                break

        if not has_our_message:
            welcome_text = (
                "Hozirda **Soibnazarov Ro'zimurod** bandlar, lekin **tez orada yana aloqaga chiqadilar**.\n"
                "🤖 Ungacha ularning o'rniga men — sun'iy intellekt (**AI**) yordamchisi javob beryapman.\n\n"
                "💬 Biz bilan istalgan mavzuda bemalol suhbatlashishingiz va savollaringizni berishingiz mumkin. Sizga qanday yordam bera olaman?"
            )
            await event.reply(welcome_text)
            print("Bandlik matni yuborildi.")
            return

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
        print(f"Yuborilgan javob: {ai_reply}")
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await event.reply("Hozirda Soibnazarov Ro'zimurod bandlar, lekin tez orada yana aloqaga chiqadilar. Men ularning AI yordamchisiman! 🤖")

def main():
    print("AI yordamchi ishga tushdi...")
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
