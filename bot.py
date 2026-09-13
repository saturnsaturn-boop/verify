import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
from discord import app_commands


# ============================================================
# CONFIGURATION
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Your verification role
VERIFY_ROLE_ID = 1543128981413568595

# Embed color
EMBED_COLOR = discord.Color.from_rgb(255, 255, 255)

# Verification panel title
EMBED_TITLE = (
    "𝐕𝐄𝐑𝐈𝐅𝐘 𝐓𝐎 𝐆𝐀𝐈𝐍 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎 𝐑𝐄𝐒𝐓 𝐎𝐅 "
    "𝐓𝐇𝐄 𝐂𝐇𝐀𝐍𝐍𝐄𝐋𝐒 — ᨳଓ ."
)

# Verification panel description
EMBED_DESCRIPTION = "verify"

# Your verification image
IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1542776803867758602/"
    "1548570076016414803/76aeab5311fc9f53643499877bf82b3b.jpg"
    "?ex=6aa789c5&is=6aa63845&hm=f2c5e20ba571a1a45efe383814ec3a2da1447d967b067ce6bde8b70a77794c48&"
)

# Verification embed footer
EMBED_FOOTER = "♡ verification system"


# ============================================================
# CHANNELS THAT SHOULD NOT BE LOCKED
# ============================================================

STAFF_KEYWORDS = (
    "staff",
    "admin",
    "administrator",
    "mod",
    "moderator",
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("verification-bot")


# ============================================================
# DISCORD INTENTS
# ============================================================

intents = discord.Intents.default()

# Needed for working with members and roles.
intents.members = True

# Message Content Intent is NOT needed.


# ============================================================
# BOT CLASS
# ============================================================

class VerifyBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):

        # Register the persistent verification buttons.
        self.add_view(
            VerifyView()
        )

        # Sync slash commands.
        await self.tree.sync()

        logger.info("Slash commands synced.")


bot = VerifyBot()


# ============================================================
# HELPERS
# ============================================================

def is_staff_channel(channel):
    """
    Checks if a channel/category looks like a staff area.
    """

    name = channel.name.lower()

    return any(
        keyword in name
        for keyword in STAFF_KEYWORDS
    )


def build_verify_embed():
    """
    Creates the verification embed.
    """

    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR,
    )

    embed.set_image(
        url=IMAGE_URL
    )

    embed.set_footer(
        text=EMBED_FOOTER
    )

    return embed


