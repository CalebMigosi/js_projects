import os, json
from connectors.meta_trader_5 import MT5Connector
from datetime import datetime

class DailyBlotter:
    """
    This is a queue containing all open trades at the current moment

    It is also the link between the messages parsed on telegram and the execution of trades on MT5.
    """
    BLOTTER = {}
    BLOTTER['NASDAQ'] = {}
    BLOTTER['DAX'] = {}
    BLOTTER['FTSE'] = {}
    BLOTTER['DOW'] = {}
    BLOTTER['BITCOIN'] = {}
    # Load index mapper
    with open(os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, 'config', 'index_mapper.json'))) as wb:
        INDEX_MAPPER = json.load(wb)

    def __init__(self):
        # Define connector
        self.connector = MT5Connector()

        # Fill blotter with existing trades
        self.fill_blotter()

    def fill_blotter(self):
        ''' Fill DailyBlotter object with all trades still open for the given account

            Objective is to manage all the trades in the account. Typically all positions should be closed at the end of the session with the exception of a number of cases.
        '''
        open_positions = self.connector.get_all_open_positions()

        # Associate positions to their respective indices
        for key in self.BLOTTER.keys():
            symbol = self.INDEX_MAPPER[key]['SYMBOL']
            if symbol in list(open_positions.keys()):
                for position in open_positions[symbol].values():
                    deal = {"ticket": position['ticket']}
                    self.BLOTTER[key][position['time_msc']] = deal

    def trade_position(self, message_json):
        ''' Execute either an open, close or stop loss modification trade based on the parameters parsed by the message_parser.

        :param message_json: json containing all the input values to be used to determine the trade to be executed.
        :return: message_json: dictionary containing all information concerning the operation eg buy price, ticket id
        '''
        self.message_json = message_json
        if self.message_json["trade_type"] == "OPEN TRADE":
            self.open_trade()

        elif self.message_json["trade_type"] == "CLOSE ALL INDEX POSITIONS":
            self.close_all_index_open_positions()

        elif self.message_json["trade_type"] == "CLOSE SINGLE POSITIONS":
            self.close_oldest_index_position()

        elif self.message_json["trade_type"] == "PARTIAL CLOSE":
            self.partial_index_close()

        elif self.message_json["trade_type"] == "CLOSE PREVIOUS TRADES":
            self.close_n_previous_trades()

        elif  self.message_json["trade_type"] == "STOP LOSS RESET":
            self.modify_stop_loss()

        elif self.message_json['trade_type'] == "STOP LOSS RESET FOR LAST TRADE":
            self.modify_stop_loss_for_most_recent_trade()

        elif self.message_json['trade_type'] == "GET CURRENT PNL":
            self.get_current_pnl_drilldown()

        # Reinitialize message_json object
        return self.message_json

    def open_trade(self):
        '''
            Open market position based on symbol, direction, stop loss (or stop loss distance) and size
        :return: confirmation message with acceptance/rejection of trade
        '''
        if self.message_json['stop_loss'] == "DISTANCE":
            deal_reference = self.connector.open_market_position_for_symbol(symbol = self.message_json["symbol"],
                                                          direction = self.message_json["direction"],
                                                          stop_loss_distance = self.message_json['stop_loss_distance'],
                                                          volume = self.message_json["size"])
        else:
            deal_reference = self.connector.open_market_position_for_symbol(symbol = self.message_json["symbol"],
                                                          direction = self.message_json["direction"],
                                                          stop_loss = self.message_json['stop_loss'],
                                                          volume = self.message_json["size"])

        # Add deal reference to message
        self.message_json.update(deal_reference)

        # Append position to blotter
        self.BLOTTER[self.message_json['index']][datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')] = self.message_json

    def close_all_index_open_positions(self):
        '''
            Close all positions with a specific symbol eg DE40
        '''
        messages = self.connector.close_all_positions_for_symbol(symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL'])

        # Update the message json
        self.message_json.update(messages)

        self.BLOTTER[self.message_json['index']] = {}

    def close_n_previous_trades(self):
        '''
        Close n previous trades. From close one/two etc trades
        :return:
        '''
        symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL']

        # Order positions by dates and select the n previous positions
        for i in range(int(self.message_json['number_of_trades'])):
            confirmation = self.connector.close_market_order_by_order_of_open(symbol = symbol, order = i)

            # Remove position from blotter by date
            self.BLOTTER[self.message_json['index']].pop(confirmation['time_msc'])

    def close_all_trade(self):
        for index in ["DOW", "DAX", "NASDAQ", "FTSE"]:
            if len(self.BLOTTER[index]) != 0:
                symbol = self.BLOTTER[index]['symbol']
                self.connector.close_all_positions_for_symbol(symbol = symbol)
                self.BLOTTER[index] = {}

    def partial_index_close(self):
        symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL']

        confirmation = self.connector.close_all_positions_for_symbol(symbol = symbol, partial_close = True)

        self.message_json.update(confirmation)

    def close_oldest_index_position(self):
        symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL']
        confirmation = self.connector.close_market_order_by_order_of_open(symbol = symbol, first = True)

        self.message_json.update(confirmation)

    def modify_stop_loss(self):
        symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL']
        if self.message_json['stop_loss_level'] == "BREAKEVEN":
            confirmation_message = self.connector.modify_stop_loss_for_symbol(symbol = symbol, breakeven = True)
        else:
            confirmation_message = self.connector.modify_stop_loss_for_symbol(symbol = symbol,new_stop_level= self.message_json["stop_loss_level"])

        self.message_json.update(confirmation_message)

    def modify_stop_loss_for_most_recent_trade(self):
        symbol = self.INDEX_MAPPER[self.message_json['index']]['SYMBOL']
        self.connector.modify_stop_loss_for_most_recent_position(symbol, self.message_json['stop_loss'])

    def get_current_pnl_drilldown(self):
        '''
            Get a rundown of all trades executed during the trading session and the pnl generated on each
        '''
        self.message_json = self.connector.get_pnl_drilldown(datetime.now())
