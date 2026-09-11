```python
import os
import logging

import discord
from discord.ext import commands
from discord import app_commands

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

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

# Channels containing these words in their name will NOT be modified
STAFF_KEYWORDS = (
    "staff",
    "admin",
    "administrator",
    "mod",
    "moderator",
)

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("verify-bot")


# --------------------------------------------------
# INTENTS
# --------------------------------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.members = True


# --------------------------------------------------
# BOT
# --------------------------------------------------

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


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def is_staff_channel(channel: discord.abc.GuildChannel) -> bool:
    """Returns True if the channel looks like a staff-only channel."""

    name = channel.name.lower()

    return any(
        keyword in name
        for keyword in STAFF_KEYWORDS
    )


def build_verify_embed() -> discord.Embed:
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR,
    )

    embed.set_image(url=IMAGE_URL)

    return embed


# --------------------------------------------------
# VERIFY BUTTON
# --------------------------------------------------

class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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
            return

        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ I couldn't find the verification role.",
                ephemeral=True,
            )
            return

        member = interaction.user

        if role in member.roles:
            await interaction.response.send_message(
                "♡ You are already verified!",
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(
                role,
                reason="User verified through verification panel",
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to give you the verification role. "
                "Please make sure my bot role is above the verification role.",
                ephemeral=True,
            )
            return

        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Discord returned an error while verifying you. "
                "Please try again.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "♡ You are now verified! You should have access to the server channels.",
            ephemeral=True,
        )


# --------------------------------------------------
# READY
# --------------------------------------------------

@bot.event
async def on_ready():

    # Persistent button
    bot.add_view(VerifyView())

    logger.info(
        "Logged in as %s (%s)",
        bot.user,
        bot.user.id,
    )


# --------------------------------------------------
# /SEND VERIFY PANEL
# --------------------------------------------------

class VerifyPanelChannelSelect(discord.ui.ChannelSelect):

    def __init__(self):
        super().__init__(
            placeholder="Choose the channel for the verification panel...",
            channel_types=[
                discord.ChannelType.text,
            ],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):

        channel = self.values[0]

        embed = build_verify_embed()

        try:
            await channel.send(
                embed=embed,
                view=VerifyView(),
            )

        except discord.Forbidden:
            await interaction.response.edit_message(
                content=(
                    f"❌ I can't send messages in {channel.mention}.\n"
                    "Please give me permission to view and send messages there."
                ),
                view=None,
            )
            return

        except discord.HTTPException:
            await interaction.response.edit_message(
                content="❌ Discord returned an error while sending the panel.",
                view=None,
            )
            return

        await interaction.response.edit_message(
            content=(
                f"✅ Verification panel sent successfully to {channel.mention}!"
            ),
            view=None,
        )


class VerifyPanelSelectView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)

        self.add_item(VerifyPanelChannelSelect())


@bot.tree.command(
    name="send",
    description="Send a verification panel.",
)
@app_commands.describe(
    action="Choose what you want to send.",
)
@app_commands.choices(
    action=[
        app_commands.Choice(
            name="verify panel",
            value="verify_panel",
        ),
    ]
)
@app_commands.checks.has_permissions(administrator=True)
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
        "Choose the channel where you want me to send the verification panel:",
        view=VerifyPanelSelectView(),
        ephemeral=True,
    )


# --------------------------------------------------
# /SETUP VERIFY
# --------------------------------------------------

@bot.tree.command(
    name="setup",
    description="Set up the verification system.",
)
@app_commands.describe(
    action="Choose what you want to set up.",
)
@app_commands.choices(
    action=[
        app_commands.Choice(
            name="verify",
            value="verify",
        ),
    ]
)
@app_commands.checks.has_permissions(administrator=True)
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

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ This command can only be used inside a server.",
            ephemeral=True,
        )
        return

    role = guild.get_role(VERIFY_ROLE_ID)

    if role is None:
        await interaction.followup.send(
            (
                "❌ I couldn't find the verification role.\n\n"
                f"Role ID: `{VERIFY_ROLE_ID}`"
            ),
            ephemeral=True,
        )
        return

    # Check bot role hierarchy
    bot_member = guild.me

    if bot_member is None:
        await interaction.followup.send(
            "❌ I couldn't find my bot member in this server.",
            ephemeral=True,
        )
        return

    if role >= bot_member.top_role:
        await interaction.followup.send(
            (
                "❌ My bot role must be **above** the verification role.\n\n"
                "Go to Server Settings → Roles and move my bot role "
                "above the verification role."
            ),
            ephemeral=True,
        )
        return

    everyone = guild.default_role

    changed_channels = 0
    skipped_channels = 0
    failed_channels = 0

    # --------------------------------------------------
    # CONFIGURE CATEGORIES FIRST
    # --------------------------------------------------

    for category in guild.categories:

        if is_staff_channel(category):
            skipped_channels += 1
            continue

        try:

            await category.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            await category.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed_channels += 1

        except discord.Forbidden:
            failed_channels += 1

        except discord.HTTPException:
            failed_channels += 1

    # --------------------------------------------------
    # CONFIGURE CHANNELS
    # --------------------------------------------------

    for channel in guild.channels:

        if isinstance(channel, discord.CategoryChannel):
            continue

        # Don't lock the channel where setup command was used
        # if it is the current interaction channel.
        if (
            isinstance(channel, discord.TextChannel)
            and channel.id == interaction.channel_id
        ):
            skipped_channels += 1
            continue

        if is_staff_channel(channel):
            skipped_channels += 1
            continue

        try:

            # Hide from unverified users
            await channel.set_permissions(
                everyone,
                view_channel=False,
                reason="Verification system setup",
            )

            # Allow verified users
            await channel.set_permissions(
                role,
                view_channel=True,
                reason="Verification system setup",
            )

            changed_channels += 1

        except discord.Forbidden:
            failed_channels += 1

        except discord.HTTPException:
            failed_channels += 1

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    embed = discord.Embed(
        title="♡ Verification Setup Complete",
        color=EMBED_COLOR,
    )

    embed.description = (
        "I configured the server's channel permissions for verification.\n\n"
        f"**Verification role:** {role.mention}\n"
        f"**Channels/categories changed:** `{changed_channels}`\n"
        f"**Skipped:** `{skipped_channels}`\n"
        f"**Failed:** `{failed_channels}`\n\n"
        "Unverified members will be unable to view the configured channels, "
        "while members with the verification role will be able to view them."
    )

    if failed_channels > 0:
        embed.add_field(
            name="⚠️ Some channels failed",
            value=(
                "This usually means the bot doesn't have **Manage Channels** "
                "permission or another permission/Discord hierarchy issue "
                "prevented the change."
            ),
            inline=False,
        )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True,
    )


# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

@send.error
async def send_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    if isinstance(error, app_commands.MissingPermissions):

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

    if isinstance(error, app_commands.MissingPermissions):

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


# --------------------------------------------------
# START
# --------------------------------------------------

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
```
