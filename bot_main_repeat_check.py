import logging
import pandas as pd
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram import ChatAction
import re
import os
from datetime import datetime

# ========== 配置 ==========
BOT_TOKEN = "7560944933:AAFvq3i5FdJUENcBNsk2Uzir4iYe61Fn_TI"
DATA_FILE = "phone_data.csv"

# ========== 初始化日志 ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# ========== 更宽松的手机号正则 ==========
US_PHONE_PATTERN = re.compile(r"(\+1[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4})")

# ========== 读取已有数据 ==========
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, dtype=str)
    else:
        return pd.DataFrame(columns=["phone", "user", "time"])

# ========== 保存数据 ==========
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ========== 消息处理 ==========
def handle_message(update, context):
    msg = update.message.text
    user = update.message.from_user.username or update.message.from_user.first_name
    chat_id = update.message.chat_id

    logging.info(f"[收到消息] {user}: {msg}")

    found_numbers = US_PHONE_PATTERN.findall(msg)
    if not found_numbers:
        logging.info("[未识别到手机号]")
        return

    df = load_data()
    reply_lines = []

    for num in found_numbers:
        clean_num = re.sub(r"[\s\-]", "", num)  # 清洗：去除空格和横杠
        existing = df[df["phone"] == clean_num]
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not existing.empty:
            old_user = existing.iloc[0]["user"]
            reply_lines.append(f"⚠️ 号码 {clean_num} 已重复登记\n原登记人：@{old_user}\n本次验证人：@{user}")
        else:
            new_row = pd.DataFrame([{
                "phone": clean_num,
                "user": user,
                "time": now_time
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            reply_lines.append(f"✅ 手机号 {clean_num} 已成功入库，登记人：@{user}")

    save_data(df)
    context.bot.send_message(chat_id=chat_id, text="\n\n".join(reply_lines))

# ========== 导出数据命令 ==========
def export_data(update, context):
    chat_id = update.message.chat_id
    df = load_data()

    if df.empty:
        update.message.reply_text("暂无任何手机号数据。")
        return

    file_name = "手机号入库.csv"
    df.to_csv(file_name, index=False)

    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
    context.bot.send_document(chat_id=chat_id, document=open(file_name, "rb"))

# ========== 主入口 ==========
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler("get_data", export_data))
    dp.add_handler(CommandHandler("daochu", export_data))

    updater.start_polling()
    print("🤖 机器人已启动，正在监听群消息...")
    updater.idle()

if __name__ == '__main__':
    main()