# ============================================================
# VERIFICATION BUTTONS
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):

        # None means the buttons never expire.
        super().__init__(
            timeout=None
        )

    # ========================================================
    # VERIFY BUTTON
    # ========================================================

    @discord.ui.button(
        label="♡",
        style=discord.ButtonStyle.success,
        custom_id="verification_button",
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # Must be used inside a server.
        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This button can only be used inside a server.",
                ephemeral=True,
            )

            return

        guild = interaction.guild

        # Find verification role.
        role = guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ I couldn't find the verification role.",
                ephemeral=True,
            )

            return

        member = interaction.user

        # Make sure we have a Member object.
        if not isinstance(member, discord.Member):

            await interaction.response.send_message(
                "❌ I couldn't find your server member information.",
                ephemeral=True,
            )

            return

        # Already verified.
        if role in member.roles:

            await interaction.response.send_message(
                "You are already verified ♡!",
                ephemeral=True,
            )

            return

        # ====================================================
        # GIVE ROLE
        # ====================================================

        try:

            await member.add_roles(
                role,
                reason="User verified through verification panel",
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I can't give you the verification role.\n\n"
                "Make sure the bot's role is ABOVE the verification role.",
                ephemeral=True,
            )

            return

        except discord.HTTPException as error:

            logger.error(
                "Failed to give verification role: %s",
                error,
            )

            await interaction.response.send_message(
                "❌ Discord returned an error while giving you the role.",
                ephemeral=True,
            )

            return

        # ====================================================
        # SUCCESS
        # ====================================================

        await interaction.response.send_message(
            "♡ **Verified!** You now have access to the server channels.",
            ephemeral=True,
        )

    # ========================================================
    # VERIFICATION COUNT BUTTON
    # ========================================================

    @discord.ui.button(
        label="How many people are verified?",
        style=discord.ButtonStyle.secondary,
        custom_id="verification_count_button",
    )
    async def verification_count_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # Must be used inside a server.
        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This button can only be used inside a server.",
                ephemeral=True,
            )

            return

        guild = interaction.guild

        # Find verification role.
        role = guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ I couldn't find the verification role.",
                ephemeral=True,
            )

            return

        # Count members who have the verification role.
        verified_count = len(role.members)

        await interaction.response.send_message(
            f"There are currently **{verified_count}** verified "
            f"in **{guild.name}** ♡",
            ephemeral=True,
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    logger.info(
        "Bot is online as %s (%s)",
        bot.user,
        bot.user.id,
    )


# ============================================================
# /SEND
# ============================================================

@bot.tree.command(
    name="send",
    description="Send a verification panel.",
)
@app_commands.describe(
    action="Choose what to send.",
    channel="Choose the channel for the verification panel.",
)
@app_commands.choices(
    action=[
        app_commands.Choice(
            name="verify panel",
            value="verify_panel",
        ),
    ]
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def send(
    interaction: discord.Interaction,
    action: app_commands.Choice[str],
    channel: discord.TextChannel,
):

    # ========================================================
    # CHECK ACTION
    # ========================================================

    if action.value != "verify_panel":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    # ========================================================
    # RESPOND IMMEDIATELY
    # ========================================================

    await interaction.response.send_message(
        f"⏳ Setting up {channel.mention}...",
        ephemeral=True,
    )

    # ========================================================
    # MAKE PANEL CHANNEL VISIBLE
    # ========================================================

    try:

        if interaction.guild is not None:

            guild = interaction.guild

            everyone = guild.default_role

            role = guild.get_role(
                VERIFY_ROLE_ID
            )

            # Allow everyone to see the verification channel.
            everyone_overwrite = (
                channel.overwrites_for(everyone)
            )

            everyone_overwrite.view_channel = True

            await channel.set_permissions(
                everyone,
                overwrite=everyone_overwrite,
                reason="Verification panel channel",
            )

            # Also allow the verification role.
            if role is not None:

                role_overwrite = (
                    channel.overwrites_for(role)
                )

                role_overwrite.view_channel = True

                await channel.set_permissions(
                    role,
                    overwrite=role_overwrite,
                    reason="Verification panel channel",
                )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                "❌ I don't have permission to change the "
                "permissions of that channel.\n\n"
                "Give the bot **Administrator** permission."
            )
        )

        return

    except discord.HTTPException as error:

        logger.error(
            "Failed setting panel channel permissions: %s",
            error,
        )

        await interaction.edit_original_response(
            content=(
                "❌ Discord returned an error while configuring "
                "the verification channel."
            )
        )

        return

    # ========================================================
    # SEND VERIFICATION PANEL
    # ========================================================

    try:

        await channel.send(
            embed=build_verify_embed(),
            view=VerifyView(),
        )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                f"❌ I can't send the panel to {channel.mention}.\n\n"
                "Make sure the bot has:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Embed Links"
            )
        )

        return

    except discord.HTTPException as error:

        logger.error(
            "Failed to send panel: %s",
            error,
        )

        await interaction.edit_original_response(
            content=(
                "❌ Discord returned an error while sending "
                "the verification panel."
            )
        )

        return

    # ========================================================
    # SUCCESS
    # ========================================================

    await interaction.edit_original_response(
        content=(
            f"✅ Verification panel sent to "
            f"{channel.mention}! ♡"
        )
    )


# ============================================================
# /SETUP VERIFY
# ============================================================

