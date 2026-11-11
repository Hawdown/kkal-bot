import base64
from openai import OpenAI
import telebot

BOT_TOKEN = "9097879444:AAEZJfhBjscvL3CxSfgDHdJTm_xv5J_r7Oc"
PROXYAPI_KEY = "sk-Puf1u6JeY80t1KGui9kCXew7V35OVqkM"

bot = telebot.TeleBot(BOT_TOKEN)

PROMPT = (
    "Определи все блюда и продукты на фото, оцени их примерный вес в граммах. "
    "Рассчитай калории, белки, жиры и углеводы (КБЖУ) для каждого продукта и итоговую сумму. "
    "Отвечай кратко, по делу и списком."
)


def ask_vision_model(base64_image, user_caption):
  domain = "api." + "proxyapi.ru"
  configs = [
      (f"https://{domain}/openrouter/v1", "openai/gpt-4.1-mini"),
      (f"https://{domain}/openai/v1", "gpt-4.1-mini"),
      (f"https://{domain}/openai/v1", "gpt-4o-mini"),
  ]
  last_error = None
  for url, model_name in configs:
    try:
      client = OpenAI(api_key=PROXYAPI_KEY, base_url=url)
      response = client.chat.completions.create(
          model=model_name,
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
      return first_choice.message.content
    except Exception as e:
      last_error = f"[{url} | {model_name}]: {e}"
  raise Exception(last_error)


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Отправь мне фото еды (в личку или в группу), и я посчитаю её"
      " КБЖУ.",
  )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
  msg = bot.reply_to(message, "Считаю КБЖУ по фото (v4)...")

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
    result_text = ask_vision_model(base64_image, user_caption)

    bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
    bot.reply_to(message, result_text)

  except Exception as e:
    bot.reply_to(message, f"Ошибка: {e}")


print("Бот запущен!")
bot.polling(none_stop=True)

