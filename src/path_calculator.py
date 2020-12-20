"""
Handles all of the functionality with pathing and the items gathered from it
"""

import eternal_api


# noinspection PyMissingOrEmptyDocstring
class PathCalc:
    def __init__(self, path_list: str, list_type: str):
        """
        What the path calculator should find out.

        :param path_list: A list of numbers representing the given path
        :param list_type: The type of list to provide E.g. Total, Single, Balanced
        """
        # Public variables
        self.messages = {
            'info': [],
            'error': []
        }
        self.path = []

        # Private variables
        self.api_results = eternal_api.EternalReturnApi().get_all_info()
        self.__path_list = path_list.strip()
        self.foods_and_drinks = {}
        self.possible_items = {}
        self.ingredients = []
        self.list_type = list_type.strip().lower()
        self.result_count = 5

    def create_item_path(self):
        """
        Create an item list to grab based on the path given and the path type
        """
        if self.sanity_check():
            self.get_given_path()
            self.get_all_food_and_drink()
            self.get_ingredients()
            self.calculate_food()
            self.calculate_drink()
        return self.messages

    def sanity_check(self) -> bool:
        """
        Verify the given information is valid
        """
        if self.list_type not in ['total', 'single', 'balanced']:
            self.messages['error'].append('Unknown list type. Choose from: Total, Single, Balanced')
            return False
        return True

    def get_given_path(self):
        """
        Get the path based on the numbers given
        """
        areas = {
            '0': 'Alley',
            '1': 'Archery Range',
            '2': 'Avenue',
            '3': 'Beach',
            '4': 'Cemetery',
            '5': 'Chapel',
            '6': 'Dock',
            '7': 'Factory',
            '8': 'Forest',
            '9': 'Hospital',
            '10': 'Hotel',
            '11': 'Pond',
            '13': 'School',
            '14': 'Temple',
            '15': 'Uptown'
        }
        for number in self.__path_list.split():
            if number in areas:
                self.path.append(areas[number])
            else:
                self.messages['error'].append(f'Unrecognized area {number}')

    def get_all_food_and_drink(self):
        """
        Extract all of the food items
        """
        foods_and_drinks = [[name, info] for name, info in self.api_results['items'].items()
                            if info['ItemType'] in ['Food', 'Beverage']]
        for name, info in foods_and_drinks:
            self.foods_and_drinks[name] = info

    def get_ingredients(self):
        """
        Get all of the ingredients that can be gathered from the given path
        """
        for ingredient in self.foods_and_drinks:
            for area in self.path:
                if ingredient in self.api_results['areas'][area] and ingredient not in self.ingredients:
                    self.ingredients.append(ingredient)

        self.ingredients.append('Stone')
        self.ingredients.append('Branch')
        self.ingredients.append('Bread')
        self.ingredients.append('Water')

    def calculate_food(self):
        """
        Calculate the best food for the given path
        """
        self.get_possible_items('Heal')
        best_foods = self.get_best_items('Heal')
        self.create_message(best_foods, 'Best Foods To Create:', 'Heal')

    def calculate_drink(self):
        """
        Calculate the best drink for the given path
        """
        self.get_possible_items('SpRestore')
        best_drinks = self.get_best_items('SpRestore')
        self.create_message(best_drinks, 'Best Drinks To Create:', 'SpRestore')

    def get_possible_items(self, stat: str):
        """
        Get all of the possible food combinations based on the available ingredient list

        :param stat: The stat to compare
        """
        self.possible_items = {}
        stat_items = {item: info for item, info in self.foods_and_drinks.items() if info[stat] != ''}
        for item, info in stat_items.items():
            if item in self.ingredients:
                self.possible_items[item] = info
            elif info['Material1'] != '':
                if self.check_possible_items_recursive(info):
                    self.possible_items[item] = info

    # noinspection PyArgumentList,PyTypeChecker
    def get_best_items(self, stat: str) -> dict:
        """
        Get the best items based on the given criteria and available items

        :param stat: The stat to compare
        """
        options = {
            'single': self.get_highest_single_item,
            'total': self.get_highest_total_item,
            'balanced': self.get_highest_balanced_item
        }
        return options.get(self.list_type)(self.possible_items, stat)

    def get_highest_single_item(self, possible_items: dict, stat: str, double_results: bool = False) -> dict:
        """
        Get the highest valued item based on the given stat

        :param possible_items: Dictionary containing the possible items from the given path
        :param stat: The stat to compare
        :param double_results: If the results should be doubled when comparing with the highest total item
        """
        highest_items = {}
        for _ in range(self.result_count):
            try:
                highest_item = max(possible_items, key=lambda item: possible_items[item][stat])

            # Stop if there are fewer items available then trying to grab
            except ValueError:
                break
            highest_items[highest_item] = possible_items.pop(highest_item)
        return highest_items

    def get_highest_total_item(self, possible_items: dict, stat: str, double_results: bool = False) -> dict:
        """
        Get the highest total valued item based on the given stat

        :param possible_items: Dictionary containing the possible items from the given path
        :param stat: The stat to compare
        :param double_results: If the results should be doubled when comparing with the highest single item
        """
        highest_items = {}
        for _ in range(self.result_count):
            try:
                highest_item = max(possible_items,
                                   key=lambda item: possible_items[item][stat] * self.get_ingredient_count_recursive(possible_items[item]))

            # Stop if there are fewer items available then trying to grab
            except ValueError:
                break
            highest_items[highest_item] = possible_items.pop(highest_item)
        return highest_items

    def get_highest_balanced_item(self, possible_items: dict, stat: str) -> dict:
        """
        Get the highest balanced valued item based on the given stat

        :param possible_items: Dictionary containing the possible items from the given path
        :param stat: The stat to compare
        """
        self.result_count *= 2
        scores = {
            'single': {},
            'total': {}
        }

        # Rank the single items
        best_single = self.get_highest_single_item(possible_items.copy(), stat, True)
        current_highest = 99999
        for item in best_single.values():
            if item[stat] < current_highest:
                current_highest = item[stat]
                scores['single'][item['Name']] = len(scores['single'])
            else:
                scores['single'][item['Name']] = scores['single'][list(scores['single'].keys())[-1]]

        # Rank the total items
        best_total = self.get_highest_total_item(possible_items.copy(), stat, True)
        current_highest = 99999
        for item in best_total.values():
            item_total = item[stat] * self.get_ingredient_count_recursive(item)
            if item_total < current_highest:
                current_highest = item_total
                scores['total'][item['Name']] = len(scores['total'])
            else:
                scores['total'][item['Name']] = scores['total'][list(scores['total'].keys())[-1]]

        # Rank the best overall items
        final_score = {name_1: score_1 + score_2 for name_1, score_1 in scores['single'].items()
                       for name_2, score_2 in scores['total'].items() if name_1 == name_2}

        # Remove and which aren't crafted E.g. Water
        for item in final_score.copy():
            if self.api_results['items'][item]['Material1'] == '':
                final_score.pop(item)

        highest_items = {}
        self.result_count = int(self.result_count / 2)
        for _ in range(self.result_count):
            try:
                highest_item = min(final_score, key=final_score.get)

            # Stop if there are fewer items available then trying to grab
            except ValueError:
                break
            highest_items[highest_item] = self.api_results['items'][highest_item]
            final_score.pop(highest_item)
        return highest_items

    def create_message(self, item_dict: dict, item_header: str, stat: str):
        """
        Create the message to send back to the user based on the gathered information and type of message

        :param item_dict: Contains the recommended items in order
        :param item_header: The type of items in the dictionary
        :param stat: The type of stat that we are looking for E.g. Heal
        """
        final_string = f'**{item_header}**\n'
        for cnt, (name, item) in enumerate(item_dict.items()):
            ingredients = self.get_ingredients_for_item_recursive(item)
            final_string += f'*{name}*\n{self.get_ingredient_string(ingredients)}\n' \
                            f'{self.get_item_value_string(item, stat)}\n\n'
        self.messages['info'].append(final_string)

    def check_possible_items_recursive(self, item_info: dict) -> bool:
        """
        Recursively check if the item has all of the ingredients available from the given path

        :param item_info: Dictionary containing the information about the current item
        """
        if item_info['Material1'] != '':
            if self.check_possible_items_recursive(self.api_results['items'][item_info['Material1']]) and \
                    self.check_possible_items_recursive(self.api_results['items'][item_info['Material2']]):
                return True
            else:
                return False
        else:
            if item_info['Name'] in self.ingredients:
                return True
            else:
                return False

    def get_ingredients_for_item_recursive(self, item_info: dict) -> list:
        """
        Get all of the ingredients for the given item

        :param item_info: Contains the information for the current item
        """
        ingredients = []
        results = []
        if item_info['Material1'] != '':
            results.append(self.get_ingredients_for_item_recursive(self.api_results['items'][item_info['Material1']]))
            results.append(self.get_ingredients_for_item_recursive(self.api_results['items'][item_info['Material2']]))
            for result in results:
                if type(result) == list:
                    for item in result:
                        ingredients.append(item)
                else:
                    ingredients.append(result)
        else:
            return item_info['Name']
        return ingredients

    def get_ingredient_string(self, ingredients: list) -> str:
        """
        Get a string to represent where to collect each of the ingredients

        :param ingredients: List of ingredients to create the string for
        """
        final_string = ''

        # Create a string for each ingredient in the item
        for ingredient in ingredients:
            final_string += f'{ingredient} ({self.get_ingredient_areas_for_output(ingredient)}), '
        return final_string[:-2]

    def get_ingredient_areas_for_output(self, ingredient: str) -> str:
        """
        Get a list of each zone the ingredient spawns in.

        :param ingredient: What ingredient needs to be processed
        :return: A string based on the order of the given path. E.g. 1st, 3rd
        """
        area_string = ''
        spawning_areas = [area for area in self.api_results['areas'] if ingredient in self.api_results['areas'][area]]

        # If it spawns in every zone, just return All
        if not any([True for area in self.path if area not in spawning_areas]):
            return 'All'

        # Otherwise return a string with all of the places they do spawn
        for cnt, area in enumerate(self.path):
            if area in spawning_areas:
                if cnt % 10 == 0:
                    area_string += f'{cnt + 1}st, '
                elif cnt % 10 == 1:
                    area_string += f'{cnt + 1}nd, '
                elif cnt % 10 == 2:
                    area_string += f'{cnt + 1}rd, '
                else:
                    area_string += f'{cnt + 1}th, '

        # If it is given at the start, add that to the beginning. Water is on the map and at start
        if ingredient in ['Bread', 'Water']:
            area_string = f'Start, {area_string}'
        return area_string[:-2]

    def get_item_value_string(self, final_item_dict: dict, stat: str, quantity: bool = True) -> str:
        """
        Get the information for the final stats of the item

        :param final_item_dict: Dictionary of the final item
        :param stat: The type of stat that we are looking for E.g. Heal
        :param quantity: If the quantity of the items made should be displayed
        :return: String displaying the value information
        """
        if quantity:
            final_count = self.get_ingredient_count_recursive(final_item_dict)
            quantity_string = f', Quantity: {final_count}, Total: {final_item_dict[stat] * final_count}'
        else:
            quantity_string = ''
        value_string = f'{stat}: {final_item_dict[stat]}{quantity_string}'
        return value_string

    def get_ingredient_count_recursive(self, item_dict: dict):
        """
        Get the number of the final item will be crafted after using all of the ingredients

        :param item_dict: Dictionary of the current item
        :return:
        """
        if item_dict['Material1'] != '':
            count_1 = self.get_ingredient_count_recursive(self.api_results['items'][item_dict['Material1']])
            count_2 = self.get_ingredient_count_recursive(self.api_results['items'][item_dict['Material2']])
            if item_dict['Material1'] in ['Branch', 'Bread']:
                count_1 = 2
            elif item_dict['Material2'] in ['Branch', 'Bread']:
                count_2 = 2
            return min(count_1, count_2) * item_dict['InitialCount']
        else:
            return item_dict['InitialCount']


if __name__ == '__main__':
    path_calc = PathCalc('2 14 15', 'balanced').create_item_path()
    for message_type_main in path_calc:
        for message_main in path_calc[message_type_main]:
            if message_type_main == 'error':
                print(f'ERROR - {message_main}')
            else:
                print(message_main)
