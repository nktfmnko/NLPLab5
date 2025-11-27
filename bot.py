import telebot
import requests
import jsons
from typing import List, Optional

API_TOKEN = 'API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

dialog_history = {}

class UsageResponse:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class MessageResponse:
    role: str
    content: str

class ChoiceResponse:
    index: int
    message: MessageResponse
    logprobs: Optional[str]
    finish_reason: str

class ModelResponse:
    id: str
    object: str
    created: int
    model: str
    choices: List[ChoiceResponse]
    usage: UsageResponse
    system_fingerprint: str

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очищает историю диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):    
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id    
    dialog_history[user_id] = []
    bot.reply_to(message, "История диалога очищена!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text

    if user_id not in dialog_history:
        dialog_history[user_id] = []

    dialog_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    request = {
        "messages": dialog_history[user_id]
    }

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        answer = model_response.choices[0].message.content
        
        dialog_history[user_id].append({
            "role": "assistant",
            "content": answer
        })

        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "Ошибка при обращении к модели.")

if __name__ == '__main__':
    bot.polling(none_stop=True)