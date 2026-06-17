import discord
from discord import app_commands
import psutil
import platform
import io
import subprocess
from datetime import datetime
from PIL import ImageGrab

# ======================
# CONFIG
# ======================
TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
AUTHORIZED_USER_ID = PUT_YOUR_USER_ID_HERE

# ======================
# BOT SETUP
# ======================
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


def is_authorized(user_id: int):
    return user_id == AUTHORIZED_USER_ID


@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")


# =========================================================
# 📊 SYSTEM GROUP
# =========================================================
system = app_commands.Group(name="system", description="System tools")
tree.add_command(system)


@system.command(name="performance", description="Show CPU, RAM, Disk usage")
async def performance(interaction: discord.Interaction):
    if not is_authorized(interaction.user.id):
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    cpu = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory()
    ram_used = ram.used / (1024 ** 3)
    ram_total = ram.total / (1024 ** 3)

    disk = psutil.disk_usage("/")
    disk_used = disk.used / (1024 ** 3)
    disk_total = disk.total / (1024 ** 3)

    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    msg = (
        f"📊 **System Performance**\n\n"
        f"🧠 CPU: {cpu}%\n"
        f"💾 RAM: {ram_used:.1f}/{ram_total:.1f} GB\n"
        f"🗄️ Disk: {disk_used:.1f}/{disk_total:.1f} GB\n"
        f"⏱️ Uptime: {str(uptime).split('.')[0]}\n"
        f"💻 OS: {platform.system()} {platform.release()}"
    )

    await interaction.response.send_message(msg)


@system.command(name="list", description="List running processes (no duplicates)")
async def list_processes(interaction: discord.Interaction):
    if interaction.user.id != AUTHORIZED_USER_ID:
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    seen = set()
    processes = []

    for p in psutil.process_iter(['pid', 'name']):
        try:
            name = p.info['name'] or "Unknown"
            pid = p.info['pid']

            # normalize name to avoid duplicate spam
            key = name.lower()

            if key not in seen:
                seen.add(key)
                processes.append(f"{pid} - {name}")

        except:
            pass

    processes.sort()

    output = "\n".join(processes)

    if len(output) > 1900:
        output = output[:1900] + "\n...truncated"

    await interaction.response.send_message(f"📋 **Processes (deduped):**\n```\n{output}\n```")# # =========================================================
# 🪟 APPS GROUP
# Controls launching and stopping local applications
# =========================================================

apps = app_commands.Group(name="apps", description="App control")
tree.add_command(apps)


def is_authorized(user_id: int) -> bool:
    return True  # keep your own logic


# =========================================================
# 🚀 START APP
# =========================================================
@apps.command(name="start", description="Start an application")
async def start_app(interaction: discord.Interaction, path: str):
    if not is_authorized(interaction.user.id):
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    await interaction.response.defer(ephemeral=False)

    try:
        subprocess.Popen(path, shell=True)
        await interaction.followup.send("🚀 App started")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed: {e}")


# =========================================================
# ❌ STOP APP (by name)
# =========================================================
@apps.command(name="stop", description="Stop an application by name")
async def stop_app(interaction: discord.Interaction, name: str):
    if not is_authorized(interaction.user.id):
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    await interaction.response.defer(ephemeral=False)

    name = name.lower()
    found = False

    try:
        for p in psutil.process_iter(['name']):
            proc_name = p.info['name']
            if proc_name and name in proc_name.lower():
                p.kill()
                found = True

        await interaction.followup.send(
            "🛑 App stopped" if found else "❌ No matching app found"
        )

    except Exception as e:
        await interaction.followup.send(f"❌ Failed: {e}")
# =========================================================
# 📸 TOOLS GROUP
# =========================================================
tools = app_commands.Group(name="tools", description="Utilities")
tree.add_command(tools)


@tools.command(name="screenshot", description="Take a screenshot")
async def screenshot(interaction: discord.Interaction):
    if not is_authorized(interaction.user.id):
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    img = ImageGrab.grab()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    file = discord.File(buffer, filename="screen.png")
    await interaction.response.send_message("📸 Screenshot:", file=file)


# =========================================================
# ⚡ POWER GROUP
# =========================================================
power = app_commands.Group(name="power", description="Power controls")
tree.add_command(power)


@power.command(name="shutdown", description="Shutdown PC (confirm required)")
async def shutdown(interaction: discord.Interaction, confirm: bool = False):
    if interaction.user.id != AUTHORIZED_USER_ID:
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    if not confirm:
        return await interaction.response.send_message("⚠️ Use confirm:true", ephemeral=True)

    await interaction.response.send_message("🔌 Shutting down...")
    subprocess.run("shutdown /s /t 0", shell=True)


@power.command(name="restart", description="Restart PC (confirm required)")
async def restart(interaction: discord.Interaction, confirm: bool = False):
    if interaction.user.id != AUTHORIZED_USER_ID:
        return await interaction.response.send_message("❌ Not allowed", ephemeral=True)

    if not confirm:
        return await interaction.response.send_message("⚠️ Use confirm:true", ephemeral=True)

    await interaction.response.send_message("🔄 Restarting...")
    subprocess.run("shutdown /r /t 0", shell=True)


# ======================
# RUN BOT
# ======================
bot.run(TOKEN)