import discord
from discord.ext import commands

class HelpCommands(commands.HelpCommand):
    def __init__(self):
        super().__init__(
                command_attrs={"help": "Show help about a command\n **command**(Optional): A command you want help for"}
        )

    def make_embed(self, title="Marbles Help", description=discord.Embed.Empty):
        embed = discord.Embed()
        embed.title = title
        embed.description = description
        return embed


    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot
        embed = self.make_embed("Marbles Help", f"Use `{self.clean_prefix}help <command>` for more info on a command.")
        for cog,commands in mapping.items():
            if len(commands) == 0 or cog == None or cog.qualified_name == 'Admin':
                pass
            else:
                print(commands)
                embed.add_field(name = cog.qualified_name, value = f"{cog.description or 'No description'}\n{''.join([f'`{command.qualified_name}` ' for command in commands])}", inline=False)
        await ctx.send(embed=embed)


    async def send_command_help(self, command):
        print(command)
        embed = self.make_embed(self.clean_prefix + command.qualified_name)

        if command.description:
            embed.description = f"{command.description}\n\n{command.help}"
        else:
            embed.description = command.help or "No help found"

        embed.add_field(name="Usage", value=self.get_command_signature(command))
        await self.context.send(embed=embed)

    async def send_group_help(ctx, group):
        return

    async def send_cog_help(ctx, cog):
        return


def setup(bot):
    bot.old_help_command = bot.help_command
    bot.help_command = HelpCommands()

def teardown(bot):
    bot.help_command = bot.old_help_command
