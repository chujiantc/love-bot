import os
import random
import logging
import threading
import urllib.request
from datetime import datetime, time, timezone, timedelta
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ----------------- 0. 日志配置 -----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------- 1. 轻量保活 Web 服务器 -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Love Bot is active 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

# ----------------- 2. 群组 ID 记录 (双重持久化) -----------------
CHAT_ID_FILE = "chat_id.txt"

def save_chat_id(chat_id):
    try:
        with open(CHAT_ID_FILE, "w") as f:
            f.write(str(chat_id))
    except Exception as e:
        logger.error(f"保存 Chat ID 失败: {e}")

def load_chat_id():
    if os.path.exists(CHAT_ID_FILE):
        try:
            with open(CHAT_ID_FILE, "r") as f:
                cid = f.read().strip()
                if cid:
                    return cid
        except Exception as e:
            logger.error(f"读取 Chat ID 文件失败: {e}")
    return os.environ.get("TELEGRAM_CHAT_ID", None)

# ----------------- 3. 纪念日与丰富语库配置 -----------------
START_DATE = datetime(2026, 4, 1).date()

CAPSULES = [
    "📮 【时光胶囊 · 封存甜蜜】\n“致未来的我们：无论岁月怎么变，记得今天我们说好要一直手牵手的温度哦。”",
    "📮 【时光胶囊 · 延时惊喜】\n“解锁了一封来自过去的密信：『今天也要记得给对方一个大大的拥抱！』”",
    "📮 【时光胶囊 · 爱情凭证】\n“胶囊已开启！里面装满了我们相识以来的每一个闪光瞬间与欢笑。”",
    "📮 【时光胶囊 · 未来约定】\n“很久很久以后，当我们都变老了，还要像现在一样一起做无厘头的事情发呆。”",
    "📮 【时光胶囊 · 专属留言】\n“时空胶囊提示：你现在拥有的这个人，正在非常非常深地爱着你。”"
]

WATER_MESSAGES = [
    "🥤 咕噜咕噜~ 您的专属提醒官已上线！快喝一口水补补水分，今天也要保持水灵灵呀！",
    "💧 喝水时间到！小体质需要大水库，不喝水的小宝贝可是要被惩罚亲一口的哦~",
    "🍵 忙碌之余别忘了喝杯温水！多喝水皮肤好，照顾好自己才是最重要的事！",
    "🧃 滴！喝水卡！赶快拿起水杯喝三口，给身体补充能量！",
    "🥛 喝水提醒发送中... 水喝够了，心情也会跟着变甜哦！"
]

FOODS = [
    "🍲 沸腾香辣火锅", "烤 肉 🥩", "日料寿司🍣", "螺蛳粉/酸辣粉 🍜",
    "韩式炸鸡+奶茶 🍗🧋", "暖胃煲仔饭/靓汤 🍲", "酸菜鱼/水煮鱼 🐟",
    "深夜路边摊烧烤串串 🍢", "披萨/意大利面 🍕", "今天听宝的，想吃啥就吃啥！❤️"
]

PRIVILEGES = [
    "🎟 【无条件原谅券】x1\n凭此券，今天内任何不讲理的小脾气都必须被原谅！",
    "🍟 【深夜宵夜买单券】x1\n今晚想吃什么对方全额赞助，不得拒绝！",
    "💆 【专属按摩 10 分钟券】x1\n享受全套揉肩背按摩服务，随时召唤！",
    "🎬 【看什么电影听我的券】x1\n拥有绝对选择权，对方不许挑剔！",
    "👑 【一日听话卡】x1\n今天对方必须做你的小跟班，指东不往西！",
    "🍦 【奶茶自由券】x1\n今天可以无条件兑换一杯最爱的奶茶/甜品！"
]

