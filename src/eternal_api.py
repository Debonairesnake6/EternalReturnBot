"""
Handle all of the communications with the Eternal Return API
"""

import requests
import json
import os
import datetime


# noinspection PyMissingOrEmptyDocstring
class EternalReturnApi:
    def __init__(self):
        """
        Class to interact with the Eternal Return Api
        """
        # Public variables
        self.all_info_dict = {
            'items': {},
            'areas': {},
            'characters': {}
        }

        # Private variables
        self.__base_url = 'http://api.playeternalreturn.com/aesop'
        self.__all_items = f'{self.__base_url}/item/all'
        self.__items_in_area = f'{self.__base_url}/area?areaName='
        self.__areas_for_item = f'{self.__base_url}/area?itemName='
        self.__character_stats = f'{self.__base_url}/char?name='
        self.__force_pull = False

    def get_all_info(self):
        """
        Get the required information from the API or on disk
        """
        if not self.__load_from_disk():
            self.__get_all_item_info()
            self.__get_all_area_info()
            self.__save_to_disk()

        return self.all_info_dict

    def __load_from_disk(self) -> bool:
        """
        Load the dictionary from disk if the last pull was recent

        :return True on successful load from disk.
        """
        # Can't load if the file doesn't exist
        if not os.path.isfile('../extra_files/api_results.json') or self.__force_pull:
            return False

        else:
            with open('../extra_files/api_results.json', 'r') as input_file:
                my_dict = json.load(input_file)

                # Don't load if the last pull was old
                if my_dict['__timestamp'] + 10800 < int(datetime.datetime.now().timestamp()):
                    return False

                # Use the on disk json file
                else:
                    self.all_info_dict = my_dict
                    return True

    def __get_all_item_info(self):
        """
        Get all of the information for each of the items
        """
        api_response = requests.get(self.__all_items)
        # self.all_info_dict['items'] = json.loads(api_response.content.decode().strip())
        all_items_list = json.loads(api_response.content.decode().strip())
        for item in all_items_list:
            self.all_info_dict['items'][item['Name']] = item

    def __get_all_area_info(self):
        """
        Get information for each of the areas
        """
        area_list = ['Alley', 'Temple', 'Avenue', 'Pond', 'Hospital', 'Archery Range', 'School', 'Research Center',
                     'Cemetery', 'Factory', 'Hotel', 'Forest', 'Chapel', 'Beach', 'Uptown', 'Dock']

        # Get a list of items for each area
        for area in area_list:
            self.all_info_dict['areas'][area] = {}
            api_response = requests.get(f'{self.__items_in_area}{area}')

            # Ignore the error if no results are found from the Research Center, that is expected
            try:
                items_in_area = json.loads(api_response.content.decode().strip())
            except json.JSONDecodeError:
                if area == 'Research Center':
                    pass
                else:
                    raise json.JSONDecodeError
                continue

            # Save the list to the class variable
            for item in items_in_area:
                self.all_info_dict['areas'][area][item['ItemName']] = item['DropCount']

        self.__add_items_not_in_containers()

    def __add_items_not_in_containers(self):
        """
        Add items not found in containers to the items available in each area
        """
        # Items that are from every area
        for area in self.all_info_dict['areas']:
            self.all_info_dict['areas'][area]['Stone'] = 99
            self.all_info_dict['areas'][area]['Branch'] = 99
            self.all_info_dict['areas'][area]['Meat'] = 99

        # Area specific
        area_specific_items = {
            'Potato': {'Alley': 4, 'Temple': 8, 'Pond': 4},
            'Cod': {'Beach': 4, 'Uptown': 4, 'Dock': 4},
            'Carp': {'Forest': 2, 'Pond': 9, 'Cemetery': 2},
            'Water': {'Hotel': 4, 'Forest': 3, 'Cemetery': 4, 'Pond': 11, 'Chapel': 1}
        }
        for item in area_specific_items:
            for area, count in area_specific_items[item].items():
                self.all_info_dict['areas'][area][item] = count

    def __save_to_disk(self):
        """
        Save all of the api information to disk so save bandwidth
        """
        # noinspection PyTypeChecker
        self.all_info_dict['__timestamp'] = int(datetime.datetime.now().timestamp())
        if not os.path.isdir('../extra_files'):
            os.mkdir('../extra_files')
        with open('../extra_files/api_results.json', 'w') as output_file:
            json.dump(self.all_info_dict, output_file)


if __name__ == '__main__':
    api_results = EternalReturnApi().get_all_info()
    print()
