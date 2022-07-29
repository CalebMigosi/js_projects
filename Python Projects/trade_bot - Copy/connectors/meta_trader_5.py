import datetime

import MetaTrader5 as mt5
import configparser, os, json

class MT5Connector:
    '''This is the main connector to the MT5 platform.

        This class will connect to MT5 and initiate & edit trades once received from
    '''
    # Obtain the login configurations
    config = configparser.ConfigParser()
    CONFIG_FILE = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, "config", "config_IDs.ini"))
    config.read(CONFIG_FILE)

    def __init__(self):
        '''
            Connect to IG account using account number, server and password
        '''
        account_number = int(self.config['ICMarkets']['IC_ACCOUNT_NUMBER'])
        server = self.config['ICMarkets']['IC_SERVER']
        password = self.config['ICMarkets']['IC_PASSWORD']

        # Connect to MetaTrader 5
        if not mt5.initialize(login=account_number, server=server, password=password):
            print("initialize() failed, error code =", mt5.last_error())
            quit()
        else:
            print("Successfully logged in to IC Markets")

    def get_account_info(self):
        '''
            Get details on the current account being used
        '''
        return mt5.account_info()

    def get_symbols(self):
        '''
            Get list of all symbols available on the platform
        '''
        return [print (i) for i in mt5.symbols_get()[0]._asdict().keys()]

    def get_symbol_info(self, symbol: str):
        '''
            Get list of pertinent info about a symbol including bid/ask, max volume, min volume etc
        '''
        return mt5.symbol_info(symbol)._asdict()

    def get_bid_ask(self, symbol: str):
        '''
            Get bid ask spread of symbol
        '''
        return mt5.symbol_info_tick(symbol)._asdict()

    def get_number_of_active_limit_orders(self):
        '''
            Get list of all active orders on the account.

            Note that these are LIMIT ORDERS that are yet to be filled.

            To find the list of open positions use get_open_positions
        '''
        return mt5.orders_total()

    def get_number_of_open_positions(self):
        '''
            Get list of all open positions

        :return: List: list containing all open positions for the account
        '''
        return mt5.positions_total()

    def get_open_positions_for_symbol(self, symbol:str):
        '''
        Returns a dictionary of all open positions for a given symbol

        :param symbol: this is the name of the symbol we want to use.
        :return: Dictionary with all positions and their respective information
        '''
        positions = {}
        for position in mt5.positions_get(symbol=symbol):
            position_dict = position._asdict()
            positions[position_dict['time_msc']] = position_dict

        return positions

    def get_all_open_positions(self):
        '''
        Returns a dictionary of all open positions in the account

        Positions are classified by their symbol and timestamp in milliseconds
        :param symbol: this is the name of the symbol we want to use.
        :return: Dictionary with all positions and their respective information. Example:

                {"USTEC": {"1657213998276": {'ticket': 241727694, 'time': 1657213998, 'time_msc': 1657213998276 .....} }}
        '''
        positions = {}

        # Get all open positions and convert to dictionary
        for position in mt5.positions_get():
            position_dict = position._asdict()
            position_symbol = position_dict['symbol']
            position_timestamp = position_dict['time_msc']

            # Create field for position symbol if not included
            if position_symbol not in positions.keys():
                positions[position_symbol] = {}

            # Add position by symbol and timestamp
            positions[position_symbol][position_timestamp] = position_dict

        return positions

    def open_market_position_for_symbol(self, symbol:str, volume: float = 1.0, direction: str = "BUY", stop_loss: float = None, stop_loss_distance: float = None):
        '''
            Open market position for a specific symbol
        :param symbol: Name of the symbol eg USTEC
        :param volume: Number of positions to open. Is 1.0 by default
        :param direction: Either BUY or SELL
        :param stop_loss: Stop loss to be applied to the position
        :param stop_loss_distance: Distance from the available offer/ask price where the stop loss should be
        :return: confirmation of open position
        '''
        bid_ask_for_symbol = self.get_bid_ask(symbol)

        # Set distance to proper direction ie negative when buy and +ve when sell
        if stop_loss_distance != None:
            stop_loss_distance = - abs(stop_loss_distance) if direction == 'BUY' else abs(stop_loss_distance)

        # Create request dictionary
        request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
                    "sl": bid_ask_for_symbol["ask"] + stop_loss_distance if stop_loss is None else stop_loss,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

        # Send request
        result = mt5.order_send(request)
        result = result._asdict()
        result['request'] = result['request']._asdict()
        return result

    def get_position_info_by_ticket(self, ticket: int):
        '''
        Get all positions by the value of the ticket

        :param ticket: Value of ticket
        :return: dictionary with the information of the position
        '''
        return mt5.positions_get(ticket = ticket)[0]._asdict()

    def close_market_order_position_by_ticket(self, ticket: int, partial_close: bool = False):
        '''
        Close a position using the ticket

        Note that the type = 0 is a BUY and type = 1 is a SELL

        :param ticket: unique identifier for the deal
        :return: result is a dictionary with the expected result
        '''
        # Get the position using the ticket
        position = self.get_position_info_by_ticket(ticket)

        request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position['symbol'],
                    "volume": position['volume']/2 if partial_close else position['volume'],
                    "type":  mt5.ORDER_TYPE_BUY if position['type'] == 1 else mt5.ORDER_TYPE_SELL,
                    "position": position["ticket"],
                    "comment": "close trade %s %s" % (position["ticket"], position['symbol']),
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

        # Send request
        result = mt5.order_send(request)
        result = result._asdict()
        result['request'] = result['request']._asdict()

        # Obtain the time of opening of the position
        result['time_msc'] = position['time_msc']
        return result

    def close_market_order_by_order_of_open(self, symbol: str, order: int = 0, first:bool = False, last: bool = False):
        '''
            Modify stop loss for the most recently opened position. Useful when a trade is received

        :param symbol: symbol we are querying for. We will get all positions opened for this symbol
        :param new_stop_level: float of the new stop loss whose value we want to change
        :param breakeven: if breakeven is true, set stop loss to the offer price
        :return: confirmation dictionary with all the details of the stop loss modification
        '''
        positions = self.get_open_positions_for_symbol(symbol)

        # Get the most recent date
        dates = list(positions.keys())

        # Sort from oldest to newest trade
        dates.sort()

        # Get date by order
        pertinent_date = dates[order]

        # Change the pertinent date if asked to close the first, or last position
        if last:
            pertinent_date = dates[len(dates)]
        elif first:
            pertinent_date = dates[0]

        # Obtain the most recent position
        result = self.close_market_order_position_by_ticket(ticket= positions[pertinent_date]['ticket'])

        return result

    def close_all_positions_for_symbol(self, symbol:str, partial_close: bool = False):
        '''
           Close all positions for a specific symbol eg change all stop losses for US30

        :param symbol: symbol we are querying for. We will get all positions opened for this symbol
        :return: confirmation dictionary with all the details of the trade
        '''
        positions = self.get_open_positions_for_symbol(symbol)
        results = {}

        for position in positions.values():
            results[str(position['ticket'])] = self.close_market_order_position_by_ticket(ticket = position['ticket'], partial_close = partial_close)

        return results

    def modify_stop_loss_for_ticket(self, ticket: int, new_stop_level: float = None, breakeven: bool = False):
        '''
        Modify the stop loss on a position

        :param ticket: unique identifier for the deal
        :return: result is a dictionary with a confirmation message for the trade
        '''
        # Get the position using the ticket
        position = self.get_position_info_by_ticket(ticket)

        # Set a limit to stop loss
        final_stop_level = max(position["price_open"]-100, new_stop_level) if position['type'] == 0 else min(position["price_open"]+100, new_stop_level)

        # Create request object
        request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": position['symbol'],
                    "sl":  position["price_open"] if breakeven else final_stop_level,
                    "position": position["ticket"],
                }

        # Send request
        result = mt5.order_send(request)
        result = result._asdict()
        result['request'] = result['request']._asdict()
        return result

    def modify_stop_loss_for_symbol(self, symbol: str, new_stop_level: float = None, breakeven: bool = False):
        '''
            Modify all stop losses for a specific symbol eg change all stop losses for US30

        :param symbol: symbol we are querying for. We will get all positions opened for this symbol
        :param new_stop_level: float of the new stop loss whose value we want to change
        :param breakeven: if breakeven is true, set stop loss to the offer price
        :return: confirmation dictionary with all the details of the trade
        '''
        positions = self.get_open_positions_for_symbol(symbol)
        results = {}
        if breakeven:
            for position in positions.values():
                results[str(position['ticket'])] = self.modify_stop_loss_for_ticket(ticket=position['ticket'], new_stop_level = position['price_open'], breakeven = breakeven)
        else:
            for position in positions.values():
                results[str(position['ticket'])] = self.modify_stop_loss_for_ticket(ticket = position['ticket'], new_stop_level = new_stop_level)

        return results

    def modify_stop_loss_for_most_recent_position(self, symbol: str, new_stop_level: float = None):
        '''
            Modify stop loss for the most recently opened position. Useful when a trade is received

        :param symbol: symbol we are querying for. We will get all positions opened for this symbol
        :param new_stop_level: float of the new stop loss whose value we want to change
        :param breakeven: if breakeven is true, set stop loss to the offer price
        :return: confirmation dictionary with all the details of the stop loss modification
        '''
        positions = self.get_open_positions_for_symbol(symbol)

        # Get the most recent date
        most_recent_date = max(list(positions.keys()))

        # Obtain the most recent position
        result = self.modify_stop_loss_for_ticket(ticket= positions[most_recent_date]['ticket'], new_stop_level = new_stop_level)

        return result

    def get_pnl_drilldown(self, date: datetime.datetime):
        ''' Get a rundown of the pnl for a specific date

        :param date: date of consideration. This is a datetime object
        :return: dict: contains the symbol, price and pnl
        '''
        # Define trading hours
        end_date_time = date.replace(day = date.day+1)

        # Get all positions for the given date only for trading hours
        positions = mt5.history_deals_get(date, end_date_time)

        pnl_drilldown = {}
        pnl = 0
        for position in positions:
            position_datetime = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds = position.time)

            # Get pnl only during trading hours
            position_datetime_str = position_datetime.strftime("%Y-%m-%d %H:%M:%S")
            pnl_drilldown[position_datetime_str] = {}
            pnl_drilldown[position_datetime_str]['symbol'] = position.symbol
            pnl_drilldown[position_datetime_str]['pnl'] = position.profit
            pnl_drilldown[position_datetime_str]['price'] = position.price
            pnl += position.profit

        pnl_drilldown['total_pnl'] = pnl
        return pnl_drilldown

