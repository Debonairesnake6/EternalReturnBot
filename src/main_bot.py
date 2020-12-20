"""
The main brains of the game. This handles all of the interactions with discord.
"""

import os
import urllib
import time
import sys
import path_calculator
import eternal_api

from discord import ActivityType, Activity
from discord.ext import commands
from dotenv import load_dotenv


class DiscordBot:
    """
    Discord Game Bot
    """

    def __init__(self):
        # Bot variables
        self.bot = commands.Bot(command_prefix='!')
        self.channel = None
        self.user_name = None
        self.user_id = None
        self.user_object = None
        self.display_name = None
        self.message = None
        self.reaction_payload = None
        self.message_type = None

        # Embeds
        self.main_embed = None
        self.inventory_embed = None

        # Start listening to chat
        self.start_bot()

    async def get_food_beverages(self, path_list: list):
        """
        Get the food and beverages based on the give route

        :param path_list: List of the areas traveling through
        """
        path_string = ' '.join(path_list)
        if len(path_string) > 0:
            path_calc = path_calculator.PathCalc(path_string, 'balanced').create_item_path()
            for message_type_main in path_calc:
                for message_main in path_calc[message_type_main]:
                    if message_type_main == 'error':
                        await self.message.channel.send(f'ERROR - {message_main}')
                    else:
                        await self.message.channel.send(message_main)
        else:
            await self.help_message()

    async def display_area_list(self, *args, **kwargs):
        """
        Display the list of each area and the designated number
        """
        areas_dict = eternal_api.EternalReturnApi().get_all_info()['areas']
        final_string = ''
        for cnt, area in enumerate(sorted(list(areas_dict.keys()))):
            if len(areas_dict[area]) != 0:
                final_string += f'{cnt:<3}- {area}\n'
        await self.message.channel.send(final_string)

    # @staticmethod
    # async def add_reactions(message: object, reactions: list):
    #     """
    #     Add reactions to the given message
    #
    #     :param message: Message to add the reactions to
    #     :param reactions: List of reactions to add
    #     """
    #     reactions_dict = {
    #         1: '1️⃣',
    #         2: '2️⃣',
    #         3: '3️⃣',
    #         4: '4️⃣',
    #         5: '5️⃣',
    #         6: '6️⃣',
    #         7: '7️⃣',
    #         8: '8️⃣',
    #         9: '9️⃣',
    #         'north': '⬆️',
    #         'south': '⬇️',
    #         'east': '⬅️',
    #         'west': '➡️',
    #         'reset': '♻️'
    #     }
    #     for reaction in reactions:
    #         await message.add_reaction(reactions_dict[reaction])

    async def help_message(self, *args, **kwargs):
        """
        Display the help message for the bot
        """
        await self.message.channel.send('Use `!er_list` to display each area\'s number.\n'
                                        'Then use `!er [area #1] [area #2]...` to calculate the best options for your given path.\n'
                                        'E.g. `!er 2 14 15`')

    async def unknown_command(self):
        """
        Tell the user the given command is unknown
        """
        await self.message.channel.send(f'Unknown command')

    def start_bot(self):
        """
        Start the bot
        """
        valid_commands = {
            'er': self.get_food_beverages,
            'er_list': self.display_area_list,
            'er_help': self.help_message
        }

        # noinspection PyArgumentList
        @self.bot.event
        async def on_message(message: object):
            """
            Receive any message

            :param message: Context of the message
            """
            if message.content != '' \
                    and message.content.split()[0][1:] in valid_commands \
                    and message.content[0] == '!'\
                    and not message.author.bot:
                self.user_name = message.author.name
                self.user_object = message.author
                self.display_name = message.author.display_name
                self.user_id = message.author.id
                self.message = message
                self.channel = message.channel
                await valid_commands[message.content.split()[0][1:]](message.content.split()[1:])

        # @self.bot.event
        # async def on_raw_reaction_add(reaction_payload: object):
        #     """
        #     Checks if a reaction is added to the message
        #
        #     :param reaction_payload: Payload information about the reaction
        #     """
        #     if reaction_payload.user_id not in self.bot_ids:
        #         self.reaction_payload = reaction_payload
        #         if reaction_payload.member is not None:
        #             self.user_object = reaction_payload.member
        #             self.user_name = reaction_payload.member.name
        #             self.display_name = reaction_payload.member.display_name
        #             self.user_id = reaction_payload.member.id
        #         else:
        #             self.user_object = await self.bot.fetch_user(reaction_payload.user_id)
        #             self.user_name = self.user_object.name
        #             self.display_name = self.user_object.display_name
        #             self.user_id = self.user_object.id
        #         self.channel = await self.bot.fetch_channel(self.reaction_payload.channel_id)
        #         await self.handle_reaction_result()
        #
        # @self.bot.event
        # async def on_raw_reaction_remove(reaction_payload: object):
        #     """
        #     Checks if a reaction is removed from the message
        #
        #     :param reaction_payload: Payload information about the reaction
        #     """
        #     if reaction_payload.user_id not in self.bot_ids:
        #         self.reaction_payload = reaction_payload
        #         self.user_object = await self.bot.fetch_user(reaction_payload.user_id)
        #         self.user_name = self.user_object.name
        #         self.display_name = self.user_object.display_name
        #         self.user_id = self.user_object.id
        #         self.channel = await self.bot.fetch_channel(self.reaction_payload.channel_id)
        #         await self.handle_reaction_result()

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')

            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='!er_help'))

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':

    # Load environment variables
    load_dotenv()

    while True:

        # Wait until retrying if the service is down
        try:
            DiscordBot()
            break

        # Catch if service is down
        except urllib.error.HTTPError as e:
            error_msg = "Service Temporarily Down"
            print(error_msg)
            print(e)
            # post_message(error_msg)
            time.sleep(60)

        # Catch random OS error
        except OSError as e:
            print(e, file=sys.stderr)
            time.sleep(60)
