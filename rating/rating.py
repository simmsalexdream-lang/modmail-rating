import discord
from discord.ext import commands

LOG_CHANNEL_ID = 1572278796705464444


class RatingSelect(discord.ui.Select):
    def __init__(self, bot, user, closer, thread_id):
        self.bot = bot
        self.user = user
        self.closer = closer
        self.thread_id = thread_id

        options = [
            discord.SelectOption(label="5 Stars - Excellent", value="5", emoji="⭐"),
            discord.SelectOption(label="4 Stars - Good", value="4", emoji="⭐"),
            discord.SelectOption(label="3 Stars - Average", value="3", emoji="⭐"),
            discord.SelectOption(label="2 Stars - Poor", value="2", emoji="⭐"),
            discord.SelectOption(label="1 Star - Terrible", value="1", emoji="⭐"),
        ]
        super().__init__(
            placeholder="Select a rating for your support experience...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        rating = self.values[0]

        # Disable the dropdown after the user makes a selection
        self.disabled = True
        await interaction.response.edit_message(
            content=f"Thank you! You rated our support **{rating}/5** stars.",
            view=self.view,
        )

        # Send the rating result to your staff log channel
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            closer_text = (
                f"{self.closer.mention} (`{self.closer.id}`)"
                if self.closer
                else "Unknown / System"
            )

            embed = discord.Embed(
                title="New Support Rating",
                color=discord.Color.gold(),
            )
            embed.add_field(
                name="User",
                value=f"{self.user.mention} (`{self.user.id}`)",
                inline=True,
            )
            embed.add_field(
                name="Handled By",
                value=closer_text,
                inline=True,
            )
            embed.add_field(
                name="Rating",
                value=f"{'⭐' * int(rating)} ({rating}/5)",
                inline=False,
            )
            embed.set_footer(text=f"Thread ID: {self.thread_id}")
            await log_channel.send(embed=embed)


class RatingView(discord.ui.View):
    def __init__(self, bot, user, closer, thread_id):
        # Timeout after 24 hours (86400 seconds)
        super().__init__(timeout=86400)
        self.add_item(RatingSelect(bot, user, closer, thread_id))


class ServiceRating(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled):
        # Do not send a rating prompt if the ticket was closed silently
        if silent:
            return

        user = thread.recipient
        if not user:
            return

        embed = discord.Embed(
            title="How did we do?",
            description="Your support ticket has been closed. Please take a moment to rate the service you received using the dropdown below.",
            color=discord.Color.blurple(),
        )

        try:
            view = RatingView(self.bot, user, closer, thread.id)
            await user.send(embed=embed, view=view)
        except discord.Forbidden:
            # User has DMs disabled or blocked the bot
            pass


async def setup(bot):
    await bot.add_cog(ServiceRating(bot))