def test_mt5_connector():
    mtconnector = MT5Connector()

    # Get all info about index
    print("================TEST DAILY PNL =================")
    date = datetime.datetime(2022, 7, 8)
    print(json.dumps(mtconnector.get_pnl_drilldown(date), indent = 4))
    print("\n")

    # Get all info about index
    print("================TEST SYMBOL INFO=================")
    print(json.dumps(mtconnector.get_symbol_info("USTEC"), indent = 4))
    print("\n")

    # Get bid ask spread
    print("================TEST TICK=================")
    print(json.dumps(mtconnector.get_bid_ask("USTEC"), indent = 4))
    print("\n")

    # Get number of active limit orders
    print("================TEST ACTIVE ORDERS=================")
    print(json.dumps(mtconnector.get_number_of_active_limit_orders(), indent = 4))
    print("\n")

    # Get number of open positions
    print("================TEST OPEN POSITIONS =================")
    print(json.dumps(mtconnector.get_number_of_open_positions(), indent = 4))
    print("\n")

    # Get active positions for symbol
    print("================TEST POSITIONS FOR SYMBOL =================")
    print(mtconnector.get_open_positions_for_symbol("USTEC"))
    print("\n")

    # Get active orders
    print("================TEST GET ALL POSITIONS =================")
    print(json.dumps(mtconnector.get_all_open_positions(), indent = 4))
    print("\n")

    # Open market position
    print("================TEST OPEN MARKET POSITION WITH STOP LOSS DISTANCE=================")
    result = mtconnector.open_market_position_for_symbol(symbol = 'USTEC',
                                                      volume = 1.0,
                                                      direction = "BUY",
                                                      stop_loss_distance = 50.0)
    print(json.dumps(result, indent = 4))
    print("\n")

    print("================TEST CLOSE MARKET POSITION WITH STOP LOSS=================")
    result = mtconnector.close_market_order_position_by_ticket(result['order'])
    print(json.dumps(result, indent = 4))
    print("\n")


    print("================TEST OPEN MARKET POSITION WITH STOP LOSS=================")
    result = mtconnector.open_market_position_for_symbol(symbol = 'US30',
                                                      volume = 1.0,
                                                      direction = "SELL",
                                                      stop_loss = 31500.0)
    print(json.dumps(result, indent = 4))

    print("================TEST CLOSE MARKET POSITION WITH STOP LOSS=================")
    result = mtconnector.close_market_order_position_by_ticket(result['order'])
    print(json.dumps(result, indent = 4))
    print("\n")

    print("================TEST OPEN MARKET POSITION WITH STOP LOSS=================")
    result = mtconnector.open_market_position_for_symbol(symbol = 'US30',
                                                      volume = 1.0,
                                                      direction = "SELL",
                                                      stop_loss = 31500.0)
    print(json.dumps(result, indent = 4))



    print("================TEST STOP LOSS MODIFICATION=================")
    stop_loss_modification_confirmation = mtconnector.modify_stop_loss_for_ticket(ticket = result['order'], new_stop_level = 32000.0)
    print(json.dumps(stop_loss_modification_confirmation, indent = 4))


    print("================TEST BREAKEVEN STOP LOSS MODIFICATIONS=================")
    break_even_stop_loss_confirmation = mtconnector.modify_stop_loss_for_ticket(ticket = result['order'], breakeven = True)
    print(json.dumps(break_even_stop_loss_confirmation, indent = 4))

    print("================ CLOSE ALL POSITIONS FOR THE US30 =================")
    close_position_confirmation = mtconnector.close_all_positions_for_symbol(symbol = "US30")
    print(json.dumps(close_position_confirmation, indent=4))
    print("\n")

    # Open multiple market position
    print("================TEST OPEN MULTIPLE MARKET POSITION WITH STOP LOSS DISTANCE=================")
    result = mtconnector.open_market_position_for_symbol(symbol = 'USTEC',
                                                      volume = 1.0,
                                                      direction = "BUY",
                                                      stop_loss_distance = 50.0)

    result = mtconnector.open_market_position_for_symbol(symbol = 'USTEC',
                                                      volume = 1.0,
                                                      direction = "BUY",
                                                      stop_loss_distance = 50.0)

    result = mtconnector.open_market_position_for_symbol(symbol = 'USTEC',
                                                      volume = 1.0,
                                                      direction = "BUY",
                                                      stop_loss_distance = 50.0)

    # Change stop losses for specific symbol
    break_even_stop_loss_confirmation = mtconnector.modify_stop_loss_for_symbol(symbol ="USTEC", new_stop_level = 10000.0)
    break_even_stop_loss_confirmation = mtconnector.modify_stop_loss_for_most_recent_position(symbol = "USTEC" , new_stop_level=11000.0)
    print(json.dumps(break_even_stop_loss_confirmation, indent = 4))
    print("\n")

    # Open multiple market position
    print("================ CLOSE ALL POSITIONS FOR USTEC =================")
    close_position_confirmation = mtconnector.close_all_positions_for_symbol(symbol = "USTEC")
    print(json.dumps(close_position_confirmation, indent=4))
    print("\n")

if __name__ == '__main__':
    test_mt5_connector()



