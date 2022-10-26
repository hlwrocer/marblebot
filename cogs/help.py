import discord
from discord.ext import commands

class HelpCommands(commands.HelpCommand):
    def __init__(self):
        super().__init__(
                command_attrs={"help": "Show help about a command\n **command**(Optional): A command you want help for"}
        )

    def make_embed(self, title="Marbles Help", description=None):
        embed = discord.Embed()
        embed.title = title
        embed.description = description
        return embed


    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = self.make_embed("Marbles Help", f"Use `{self.context.clean_prefix}help <command>` for more info on a command.")
        for cog,commands in mapping.items():
            if len(commands) == 0 or cog == None or cog.qualified_name == 'Admin':
                pass
            else:
                embed.add_field(name = cog.qualified_name, value = f"{cog.description or 'No description'}\n{''.join([f'`{command.qualified_name}` ' for command in commands])}", inline=False)
        await ctx.send(embed=embed)


    async def send_command_help(self, command):
        embed = self.make_embed(self.context.clean_prefix + command.qualified_name + f'[{"|".join(command.aliases)}]')

        if command.help:
            embed.description = command.help
        else:
            embed.description = "No help found"

        embed.add_field(name="Usage", value=self.get_command_signature(command))
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        self.context.invoked_with = "help"
        embed = self.make_embed(f"{self.context.clean_prefix}{group.qualified_name}[{'|'.join(group.aliases)}] <subcommand>", description=group.help)
        for command in group.commands:
            embed.add_field(name = f"{command.qualified_name} {command.signature}", value= f"{command.help}\n_{self.get_command_signature(command)}_", inline=False)

        embed.set_footer(text=f'Use `{self.context.clean_prefix}help command` for more info on a command')
        await self.context.send(embed=embed)

    async def send_cog_help(ctx, cog):
        return


async def setup(bot):
    bot.old_help_command = bot.help_command
    bot.help_command = HelpCommands()

async def teardown(bot):
    bot.help_command = bot.old_help_command
