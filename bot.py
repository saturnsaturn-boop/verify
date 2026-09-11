import os
import logging

import discord
from discord.ext import commands
from discord import app_commands


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Your verification role
VERIFY_ROLE_ID = 1543128981413568595

# Light green
EMBED_COLOR = discord.Color.from_rgb(144, 238, 144)

# Verification embed title
EMBED_TITLE = (
    "𝐕𝐄𝐑𝐈𝐅𝐘 𝐓𝐎 𝐆𝐀𝐈𝐍 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎 𝐑𝐄𝐒𝐓 𝐎𝐅 "
    "𝐓𝐇𝐄 𝐂𝐇𝐀𝐍𝐍𝐄𝐋𝐒 — ᨳଓ ."
)

# Verification embed description
EMBED_DESCRIPTION = "verify"

# Your verification image
IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1542776803867758602/1547851068602585159/"
    "2875db0a714b7ee9cb08f6d15765e123.jpg"
    "?ex=6aa4ec24&is=6aa39aa4&"
    "hm=afefd3310a432a04cff76dc592a2cb928806d9ff10b2e000b8706e88ad9b77cf&"
)

# Channels containing these words will be skipped
# by /setup verify.
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

logger = logging.getLogger("verify-bot")


# ============================================================
# DISCORD INTENTS
# ============================================================

intents = discord.Intents.default()

# Required for working with server members/roles.
intents.members = True

# Message Content Intent is NOT required.
# This bot uses slash commands.


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
# HELPER FUNCTIONS
# ============================================================

def is_staff_channel(channel):
    """
    Checks whether a channel/category looks like a staff channel.
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

    return embed


# ============================================================
# VERIFICATION BUTTON
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):

        # None = button never expires
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="♡",
        style=discord.ButtonStyle.success,
        custom_id="verify_button",
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # Make sure this is being used inside a server
        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This button can only be used inside a server.",
                ephemeral=True,
            )

            return

        # Find verification role
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

        # Give the role
        try:

            await member.add_roles(
                role,
                reason="Verified through verification panel",
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I can't give you the verification role.\n\n"
                "Make sure my bot role is ABOVE the verification role.",
                ephemeral=True,
            )

            return

        except discord.HTTPException as error:

            logger.error(
                "Failed to give verification role: %s",
                error,
            )

            await interaction.response.send_message(
                "❌ Discord returned an error. Please try again.",
                ephemeral=True,
            )

            return

        # Successful verification
        await interaction.response.send_message(
            "♡ You are now verified! You should have access to the server.",
            ephemeral=True,
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    # Register persistent verification button
    bot.add_view(
        VerifyView()
    )

    logger.info(
        "Bot is online as %s (%s)",
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

    # Make sure correct action was selected
    if action.value != "verify_panel":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    # ========================================================
    # RESPOND IMMEDIATELY
    # ========================================================
    # This prevents the "didn't respond in time" error.

    await interaction.response.send_message(
        f"⏳ Sending the verification panel to {channel.mention}...",
        ephemeral=True,
    )

    # ========================================================
    # SEND PANEL
    # ========================================================

    try:

        await channel.send(
            embed=build_verify_embed(),
            view=VerifyView(),
        )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                f"❌ I can't send the verification panel to "
                f"{channel.mention}.\n\n"
                "Make sure the bot has:\n"
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
            f"✅ Verification panel successfully sent to "
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

    # Respond immediately
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
    # FIND VERIFICATION ROLE
    # ========================================================

    role = guild.get_role(
        VERIFY_ROLE_ID
    )

    if role is None:

        await interaction.followup.send(
            f"❌ I couldn't find the verification role.\n\n"
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
            "❌ I couldn't find my bot member.",
            ephemeral=True,
        )

        return

    # ========================================================
    # ROLE HIERARCHY
    # ========================================================

    if role >= bot_member.top_role:

        await interaction.followup.send(
            "❌ **Role hierarchy problem!**\n\n"
            "Move the bot's role ABOVE the verification role.\n\n"
            "It needs to look like:\n\n"
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
    # CONFIGURE CATEGORIES
    # ========================================================

    for category in guild.categories:

        # Don't touch obvious staff categories
        if is_staff_channel(category):

            skipped += 1

            continue

        try:

            # Hide from @everyone
            await category.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            # Give verified users access
            await category.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed += 1

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "Cannot edit category: %s",
                category.name,
            )

        except discord.HTTPException:

            failed += 1

    # ========================================================
    # CONFIGURE CHANNELS
    # ========================================================

    for channel in guild.channels:

        # Skip categories because we already handled them
        if isinstance(
            channel,
            discord.CategoryChannel
        ):

            continue

        # Don't hide the channel where /setup was used
        if channel.id == interaction.channel_id:

            skipped += 1

            continue

        # Don't touch staff channels
        if is_staff_channel(channel):

            skipped += 1

            continue

        try:

            # Hide from unverified users
            await channel.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            # Give verified users access
            await channel.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed += 1

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "Cannot edit channel: %s",
                channel.name,
            )

        except discord.HTTPException:

            failed += 1

    # ========================================================
    # SETUP RESULT
    # ========================================================

    embed = discord.Embed(
        title="♡ Verification Setup Complete",
        color=EMBED_COLOR,
    )

    embed.description = (
        f"**Verification role:** {role.mention}\n\n"
        f"✅ **Changed:** `{changed}`\n"
        f"⏭️ **Skipped:** `{skipped}`\n"
        f"❌ **Failed:** `{failed}`"
    )

    if failed > 0:

        embed.add_field(
            name="⚠️ Some channels could not be changed",
            value=(
                "Make sure the bot has **Manage Channels** "
                "permission."
            ),
            inline=False,
        )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True,
    )


# ============================================================
# ERROR HANDLING
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
                "❌ Something went wrong.",
                ephemeral=True,
            )


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
                "❌ Something went wrong.",
                ephemeral=True,
            )


# ============================================================
# START BOT
# ============================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
