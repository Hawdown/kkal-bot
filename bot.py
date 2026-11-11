import base64
from openai import OpenAI
import telebot

BOT_TOKEN = "9097879444:AAEZJfhBjscvL3CxSfgDHdJTm_xv5J_r7Oc"
PROXYAPI_KEY = "sk-Puf1u6JeY80t1KGui9kCXew7V35OVqkM"
ALLOWED_TOPIC_ID = 3

bot = telebot.TeleBot(BOT_TOKEN)

client = OpenAI(
    api_key=PROXYAPI_KEY,
    base_url="https://api.proxyapi.ru/v1",
)

PROMPT = (
    "Определи все блюда и продукты на фото, оцени их примерный вес в граммах. "
    "Рассчитай калории, белки, жиры и углеводы (КБЖУ) для каждого продукта и итоговую сумму. "
    "Отвечай кратко, по делу и списком."
)


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Отправь мне фото еды в ветку «Питание», и я посчитаю её КБЖУ.",
  )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
  if message.chat.type in ["group", "supergroup"]:
    if message.message_thread_id != ALLOWED_TOPIC_ID:
      return

  msg = bot.reply_to(message, "Считаю КБЖУ по фото...")

  try:
    photo = message.photo.pop()
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    base64_image = base64.b64encode(downloaded_file).decode("utf-8")

    user_caption = (
        f"\nУточнение от пользователя: {message.caption}"
        if message.caption
        else ""
    )

    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT + user_caption},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ],
        }],
        max_tokens=500,
    )

    first_choice = next(iter(response.choices))
    result_text = first_choice.message.content

    bot.edit_message_text(
        result_text, chat_id=message.chat.id, message_id=msg.message_id
    )
  except Exception as e:
    bot.edit_message_text(
        f"Ошибка при анализе: {e}",
        chat_id=message.chat.id,
        message_id=msg.message_id,
    )


print("Бот запущен!")
bot.polling(none_stop=True)
