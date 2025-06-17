import discord
from discord.ext import commands
import threading
import time
import re
import requests
import os
import random
import json

TOKEN = input("Nhập token bot Discord: ")
ADMIN_ID = int(input("Nhập ID admin (số): "))

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='@', intents=intents)

allowed_users = set()
treo_threads = {}
treo_start_times = {}
messenger_instances = {}
nhay_threads = {}
nhay_start_times = {}
chui_threads = {}
chui_start_times = {}
codelag_threads = {}
codelag_start_times = {}

UA_KIWI = [
    "Mozilla/5.0 (Linux; Android 11; RMX2185)...",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11)..."
]
UA_VIA = [
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 8)...",
    "Mozilla/5.0 (Linux; Android 11; V2109)..."
]
USER_AGENTS = UA_KIWI + UA_VIA

class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.user_agent = random.choice(USER_AGENTS)
        self.fb_dtsg = None
        self.init_params()

    def id_user(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': self.user_agent
        }
        try:
            response = requests.get('https://mbasic.facebook.com', headers=headers)
            fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
            if fb_dtsg_match:
                self.fb_dtsg = fb_dtsg_match.group(1)
            else:
                raise Exception("Không lấy được fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khi khởi tạo tham số: {str(e)}")

    def gui_tn(self, recipient_id, message, max_retries=10):
        for _ in range(max_retries):
            timestamp = int(time.time() * 1000)
            message_id = str(timestamp)
            data = {
                'thread_fbid': recipient_id,
                'action_type': 'ma-type:user-generated-message',
                'body': message,
                'client': 'mercury',
                'author': f'fbid:{self.user_id}',
                'timestamp': timestamp,
                'offline_threading_id': message_id,
                'message_id': message_id,
                'ephemeral_ttl_mode': '',
                '__user': self.user_id,
                '__a': '1',
                '__req': '1b',
                '__rev': '1015919737',
                'fb_dtsg': self.fb_dtsg
            }
            headers = {
                'Cookie': self.cookie,
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f'https://www.facebook.com/messages/t/{recipient_id}'
            }
            try:
                res = requests.post('https://www.facebook.com/messaging/send/', data=data, headers=headers)
                if res.status_code == 200:
                    return True
            except:
                pass
        return False

def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d} ngày")
    if h: parts.append(f"{h} giờ")
    if m: parts.append(f"{m} phút")
    if s or not parts: parts.append(f"{s} giây")
    return " ".join(parts)

def start_spam(user_id, idbox, cookie, message, delay):
    try:
        messenger = Messenger(cookie)
    except Exception as e:
        return f"Lỗi cookie: {str(e)}"

    def loop_send():
        while (user_id, idbox) in treo_threads:
            ok = messenger.gui_tn(idbox, message)
            print("Thành công" if ok else "Thất bại")
            time.sleep(delay)

    key = (user_id, idbox)
    thread = threading.Thread(target=loop_send)
    treo_threads[key] = thread
    treo_start_times[key] = time.time()
    messenger_instances[key] = messenger
    thread.start()
    return "Đã bắt đầu spam treo."

@bot.command()
async def set(ctx):
    if ctx.author.id != ADMIN_ID and ctx.author.id not in allowed_users:
        return await ctx.send("Bạn không có quyền dùng bot.")
    if not ctx.message.attachments:
        return await ctx.send("Gửi kèm file .txt.")
    file = ctx.message.attachments[0]
    if not file.filename.endswith(".txt"):
        return await ctx.send("Chỉ hỗ trợ file .txt")
    path = f"{ctx.author.id}_{file.filename}"
    await file.save(path)
    await ctx.send(f"Đã lưu file `{path}`.")

@bot.command()
async def treo(ctx, idbox: str, cookie: str, filename: str, delay: int):
    if ctx.author.id != ADMIN_ID and ctx.author.id not in allowed_users:
        return await ctx.send("Bạn không có quyền dùng bot.")
    path = f"{ctx.author.id}_{filename}"
    if not os.path.exists(path):
        return await ctx.send("Không thấy file.")
    with open(path, "r", encoding="utf-8") as f:
        message = f.read()
    result = start_spam(ctx.author.id, idbox, cookie, message, delay)
    await ctx.send(result)

@bot.command()
async def stoptreo(ctx, idbox: str):
    key = (ctx.author.id, idbox)
    if key in treo_threads:
        treo_threads.pop(key)
        treo_start_times.pop(key)
        messenger_instances.pop(key)
        await ctx.send(f"Đã dừng spam treo {idbox}.")
    else:
        await ctx.send("Không tìm thấy tab treo.")

@bot.command()
async def tabtreo(ctx):
    msg = "**Tab Treo đang chạy:**\n"
    count = 0
    for (uid, ib), start in treo_start_times.items():
        if uid == ctx.author.id:
            uptime = format_duration(time.time() - start)
            msg += f"• {ib}: {uptime}\n"
            count += 1
    if count == 0:
        msg = "Không có tab treo nào."
    await ctx.send(msg)

@bot.command()
async def add(ctx, iduser: int):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("Chỉ admin được thêm user.")
    allowed_users.add(iduser)
    await ctx.send(f"Đã thêm {iduser}.")

@bot.command()
async def xoa(ctx, iduser: int):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("Chỉ admin được xoá user.")
    allowed_users.discard(iduser)
    await ctx.send(f"Đã xoá {iduser}.")
@bot.command()
async def menu(ctx):
    await ctx.send(
        "**╔═══════『 MENU BOT BY DNK  』═══════╗**\n\n"
        "🔹 **1. @set** - Đính kèm file txt.\n"
        "🔹 **2. @treo** `idbox \"cookie\" file.txt delay` - Treo\n"
        "🔹 **3. @stoptreo** `idbox` - Dừng tab treo với idbox\n"
        "🔹 **4. @tabtreo** - Hiển thị các tab treo\n"
        "🔹 **5. @nhay** `idbox \"cookie\" delay` - Nhây\n"
        "🔹 **6. @stopnhay** `idbox` - Dừng tab nhây với idbox\n"
        "🔹 **7. @tabnhay** - Hiển thị các tab nhây\n"
        "🔹 **8. @chui** `idbox \"cookie\" delay` - Chửi đổng\n"
        "🔹 **9. @stopchui** `idbox` - Dừng tab với idbox\n"
        "🔹 **10. @tabchui** - Hiển thị các tab\n"
        "🔹 **11. @codelag** `idbox \"cookie\" delay` - Spam code lag\n"
        "🔹 **12. @stopcodelag** `idbox` - Dừng tab code lag với idbox\n"
        "🔹 **13. @tabcodelag** - Hiển thị các tab\n"
        "🔹 **14. @add** `iduser` - Thêm người dùng vào bot (admin).\n"
        "🔹 **15. @xoa** `iduser` - Xóa người dùng khỏi bot (admin).\n"
        "🔹 **16. @menu** - Hiển thị danh sách lệnh hiện tại.\n\n"
        "**📌Admin & Support: Ngọc Khánh**\n"
        "`Zalo hỗ trợ: 0878569480`\n"
        "**╚══════════════════════════╝**"
    )
bot.run(TOKEN)