PEACE_MESSAGES = [
    "🕊 【和平鸽送达】对方向你抛出了一只软绵绵的鸽子，并附带了一个委屈巴巴的求抱抱！❤",
    "🥺 系统检测到空气中有微量生气的成分，请立即使用【摸头杀】进行中和！",
    "🏳️ “我知道错啦/不生气了好不好，今晚请你吃大餐做补偿！”",
    "🧸 对方发来了一个“拉钩和解”邀请，请问是否点击确认？",
    "🍰 “生气的宝贝容易长痘痘哦，要不要来一口甜甜的吃掉不开心？”"
]

CHALLENGES = [
    "🎲 【心动任务】给对方按摩肩膀 3 分钟！",
    "🎲 【心动任务】看着对方的眼睛，深情地说出三个优点！",
    "🎲 【心动任务】拍一张现在的搞怪/可爱自拍发在群里！",
    "🎲 【心动任务】无条件答应对方一个小要求（不能拒绝哦）！",
    "🎲 【心动任务】给对方一个持续 10 秒钟的超级大拥抱！"
]

QUIZZES = [
    "🧠 【默契考验】对方最喜欢你身上的哪一个细节或习惯？",
    "🧠 【默契考验】如果只能带三样东西去无人岛，对方会带什么？",
    "🧠 【默契考验】两人第一次约会时，对方穿的是什么颜色的衣服？",
    "🧠 【默契考验】对方最讨厌吃的一种食物是什么？",
    "🧠 【默契考验】说出对方最近最想买或最念念不忘的一件东西！"
]

MEMORIES = [
    "📖 【专属回忆】2026年4月1日，我们的故事正式拉开了序幕...",
    "📖 【专属回忆】那些一起熬夜聊天、分享生活碎碎念的日子，每一刻都很珍贵。",
    "📖 【专属回忆】记得第一次互道晚安时的害羞与心动吗？",
    "📖 【专属回忆】只要和你在一起，连最平凡的烟火气都变得无比甜蜜。"
]

# ----------------- 4. 辅助功能函数 -----------------
def get_days_together():
    tz_cst = timezone(timedelta(hours=8))
    today = datetime.now(tz_cst).date()
    delta = (today - START_DATE).days + 1
    return max(1, delta)

