import os
import logging
import discord
from discord.ext import commands
from discord import app_commands


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Verification role ID
VERIFY_ROLE_ID = 1543128981413568595

# Light green embed
EMBED_COLOR = discord.Color.from_rgb(144, 238, 144)

# Clean bold title
EMBED_TITLE = (
    "𝐕𝐄𝐑𝐈𝐅𝐘 𝐓𝐎 𝐆𝐀𝐈𝐍 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎 𝐑𝐄𝐒𝐓 𝐎𝐅 "
    "𝐓𝐇𝐄 𝐂𝐇𝐀𝐍𝐍𝐄𝐋𝐒 — ᨳଓ ."
)

# Embed description
EMBED_DESCRIPTION = "verify"

# Your image
IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1542776803867758602/1547851068602585159/"
    "2875db0a714b7ee9cb08f6d15765e123.jpg"
    "?ex=6aa4ec24&is=6aa39aa4&"
    "hm=afefd3310a432a04cff76dc592a2cb928806d9ff10b2e000b8706e88ad9b77cf&"
)

# These channels/categories are skipped by setup
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
# INTENTS
# ============================================================

intents = discord.Intents.default()

# Needed for members/roles
intents.members = True

# Message Content Intent is NOT required.


# ============================================================
# BOT
# ============================================================

class VerifyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):

        await self.tree.sync()

        logger.info("Slash commands synced.")


bot = VerifyBot()


# ============================================================
# HELPERS
# ============================================================

def is_staff_channel(channel):
    """
    Returns True if the channel/category name looks like
    a staff/admin/mod channel.
    """

    name = channel.name.lower()

    return any(
        keyword in name
        for keyword in STAFF_KEYWORDS
    )


def build_verify_embed():

    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR,
    )

    embed.set_image(
        url=IMAGE_URL
    )

    return embed


