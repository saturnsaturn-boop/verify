import os
import logging

import discord
from discord.ext import commands
from discord import app_commands


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

VERIFY_ROLE_ID = 1543128981413568595

EMBED_COLOR = discord.Color.from_rgb(144, 238, 144)

EMBED_TITLE = (
    "🇻​🇪​🇷​🇮​🇫​🇾​ 🇹​🇴​ 🇬​🇦​🇮​🇳​ 🇦​🇨​🇨​🇪​🇸​ 🇹​🇴​ 🇷​🇪​🇸​🇹​ "
    "🇴​🇫​ 🇹​🇭​🇪​ 🇨​🇭​🇦​🇳​🇳​🇪​🇱​🇸​ — ᨳଓ ."
)

EMBED_DESCRIPTION = "verify"

IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1542776803867758602/1547851068602585159/"
    "2875db0a714b7ee9cb08f6d15765e123.jpg"
    "?ex=6aa4ec24&is=6aa39aa4&"
    "hm=afefd3310a432a04cff76dc592a2cb928806d9ff10b2e000b8706e88ad9b77cf&"
)

# Channels with these words will be skipped by /setup verify
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
# INTENTS
# ============================================================

intents = discord.Intents.default()

# Needed so the bot can work with members and roles
intents.members = True

# Message content is NOT needed because we use slash commands.


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

    embed.set_image(url=IMAGE_URL)

    return embed


# ============================================================
# VERIFY BUTTON
# ============================================================

class VerifyView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="♡",
        style=discord.ButtonStyle.success,
        custom_id="verify_button",
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This button can only be used inside a server.",
                ephemeral=True,
            )

            return

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
                "Error giving verification role: %s",
                error,
            )

            await interaction.response.send_message(
                "❌ Discord returned an error. Please try again.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            "♡ You are now verified! You should have access to the server.",
            ephemeral=True,
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    # Keep the verification button working after restarts
    bot.add_view(
        VerifyView()
    )

    logger.info(
        "Logged in as %s (%s)",
        bot.user,
        bot.user.id,
    )


# ============================================================
# CHANNEL SELECT
# ============================================================

class VerifyPanelChannelSelect(
    discord.ui.ChannelSelect
):

    def __init__(self):

        super().__init__(
            placeholder="Choose the verification channel...",

            channel_types=[
                discord.ChannelType.text,
            ],

            min_values=1,
            max_values=1,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):

        # ====================================================
        # IMPORTANT FIX:
        # Respond immediately so Discord doesn't timeout.
        # ====================================================

        await interaction.response.defer(
            ephemeral=True
        )

        channel = self.values[0]

        logger.info(
            "Sending verification panel to #%s",
            channel.name,
        )

        try:

            await channel.send(
                embed=build_verify_embed(),
                view=VerifyView(),
            )

        except discord.Forbidden:

            await interaction.followup.send(
                f"❌ I can't send messages in {channel.mention}.\n\n"
                "Make sure the bot has:\n"
                "• View Channel\n"
                "• Send Messages\n"
                "• Embed Links",

                ephemeral=True,
            )

            return

        except discord.HTTPException as error:

            logger.error(
                "Failed to send verification panel: %s",
                error,
            )

            await interaction.followup.send(
                "❌ Discord returned an error while sending the panel.",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            f"✅ Verification panel sent to {channel.mention}!",
            ephemeral=True,
        )


class VerifyPanelSelectView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=60
        )

        self.add_item(
            VerifyPanelChannelSelect()
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
):

    if action.value != "verify_panel":

        await interaction.response.send_message(
            "❌ Invalid option.",
            ephemeral=True,
        )

        return

    await interaction.response.send_message(
        "Choose the channel where you want the verification panel:",
        view=VerifyPanelSelectView(),
        ephemeral=True,
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

    bot_member = guild.me

    if bot_member is None:

        await interaction.followup.send(
            "❌ I couldn't find my bot member.",
            ephemeral=True,
        )

        return

    # ========================================================
    # ROLE HIERARCHY CHECK
    # ========================================================

    if role >= bot_member.top_role:

        await interaction.followup.send(
            "❌ **Role hierarchy problem!**\n\n"
            "Move the bot's role ABOVE the verification role.\n\n"
            "It should look like:\n"
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

        if is_staff_channel(category):

            skipped += 1
            continue

        try:

            # Hide category from unverified users
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
                "No permission to edit category: %s",
                category.name,
            )

        except discord.HTTPException:

            failed += 1

    # ========================================================
    # CHANNELS
    # ========================================================

    for channel in guild.channels:

        # Don't process categories again
        if isinstance(
            channel,
            discord.CategoryChannel
        ):

            continue

        # Don't lock the channel where the command was run
        if channel.id == interaction.channel_id:

            skipped += 1
            continue

        # Skip staff channels
        if is_staff_channel(channel):

            skipped += 1
            continue

        try:

            # Hide from @everyone
            await channel.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            # Give verified role access
            await channel.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed += 1

        except discord.Forbidden:

            failed += 1

            logger.warning(
                "No permission to edit channel: %s",
                channel.name,
            )

        except discord.HTTPException:

            failed += 1

    # ========================================================
    # RESULT
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
# COMMAND ERROR HANDLING
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
