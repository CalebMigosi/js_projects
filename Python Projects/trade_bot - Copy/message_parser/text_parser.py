import re, os, json
from copy import deepcopy

class MessageParser:
    RESULT = {}
    CONTEXT_INDEX = None

    def __init__(self, size: float):
        '''
        This parser

        :param size: default size for any position opened
        '''
        self.size = size
        # LOAD REGEX CONFIGS
        with open(os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, 'config', 'telegram_keywords.json'))) as wb:
            self.REGEX_CONFIGS = json.load(wb)

        # Load index mapper
        with open(os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, 'config', 'index_mapper.json'))) as wb:
            self.INDEX_MAPPER = json.load(wb)

    def get_trade_info(self, text_input, edited_message = False):
        self.edited_message = edited_message
        self.text_input = text_input.upper()

        # Remove links
        link_text = re.search("HTTPS[^\s]+", self.text_input)

        if link_text != None:
            self.text_input = self.text_input.replace(link_text.group(0), "")

        self.text_list = self.text_input.split('\n')

        # Remove all empty spaces
        self.text_list = list(filter(None, self.text_list))

        return self.parse_message()

    def parse_message(self):
        self.RESULT = {}

        # Check for all details of the trade in the message
        if all(text in self.text_input for text in ["ENTRY", "STOP", "INDEX"]):
            if self.edited_message:
                self.RESULT["trade_type"] = "STOP LOSS RESET FOR LAST TRADE"
                self.parse_index_name()
                self.parse_stop()
                self.RESULT['stop_loss_level'] = self.RESULT['stop_loss']
            else:
                self.parse_open_trade_message()

            self.CONTEXT_INDEX = self.RESULT['index']

        elif any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["STOP LOSS ALERT"]):
            self.parse_stop_loss_modification()

        # Get the PNL of the current date
        elif self.text_input == 'GET PNL':
            self.RESULT = {"trade_type": "GET CURRENT PNL"}

        else:
            self.parse_close_trade_message()

        return self.RESULT

    def parse_open_trade_message(self):
        self.parse_index_name()
        self.parse_trade_direction_and_size()
        self.parse_entry()
        self.parse_stop()
        self.RESULT["trade_type"] = "OPEN TRADE"
        self.CONTEXT_INDEX = deepcopy(self.RESULT['index'])
        return self.RESULT

    def parse_stop_loss_modification(self):
        self.RESULT["trade_type"] = "STOP LOSS RESET"
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
        else:
            self.RESULT.update(self.get_index_from_string(self.CONTEXT_INDEX))

        # Parse new stop loss level
        level = re.compile('[0-9]{1,3}(,|.)?[0-9]{1,10}').search(self.text_input)

        if level != None:
            self.RESULT['stop_loss_level'] = self.str_to_float(level[0])
        else:
            self.RESULT['stop_loss_level'] = 'BREAKEVEN'

        self.CONTEXT_INDEX = self.RESULT['index']
        return self.RESULT

    def parse_close_trade_message(self):
        if any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["PARTIAL CLOSE"]):
            self.parse_partial_close_for_single_index()
            self.RESULT["trade_type"] = "PARTIAL CLOSE"

        elif any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["CLOSE MOST PREVIOUS TRADES"]):
            self.parse_previous_trades()
            self.RESULT["trade_type"] = "CLOSE PREVIOUS TRADES"

        elif any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["CLOSE SPECIFIC TRADES"]):
            self.parse_single_index_close_message()
            self.RESULT["trade_type"] = "CLOSE SINGLE POSITIONS"

        elif any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["CLOSE ALL INDEX TRADES"]):
            self.parse_all_index_close_message()
            self.RESULT["trade_type"] = "CLOSE ALL INDEX POSITIONS"

        elif any(re.compile(text).search(self.text_input) for text in self.REGEX_CONFIGS["CLOSE ALL TRADE"]):
            self.parse_all_trade_close_message()
            self.RESULT["trade_type"] = "CLOSE ALL TRADE"

        else:
            index = self.get_index_from_string(self.text_input)
            if index != {}:
                self.CONTEXT_INDEX = deepcopy(index['index'])

            self.RESULT["trade_type"] = "NOT A PARSING MESSAGE. Updated context index to: %s" % self.CONTEXT_INDEX

        return self.RESULT

    def parse_single_index_close_message(self):
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
        else:
            self.RESULT['index'] = self.CONTEXT_INDEX

        self.parse_index()

    def parse_all_index_close_message(self):
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
        else:
            self.RESULT['index'] = self.CONTEXT_INDEX

        self.parse_index()

    def parse_partial_close_for_single_index(self):
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
        else:
            self.RESULT['index'] = self.CONTEXT_INDEX

        self.parse_index()

    def parse_previous_trades(self):
        self.RESULT["number_of_trades"] = self.get_number_of_trades(self.text_input)
        self.parse_index()

    def parse_index_name(self):
        if 'INDEX' in self.text_list[0]:
            compiler = re.compile("([A-Z]{3,12})?\s([A-Z]{3,12}|100)(?= INDEX)")
            index_string = compiler.search(self.text_list[0]).group()
            self.RESULT.update(self.get_index_from_string(index_string))

    def parse_trade_direction_and_size(self):
        if '=' in self.text_list[1]:
            self.RESULT['direction'] = "BUY" if self.text_list[1].split(" ")[1] == "LONG" else "SELL"

            # Open 10 positions
            self.RESULT['size'] = (float(re.compile('[0-9]{2,3}(?=%)').search(self.text_list[1])[0])/100) * self.size

    def parse_entry(self):
        # Check if there are any numbers after ENTRY =
        if re.compile("ENTRY(\s)?=(?!( ||  |    )[0-9]{1})").search(self.text_list[2]) != None:
            self.RESULT['entry'] = "MARKET"

        elif 'ENTRY' in self.text_list[2]:
            compiler = re.compile("(?<=ENTRY)( = |=|= | =)[0-9]{2,10}(.[0-9]{2,10})?")
            input_text = compiler.search(self.text_list[2]).group()
            input_text = input_text.replace(" ", "").replace("=", "")
            self.RESULT['entry'] = self.str_to_float(input_text)

    def parse_stop(self):
        if re.compile("STOP(\s)?=(?!( ||  |    )[0-9]{1})").search(self.text_list[3]) != None:
            if self.RESULT['index'] in ["FTSE", "DAX"]:
                self.RESULT['stop_loss'] = "DISTANCE"
                self.RESULT['stop_loss_distance'] = 30.0
            else:
                self.RESULT['stop_loss'] = "DISTANCE"
                self.RESULT['stop_loss_distance'] = 50.0

        elif 'STOP' in self.text_list[3]:
            compiler = re.compile("(?<=STOP)( = |=|= | =)[0-9]{2,10}(.[0-9]{2,10})?")
            input_text = compiler.search(self.text_list[3]).group()
            input_text = input_text.replace(" ", "").replace("=", "")
            self.RESULT['stop_loss'] = self.str_to_float(input_text)

    def str_to_float(self, string):
        return float(string.replace(",", "").replace(".", ""))

    def get_index_from_string(self, string):
        result = {}
        for key in self.INDEX_MAPPER.keys():
            if any(option in string for option in self.INDEX_MAPPER[key]["OPTIONS"]) or string == key:
                result['index'] = key
                result['symbol'] = self.INDEX_MAPPER[key]['SYMBOL']

        return result

    def get_number_of_trades(self, string):
        result = None
        string = re.compile("((1|2|3|4|ONE|TWO|THREE|FOUR)(?![0-9]{1}))").search(string).group(0)
        if any(number in string for number in ["FOUR", "4"]):
            result = 4
        elif any(number in string for number in ["THREE", "3"]):
            result = 3
        elif any(number in string for number in ["TWO", "BOTH", "2"]):
            result = 2
        elif any(number in string for number in ["ONE", "LAST", "1"]):
            result = 1

        return result

    def parse_index(self):
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
            self.CONTEXT_INDEX = deepcopy(index['index'])
        else:
            self.RESULT["index"] = self.CONTEXT_INDEX

    def parse_all_trade_close_message(self):
        index = self.get_index_from_string(self.text_input)
        if index != {}:
            self.RESULT.update(index)
        else:
            self.RESULT['index'] = self.CONTEXT_INDEX

        self.parse_index()

def test_message_parser():
    MessageParser.get_trade_info("STOP LOSS TO 11,618")
    MessageParser.get_trade_info("""PART OF THE  CLOSE TRADE ALERT 🇺🇸 CLOSING NASDAQ INDEX trade now""")
    MessageParser.get_trade_info("TAKE PROFIT on 2 at 13168")
    MessageParser.get_trade_info("CLOSE TRADE ALERT 🇬🇧 CLOSING FTSE INDEX trade now")

if __name__ == '__main__':
    test_message_parser()