# ============================================================
# VERIFICATION BUTTON
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):

        # Never expires
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="♡",
        style=discord.ButtonStyle.success,
        custom_id="verification_button",
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # Make sure this is a server
        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This button can only be used in a server.",
                ephemeral=True,
            )

            return

        # Get verification role
        role = interaction.guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ I couldn't find the verification role.",
                ephemeral=True,
            )

            return

        member = interaction.user

        # Already verified
        if role in member.roles:

            await interaction.response.send_message(
                "♡ You are already verified!",
                ephemeral=True,
            )

            return

        # Give verification role
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
                "Error giving verification role: %s",
                error,
            )

            await interaction.response.send_message(
                "❌ Discord returned an error. Please try again.",
                ephemeral=True,
            )

            return

        # Success
        await interaction.response.send_message(
            "♡ You are now verified! You should now have access to the channels.",
            ephemeral=True,
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    # Register persistent button
    bot.add_view(
        VerifyView()
    )

    logger.info(
        "Bot online as %s (%s)",
        bot.user,
        bot.user.id,
    )


# ============================================================
# /SEND VERIFY PANEL
# ============================================================

@bot.tree.command(
    name="send",
    description="Send a verification panel.",
)
@app_commands.describe(
    action="What do you want to send?",
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

    # Check action
    if action.value != "verify_panel":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    # Respond immediately
    await interaction.response.send_message(
        f"⏳ Sending verification panel to {channel.mention}...",
        ephemeral=True,
    )

    # Send panel
    try:

        await channel.send(
            embed=build_verify_embed(),
            view=VerifyView(),
        )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                f"❌ I can't send messages in {channel.mention}.\n\n"
                "Make sure I have:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Embed Links"
            )
        )

        return

    except discord.HTTPException as error:

        logger.error(
            "Failed to send verification panel: %s",
            error,
        )

        await interaction.edit_original_response(
            content=(
                "❌ Discord returned an error while sending the panel."
            )
        )

        return

    # Success
    await interaction.edit_original_response(
        content=(
            f"✅ Verification panel sent to {channel.mention}! ♡"
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
    action="What do you want to set up?",
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

    if action.value != "verify":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    # Respond before doing permission changes
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
    # FIND ROLE
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
    # FIND BOT
    # ========================================================

    bot_member = guild.me

    if bot_member is None:

        await interaction.followup.send(
            "❌ I couldn't find the bot in this server.",
            ephemeral=True,
        )

        return

    # ========================================================
    # ROLE POSITION
    # ========================================================

    if role >= bot_member.top_role:

        await interaction.followup.send(
            "❌ **Role hierarchy problem!**\n\n"
            "Move the bot's role ABOVE the verification role.\n\n"
            "It should look like:\n\n"
            "🤖 Bot Role\n"
            "✅ Verification Role\n"
            "👤 @everyone",
            ephemeral=True,
        )

        return

    everyone = guild.default_role

    changed = 0
    skipped = 0
    failed = 0

    # ========================================================
    # CATEGORIES
    # ========================================================

    for category in guild.categories:

        # Skip staff categories
        if is_staff_channel(category):

            skipped += 1
            continue

        try:

            # Hide category from @everyone
            await category.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification setup",
            )

            # Allow verification role
            await category.set_permissions(
                role,
                view_channel=True,
                reason="Verification setup",
            )

            changed += 1

            logger.info(
                "Configured category: %s",
                category.name,
            )

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "No permission to edit category: %s",
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
    # CHANNELS
    # ========================================================

    for channel in guild.channels:

        # Categories already handled
        if isinstance(
            channel,
            discord.CategoryChannel
        ):

            continue

        # Don't hide the channel where /setup was used
        if channel.id == interaction.channel_id:

            skipped += 1
            continue

        # Skip staff channels
        if is_staff_channel(channel):

            skipped += 1
            continue

        try:

            # ------------------------------------------------
            # @EVERYONE
            # ------------------------------------------------

            everyone_overwrite = (
                channel.overwrites_for(everyone)
            )

            everyone_overwrite.view_channel = False

            await channel.set_permissions(
                everyone,
                overwrite=everyone_overwrite,
                reason="Verification setup - hide unverified",
            )

            # ------------------------------------------------
            # VERIFICATION ROLE
            # ------------------------------------------------

            verify_overwrite = (
                channel.overwrites_for(role)
            )

            verify_overwrite.view_channel = True

            await channel.set_permissions(
                role,
                overwrite=verify_overwrite,
                reason="Verification setup - allow verified",
            )

            changed += 1

            logger.info(
                "Configured channel: #%s",
                channel.name,
            )

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "No permission to edit channel: %s",
                channel.name,
            )

        except discord.HTTPException as error:

            failed += 1

            logger.warning(
                "Discord error editing #%s: %s",
                channel.name,
                error,
            )

    # ========================================================
    # RESULT
    # ========================================================

    embed = discord.Embed(
        title="♡ Verification Setup Complete",
        color=EMBED_COLOR,
    )

    embed.description = (
        "The verification permissions have been configured.\n\n"
        f"✅ **Changed:** `{changed}`\n"
        f"⏭️ **Skipped:** `{skipped}`\n"
        f"❌ **Failed:** `{failed}`\n\n"
        f"**Verification role:** {role.mention}"
    )

    if failed > 0:

        embed.add_field(
            name="⚠️ Some channels failed",
            value=(
                "Make sure the bot has **Administrator** permission "
                "or at least **Manage Channels**."
            ),
            inline=False,
        )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# SEND ERROR
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

    else:

        logger.error(
            "Send command error: %s",
            error,
        )

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ Something went wrong while running /send.",
                ephemeral=True,
            )


# ============================================================
# SETUP ERROR
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

    else:

        logger.error(
            "Setup command error: %s",
            error,
        )

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ Something went wrong while running /setup.",
                ephemeral=True,
            )


# ============================================================
# START
# ============================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