def get_sweet_words():
    try:
        req = urllib.request.Request("https://api.vvhan.com/api/ian/qinghua", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                return response.read().decode('utf-8').strip()
    except Exception as e:
        logger.warning(f"获取情话 API 异常，自动回退本地库: {e}")

    fallbacks = [
        "希望每一个明天醒来，我都还能继续喜欢你多一点。",
        "遇见你之后，清风都变得温柔，连日子都开始散发着甜味。",
        "我的心不大，只装得下一个你。"
    ]
    return random.choice(fallbacks)

# ----------------- 5. 专属定时推送任务 -----------------
async def daily_morning_0520(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_chat_id()
    if chat_id:
        days = get_days_together()
        msg = f"老 Baby ❥\n每天对你的想和爱增加一点，最后就变成了：想你、爱你亿点点。（第 {days} 天）"
        await context.bot.send_message(chat_id=chat_id, text=msg)

async def daily_afternoon_1314(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_chat_id()
    if chat_id:
        days = get_days_together()
        msg = f"乘风破浪、御剑前行、万水千山只为寻你：ᰔᩚ 鸵 •鸟依人的老 Baby ❥（第 {days} 天）"
        await context.bot.send_message(chat_id=chat_id, text=msg)

async def daily_afternoon_1520(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_chat_id()
    if chat_id:
        days = get_days_together()
        msg = f"Ⓜ️𝒳🄿我做不到不闻不问，做不到一声不吭。我不想让时间冲淡一切，就让这个小小的空间，替我默默记录与见证（第 {days} 天）"
        await context.bot.send_message(chat_id=chat_id, text=msg)

# ----------------- 6. 对话框底部常驻菜单 (ReplyKeyboardMarkup) -----------------
def main_reply_keyboard():
    keyboard = [
        ["☀️ 早安", "🌙 晚安"],
        ["💋 亲亲", "❤️ 抱抱", "✨ 举高高"],
        ["我爱你", "📅 纪念日", "📜 甜言蜜语"],
        ["💧 提醒喝水", "🍚 今天吃什么"],
        ["🧠 默契考验", "🏺 专属回忆"],
        ["🎫 恋爱特权", "🕊️ 鸽子和解"],
        ["🎲 心动挑战", "📮 时光胶囊"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ----------------- 7. 机器人文本与指令响应逻辑 -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "爱心底部菜单已生成！定时告白服务已自动绑定当前聊天室！❤\n（请查看聊天框底部的按键）",
        reply_markup=main_reply_keyboard()
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        save_chat_id(update.effective_chat.id)

    if not update.message or not update.message.text:
        return
    text = update.message.text

    if "亲亲" in text:
        reply = "💋 给宝一个超大超响的亲亲！啪叽~"
    elif "抱抱" in text:
        reply = "❤️ 抱紧紧！今天也要一直被爱意包围哦~"
    elif "举高高" in text:
        reply = "✨ 嘿咻！把最心爱的宝高高举起~"
    elif "我爱你" in text:
        reply = "❥ 亿点点怎么够？我对你的爱是无限叠加、永不退场的！❤️❤️❤️"
    elif "纪念日" in text:
        days = get_days_together()
        reply = f"📅 今天是我们在一起的第 {days} 天啦！\n相爱起始于 2026 年 4 月 1 日，爱意每天都在持续递增中❤️"
    elif "甜言蜜语" in text or "情话" in text:
        reply = f"📜 【甜蜜情话】\n{get_sweet_words()}"
    elif "心动挑战" in text or "挑战" in text:
        reply = random.choice(CHALLENGES)
    elif "吃什么" in text:
        reply = f"🍚 【今天吃什么推荐】\n要不要试试：{random.choice(FOODS)}？"
    elif "特权" in text:
        reply = f"🎉 恭喜抽中恋爱特权卡！\n\n{random.choice(PRIVILEGES)}\n\n（记得截图存证，去向对方兑换哦！）"
    elif "鸽子" in text or "和解" in text:
        reply = random.choice(PEACE_MESSAGES)
    elif "默契" in text:
        reply = f"{random.choice(QUIZZES)}\n\n👉 两位请在群里同时打出答案，看谁答得最准！"
    elif "回忆" in text:
        reply = random.choice(MEMORIES)
    elif "胶囊" in text:
        reply = random.choice(CAPSULES)
    elif "喝水" in text:
        reply = random.choice(WATER_MESSAGES)
    elif "早安" in text:
        reply = "☀️ 早安，宝贝！新的一天也要快乐满满，记得按时吃早餐哦~"
    elif "晚安" in text:
        reply = "🌙 晚安，盖好被子！愿今晚的梦里全都是我们甜蜜的碎片~"
    else:
        return

    await update.message.reply_text(reply, reply_markup=main_reply_keyboard())

# ----------------- 8. 启动主程序 -----------------
def main():
    keep_alive()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("重大错误：未检测到 TELEGRAM_BOT_TOKEN 环境变量！程序即将退出。")
        return

    application = Application.builder().token(token).build()

    # 挂载定时任务
    job_queue = application.job_queue
    if job_queue:
        tz_cst = timezone(timedelta(hours=8))

        # 任务 1：每天 05:20
        job_queue.run_daily(daily_morning_0520, time=time(hour=5, minute=20, tzinfo=tz_cst))

        # 任务 2：每天 13:14
        job_queue.run_daily(daily_afternoon_1314, time=time(hour=13, minute=14, tzinfo=tz_cst))

        # 任务 3：每天 15:20
        job_queue.run_daily(daily_afternoon_1520, time=time(hour=15, minute=20, tzinfo=tz_cst))

        logger.info("每日定时告白任务（05:20, 13:14, 15:20）已成功挂载！")
    else:
        logger.warning("JobQueue 未能正常初始化，请检查是否安装了 APScheduler！")

    # 注册处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot Polling 轮询已启动，保活服务开启...")
    application.run_polling()

if __name__ == '__main__':
    main()