@bot.tree.command(
    name="setup",
    description="Set up the verification system.",
)
@app_commands.describe(
    action="Choose what to set up.",
)
@app_commands.choices(
    action=[
        app_commands.Choice(
            name="verify",
            value="verify",
        ),
    ]
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def setup(
    interaction: discord.Interaction,
    action: app_commands.Choice[str],
):

    # ========================================================
    # CHECK ACTION
    # ========================================================

    if action.value != "verify":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    # ========================================================
    # RESPOND IMMEDIATELY
    # ========================================================

    await interaction.response.defer(
        ephemeral=True
    )

    guild = interaction.guild

    if guild is None:

        await interaction.followup.send(
            "❌ This command must be used inside a server.",
            ephemeral=True,
        )

        return

    # ========================================================
    # GET VERIFICATION ROLE
    # ========================================================

    role = guild.get_role(
        VERIFY_ROLE_ID
    )

    if role is None:

        await interaction.followup.send(
            "❌ I couldn't find the verification role.\n\n"
            f"Role ID: `{VERIFY_ROLE_ID}`",
            ephemeral=True,
        )

        return

    # ========================================================
    # GET BOT MEMBER
    # ========================================================

    bot_member = guild.me

    if bot_member is None:

        await interaction.followup.send(
            "❌ I couldn't find the bot in this server.",
            ephemeral=True,
        )

        return

    # ========================================================
    # CHECK ROLE HIERARCHY
    # ========================================================

    if role >= bot_member.top_role:

        await interaction.followup.send(
            "❌ **Role hierarchy problem!**\n\n"
            "Move the bot's role ABOVE the verification role.\n\n"
            "It needs to look like this:\n\n"
            "🤖 **Bot Role**\n"
            "────────────\n"
            "✅ **Verification Role**\n"
            "────────────\n"
            "👤 **@everyone**",
            ephemeral=True,
        )

        return

    everyone = guild.default_role

    changed = 0
    skipped = 0
    failed = 0

    # ========================================================
    # CONFIGURE CATEGORIES
    # ========================================================

    for category in guild.categories:

        # Skip staff categories.
        if is_staff_channel(category):

            skipped += 1
            continue

        try:

            # Hide category from everyone.
            await category.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            # Allow verified role.
            await category.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed += 1

            logger.info(
                "Configured category: %s",
                category.name,
            )

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "Cannot edit category: %s",
                category.name,
            )

        except discord.HTTPException as error:

            failed += 1

            logger.warning(
                "Discord error editing category %s: %s",
                category.name,
                error,
            )

    # ========================================================
    # CONFIGURE CHANNELS
    # ========================================================

    for channel in guild.channels:

        # Categories were already handled.
        if isinstance(
            channel,
            discord.CategoryChannel
        ):

            continue

        # Keep the channel where setup was run accessible.
        if channel.id == interaction.channel_id:

            skipped += 1
            continue

        # Skip staff/admin/mod channels.
        if is_staff_channel(channel):

            skipped += 1
            continue

        try:

            # =================================================
            # HIDE FROM @EVERYONE
            # =================================================

            everyone_overwrite = (
                channel.overwrites_for(everyone)
            )

            everyone_overwrite.view_channel = False

            await channel.set_permissions(
                everyone,
                overwrite=everyone_overwrite,
                reason="Verification system - hide unverified",
            )

            # =================================================
            # ALLOW VERIFICATION ROLE
            # =================================================

            role_overwrite = (
                channel.overwrites_for(role)
            )

            role_overwrite.view_channel = True

            await channel.set_permissions(
                role,
                overwrite=role_overwrite,
                reason="Verification system - allow verified",
            )

            changed += 1

            logger.info(
                "Configured channel: #%s",
                channel.name,
            )

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "Cannot edit channel: %s",
                channel.name,
            )

        except discord.HTTPException as error:

            failed += 1

            logger.warning(
                "Discord error editing channel %s: %s",
                channel.name,
                error,
            )

    # ========================================================
    # RESULT
    # ========================================================

    result = discord.Embed(
        title="♡ Verification Setup Complete",
        color=EMBED_COLOR,
    )

    result.description = (
        "The verification permissions have been configured.\n\n"
        f"✅ **Changed:** `{changed}`\n"
        f"⏭️ **Skipped:** `{skipped}`\n"
        f"❌ **Failed:** `{failed}`\n\n"
        f"**Verification role:** {role.mention}"
    )

    if failed > 0:

        result.add_field(
            name="⚠️ Some channels failed",
            value=(
                "Make sure the bot has **Administrator** permission "
                "or at least **Manage Channels**."
            ),
            inline=False,
        )

    await interaction.followup.send(
        embed=result,
        ephemeral=True,
    )


# ============================================================
# /SEND ERROR HANDLER
# ============================================================

@send.error
async def send_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ You need Administrator permission to use this command.",
                ephemeral=True,
            )

        return

    logger.error(
        "Send command error: %s",
        error,
    )

    if not interaction.response.is_done():

        await interaction.response.send_message(
            "❌ Something went wrong while running `/send`.",
            ephemeral=True,
        )


# ============================================================
# /SETUP ERROR HANDLER
# ============================================================

@setup.error
async def setup_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ You need Administrator permission to use this command.",
                ephemeral=True,
            )

        return

    logger.error(
        "Setup command error: %s",
        error,
    )

    if not interaction.response.is_done():

        await interaction.response.send_message(
            "❌ Something went wrong while running `/setup verify`.",
            ephemeral=True,
        )


# ============================================================
# RENDER KEEP-ALIVE WEB SERVER
# ============================================================

class KeepAliveHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain",
        )

        self.end_headers()

        self.wfile.write(
            b"Verification bot is online!"
        )

    def do_HEAD(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain",
        )

        self.end_headers()

    def log_message(
        self,
        format,
        *args,
    ):

        # Don't spam Render logs.
        pass


def start_keep_alive():

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    server = HTTPServer(
        (
            "0.0.0.0",
            port,
        ),
        KeepAliveHandler,
    )

    logger.info(
        "Keep-alive web server running on port %s",
        port,
    )

    server.serve_forever()


# ============================================================
# START KEEP-ALIVE
# ============================================================

keep_alive_thread = threading.Thread(
    target=start_keep_alive,
    daemon=True,
)

keep_alive_thread.start()


# ============================================================
# START DISCORD BOT
# ============================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing. "
        "Add DISCORD_TOKEN to your Render environment variables."
    )


bot.run(TOKEN)
