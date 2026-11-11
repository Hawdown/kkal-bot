import base64
from openai import OpenAI
import telebot

BOT_TOKEN = "9097879444:AAEZJfhBjscvL3CxSfgDHdJTm_xv5J_r7Oc"
PROXYAPI_KEY = "sk-Puf1u6JeY80t1KGui9kCXew7V35OVqkM"

bot = telebot.TeleBot(BOT_TOKEN)

client = OpenAI(
    api_key=PROXYAPI_KEY,
    base_url = "https://proxyapi.ru",

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
      "Привет! Отправь мне фото еды, и я посчитаю её КБЖУ. Можешь добавить"
      " подпись к фото с точным весом.",
  )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
  msg = bot.reply_to(message, "Считаю КБЖУ по фото...")

  try:
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    base64_image = base64.b64encode(downloaded_file).decode("utf-8")

    user_caption = (
        f"\Уточнение от пользователя: {message.caption}"
        if message.caption
        else ""
    )

    response = client.chat.completions.create(
        model = "openai/gpt-4.1-mini",
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

    result_text = response.choices[0].message.content
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
