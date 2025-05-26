import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta, timezone

intents = discord.Intents.all()

TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "*")

GUILD_PREFIXES = {}
COMMAND_PERMISSIONS = {}

def get_prefix(bot, message):
    return GUILD_PREFIXES.get(str(message.guild.id), DEFAULT_PREFIX)

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

def is_mod():
    async def predicate(ctx):
        roles = [r.name for r in ctx.author.roles]
        return "〘MOD〙" in roles or "〘ADMIN〙" in roles
    return commands.check(predicate)

def is_allowed(command_name):
    async def predicate(ctx):
        perms = COMMAND_PERMISSIONS.get(str(ctx.guild.id), {}).get(command_name, [])
        return ctx.author.id in perms or any(role.id in perms for role in ctx.author.roles)
    return commands.check(predicate)

# Regex xóa link invite
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if re.search(r"(discord\.gg|discord\.com/invite)/[a-zA-Z0-9]+", message.content):
        roles = [r.name for r in message.author.roles]
        if "〘MOD〙" not in roles and "〘ADMIN〙" not in roles:
            try:
                await message.author.send("gửi link cái địt cụ mày")
                await message.delete()
                await message.guild.ban(message.author, reason="Gửi link invite Discord")
            except discord.Forbidden:
                pass

    await bot.process_commands(message)

# Lỗi
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("sai lệnh rồi thằng ngu")
    else:
        await ctx.send(f"Lỗi rồi: {type(error).__name__}: {error}")

@bot.command()
async def key(ctx):
    await ctx.send("Link lấy key của bạn nè : https://link4sub.com/CAvb")

@bot.command()
async def shop(ctx):
    await ctx.send("Link shop mua KEY VIP nè : https://hackgamevip.com/")

@bot.command(name="hackgamevipprefix", with_app_command=False)
@is_mod()
async def change_prefix(ctx, new_prefix):
    GUILD_PREFIXES[str(ctx.guild.id)] = new_prefix
    await ctx.send(f"✅ Đổi prefix thành công! Bây giờ dùng {new_prefix} để gọi bot.")

@bot.command()
@is_mod()
async def chopheplenh(ctx, command: str, target: discord.Member | discord.Role):
    gid = str(ctx.guild.id)
    if gid not in COMMAND_PERMISSIONS:
        COMMAND_PERMISSIONS[gid] = {}
    if command not in COMMAND_PERMISSIONS[gid]:
        COMMAND_PERMISSIONS[gid][command] = []
    COMMAND_PERMISSIONS[gid][command].append(target.id)
    await ctx.send(f"✅ {target} được phép dùng lệnh {command}.")

@bot.command()
async def help(ctx):
    roles = [r.name for r in ctx.author.roles]
    is_admin_or_mod = "〘MOD〙" in roles or "〘ADMIN〙" in roles
    prefix = GUILD_PREFIXES.get(str(ctx.guild.id), DEFAULT_PREFIX)

    embed = discord.Embed(title="📜 Danh sách lệnh", color=discord.Color.blue())
    embed.add_field(name=f"{prefix}key", value="Nhận link lấy key", inline=False)
    embed.add_field(name=f"{prefix}shop", value="Link đến shop mua key VIP", inline=False)

    if is_admin_or_mod:
        embed.add_field(name=f"{prefix}hackgamevipprefix [prefix mới]", value="Đổi prefix của bot", inline=False)
        embed.add_field(name=f"{prefix}chopheplenh [lệnh] [@member/@role]", value="Cho phép dùng lệnh", inline=False)
        embed.add_field(name=f"{prefix}khoamom [@user] [thời gian] [lý do]", value="Khoá mõm ai đó", inline=False)
        embed.add_field(name=f"{prefix}mokhoamom [@user]", value="Mở mõm ai đó", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="khoamom")
@is_mod()
async def timeout(ctx, member: discord.Member, duration: str = "1m", *, reason="Không có lý do"):
    seconds = parse_duration(duration)
    until_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    try:
        await member.timeout(until_time, reason=reason)
        await ctx.send(f"🔇 Khoá mõm {member.mention} vì {reason} trong {duration}.")
    except discord.Forbidden:
        await ctx.send("❌ Không thể khoá mõm người này.")
    except Exception as e:
        await ctx.send(f"Lỗi: {type(e).__name__}: {e}")

@bot.command(name="mokhoamom")
@is_mod()
async def remove_timeout(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Đã mở mõm cho {member.mention}.")
    except discord.Forbidden:
        await ctx.send("❌ Không thể mở mõm người này.")

def parse_duration(duration):
    match = re.match(r"(\d+)([smhd])", duration.lower())
    if not match:
        return 60
    num, unit = match.groups()
    return int(num) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]

bot.run(TOKEN)