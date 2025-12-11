import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

bot = telebot.TeleBot(BOT_TOKEN)

REQUIRED_CHANNELS = ["@dd_fft", "@nn_ccni"]

EPISODES = {
    "Mirm": {
        "1": "FILE_ID_EP1",
        "2": "FILE_ID_EP2",
        "3": "FILE_ID_EP3"
    },
    "Vikings": {
        "1": "FILE_ID_VIK1",
        "2": "FILE_ID_VIK2"
    },
    "Alice in Borderland": {
        "1": "FILE_ID_Alice1",
        "2": "FILE_ID_Alice2"
    }
}

USER_FILE = "users.txt"


def add_user(user_id):
    try:
        with open(USER_FILE, "r") as f:
            users = set(f.read().splitlines())
    except FileNotFoundError:
        users = set()

    if str(user_id) not in users:
        users.add(str(user_id))
        with open(USER_FILE, "w") as f:
            f.write("\n".join(users))


def get_user_count():
    try:
        with open(USER_FILE, "r") as f:
            users = set(f.read().splitlines())
        return len(users)
    except FileNotFoundError:
        return 0


def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    add_user(user_id)

    if not check_subscription(user_id):
        keyboard = InlineKeyboardMarkup()
        for ch in REQUIRED_CHANNELS:
            keyboard.add(
                InlineKeyboardButton(f"اشترك في {ch}",
                                     url=f"https://t.me/{ch[1:]}"))
        keyboard.add(
            InlineKeyboardButton("✔️ تحقّق من الاشتراك",
                                 callback_data="check_sub"))
        bot.send_message(message.chat.id,
                         "🔔 الرجاء الاشتراك في القنوات التالية اولًا:",
                         reply_markup=keyboard)
        return

    show_series_menu(message.chat.id)


def show_series_menu(chat_id):
    keyboard = InlineKeyboardMarkup()
    for series_name in EPISODES.keys():
        keyboard.add(
            InlineKeyboardButton(series_name,
                                 callback_data=f"series_{series_name}"))
    bot.send_message(chat_id, "📺 اختر المسلسل:", reply_markup=keyboard)


def show_episodes(chat_id, series_name):
    keyboard = InlineKeyboardMarkup()
    for ep_num in EPISODES[series_name].keys():
        keyboard.add(
            InlineKeyboardButton(f"الحلقة {ep_num}",
                                 callback_data=f"ep_{series_name}_{ep_num}"))
    bot.send_message(chat_id,
                     f"🎞 اختر حلقة من {series_name}:",
                     reply_markup=keyboard)


def send_video(chat_id, series_name, ep_num):
    file_id = EPISODES[series_name].get(ep_num)
    if not file_id:
        bot.send_message(chat_id, "❌ الحلقة غير موجودة.")
        return
    bot.send_message(chat_id, f"🎬 {series_name} – الحلقة {ep_num}")
    bot.send_video(chat_id, file_id)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data
    user_id = call.from_user.id

    if data == "check_sub":
        if check_subscription(user_id):
            bot.edit_message_text("✔️ تم التحقق! أهلاً بيك ❤️",
                                  call.message.chat.id,
                                  call.message.message_id)
            show_series_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id,
                                      "❌ لسه مشتركتش في كل القنوات!",
                                      show_alert=True)
        return

    if data.startswith("series_"):
        series_name = data.split("_", 1)[1]
        show_episodes(call.message.chat.id, series_name)
        return

    if data.startswith("ep_"):
        _, series_name, ep_num = data.split("_")
        send_video(call.message.chat.id, series_name, ep_num)
        return


@bot.message_handler(content_types=["video"])
def get_file_id(message):
    bot.reply_to(message,
                 f"📌 FILE_ID:\n{message.video.file_id}",
                 parse_mode="Markdown")


print("Bot is starting...")
bot.polling()
