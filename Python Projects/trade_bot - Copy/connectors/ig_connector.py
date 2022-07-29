import datetime

import requests, time

class IGConnector:
    DEMO_URL = 'https://demo-api.ig.com/gateway/deal'
    LIVE_URL = 'https://demo-api.ig.com/gateway/deal'

    def __init__(self, api_key, username, password, acc_type = 'DEMO'):
        self.session = requests.session()

        # Define the header
        self.session.headers['X-IG-API-KEY'] = api_key

        # Not strictly needed, but the documentation recommends it.
        self.session.headers['Accept'] = "application/json; charset=UTF-8"

        # Get URL
        self.url = self.DEMO_URL
        if acc_type == 'LIVE':
            self.url = self.LIVE_URL

        # Log in
        self.response = self.session.post(
            self.url + '/session',
            json={'identifier': username, 'password': password},
            headers={'VERSION': '2'},
        )

        # Raise error if any occurs
        self.response.raise_for_status()

        # Remain valid for 12h between calls
        self.session.headers['CST'] = self.response.headers['CST']
        self.session.headers['X-SECURITY-TOKEN'] = self.response.headers['X-SECURITY-TOKEN']

    def open_position(self, epic: str, direction: str, size: str, stop_loss_distance:str = None, stop_loss: str = None, order_type: str = "MARKET", level: str = None):
        CONFIRMATION_MESSAGE = {}
        bid_offer = self.get_market_snapshot(epic)

        self.session.headers['Version'] = "2"
        self.session.headers['_method'] = ""
        open_position_url = self.url + '/positions/otc'

        response = self.session.post(url = open_position_url,
                                     json={"epic": epic,
                                           "expiry": "-",
                                           "direction": direction,
                                           "size": size,
                                           "orderType": order_type,
                                           "level": level,
                                           "guaranteedStop": "false",
                                           "stopLevel": stop_loss,
                                           "stopDistance": stop_loss_distance,
                                           "forceOpen": "true",
                                           "limitLevel": None,
                                           "limitDistance": None,
                                           "quoteId": None,
                                           "currencyCode": "EUR"})

        # Get the time the trade was executed
        trade_time_stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S .%f") +"MS"

        # Deal Reference
        CONFIRMATION_MESSAGE.update(response.json())

        # Get bid offer
        CONFIRMATION_MESSAGE.update(bid_offer)

        # Get trade timestamp
        CONFIRMATION_MESSAGE["PYTHON_trade_executed_at"] = trade_time_stamp
        CONFIRMATION_MESSAGE["status_code"] = response.status_code

        # Await execution of trade
        time.sleep(0.2)

        # Get Trade confirmation info
        trade_confirmation_info = self.get_position_confirmation(CONFIRMATION_MESSAGE['dealReference'])
        CONFIRMATION_MESSAGE.update(trade_confirmation_info)

        return CONFIRMATION_MESSAGE

    def close_position_v2(self, epic: str, direction: str, size: str, stop_loss_distance:str = None, stop_loss: str = None, order_type: str = "MARKET", level: str = None):
        CONFIRMATION_MESSAGE = {}
        bid_offer = self.get_market_snapshot(epic)

        self.session.headers['Version'] = "2"
        self.session.headers['_method'] = ""
        open_position_url = self.url + '/positions/otc'
        # response = self.session.post(url = open_position_url,
        #                              json={"epic": epic,
        #                                    "expiry": "-",
        #                                    "direction": direction,
        #                                    "size": size,
        #                                    "orderType": "LIMIT",
        #                                    "level": bid_offer["offer"],
        #                                    "guaranteedStop": "false",
        #                                    "stopLevel": stop_loss,
        #                                    "stopDistance": stop_loss_distance,
        #                                    "forceOpen": "true",
        #                                    "limitLevel": None,
        #                                    "limitDistance": "3",
        #                                    "quoteId": None,
        #                                    "currencyCode": "EUR"})

        response = self.session.post(url = open_position_url,
                                     json={"epic": epic,
                                           "expiry": "-",
                                           "direction": self.flip_position(direction),
                                           "size": size,
                                           "orderType": order_type,
                                           "level": level,
                                           "guaranteedStop": "false",
                                           "stopLevel": stop_loss,
                                           "stopDistance": stop_loss_distance,
                                           "forceOpen": "false",
                                           "limitLevel": None,
                                           "limitDistance": None,
                                           "quoteId": None,
                                           "currencyCode": "EUR"})

        # Get the time the trade was executed
        trade_time_stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S .%f") +"MS"

        # Deal Reference
        CONFIRMATION_MESSAGE.update(response.json())

        # Get bid offer
        CONFIRMATION_MESSAGE.update(bid_offer)

        # Get trade timestamp
        CONFIRMATION_MESSAGE["PYTHON_trade_executed_at"] = trade_time_stamp
        CONFIRMATION_MESSAGE["status_code"] = response.status_code

        # Await execution of trade
        time.sleep(0.2)

        # Get Trade confirmation info
        trade_confirmation_info = self.get_position_confirmation(CONFIRMATION_MESSAGE['dealReference'])
        CONFIRMATION_MESSAGE.update(trade_confirmation_info)

        return CONFIRMATION_MESSAGE

    def get_open_positions(self):
        self.session.headers['Content-Type'] = "application/json; charset=UTF-8"
        self.session.headers['Accept'] = "application/json; charset=UTF-8"
        self.session.headers['Version'] = "2"
        self.session.headers['_method'] = ""
        try:
            response = self.session.get(self.url + '/positions', allow_redirects=True)
            positions = response.json()
            if positions != {}:
                result = positions['positions']
            else:
                result = {}
        except:
            result = {}
            print("405 ERROR on GET POSITIONS")

        return result

    def get_open_positions_for_epic(self, epic):
        all_open_positions = self.get_open_positions()
        positions_list = [position for position in all_open_positions if position['market']['epic'] == epic]
        return positions_list

    def close_position(self, deal_id, size, direction):
        CONFIRMATION_MESSAGE = {}

        self.session.headers['_method'] = "DELETE"
        self.session.headers['Version'] = '1'
        self.session.headers["Content-Type"] = "application/json; charset=UTF-8"

        close_position_url = self.url + '/positions/otc'
        response = self.session.post(url = close_position_url,
                                    json= {"dealId": deal_id,
                                            "epic": None,
                                            "expiry": None,
                                            "direction": self.flip_position(direction),
                                            "size": size,
                                            "level": None,
                                            "orderType": "MARKET",
                                            "timeInForce": None,
                                            "quoteId": None})

        # Add deal ID to confirmation message
        CONFIRMATION_MESSAGE.update(response.json())

        try:
            # Get confirmation message
            snapshot = self.get_market_snapshot(CONFIRMATION_MESSAGE['dealReference'])
            CONFIRMATION_MESSAGE.update(snapshot)
        except:
            print('Could not get close confirmation details for: %s' % CONFIRMATION_MESSAGE['dealReference'])

        return CONFIRMATION_MESSAGE

    def close_position_by_deal_reference(self, deal_reference, partial_close= False):
        message = {}
        open_positions = self.get_open_positions()
        for position in open_positions:
            if position['position']['dealReference'] == deal_reference:
                message = self.close_position(position['position']['dealId'],
                                    size = str(float(position['position']['size'])/2) if partial_close else position['position']['size'],
                                    direction= position['position']["direction"])
                message['deal_id'] = position['position']['dealId']

        return message


    def close_all_positions_for_epic(self, epic):
        CONFIRMATION_MESSAGES = {}
        epic_positions = self.get_open_positions_for_epic(epic)
        for position in epic_positions:
            CONFIRMATION_MESSAGES[position['position']['dealId']] = position['position']['dealId']
            self.close_position(position['position']['dealId'],
                                    size = position['position']['size'],
                                    direction = position['position']["direction"])

        return CONFIRMATION_MESSAGES

    def modify_position_stop_loss(self, deal_id:str, new_stop_level:str, epic:str):
        snapshot = self.get_market_snapshot(epic)

        # Modify headers
        self.session.headers['Version'] = "2"
        self.session.headers['Content-Type'] = "application/json; charset=UTF-8"

        # In the case of 2 digit stoploss update
        if len(str(new_stop_level)) == 2:
            new_stop_level = str(int(snapshot['offer']))[:3] + new_stop_level

        open_position_url = self.url + '/positions/otc/%s' %deal_id
        response = self.session.put(url = open_position_url,
                                    json= {"stopLevel": new_stop_level,
                                            "limitLevel": None,
                                            "trailingStop": None,
                                            "trailingStopDistance": None,
                                            "trailingStopIncrement": None})

        return response.json()

    def modify_stop_loss_by_epic(self, epic: str, new_stop_level: str = None, breakeven: bool = False):
        positions = self.get_open_positions_for_epic(epic)

        if breakeven:
            for position in positions:
                self.modify_position_stop_loss(deal_id=position['position']['dealId'], new_stop_level=position['position']['level'])
        else:
            for position in positions:
                self.modify_position_stop_loss(deal_id = position['position']['dealId'], new_stop_level= new_stop_level, epic = epic)

    def modify_stop_loss_for_most_recent_position(self, epic: str, new_stop_level: str = None):
        positions = self.get_open_positions_for_epic(epic)

        # Obtain the most recent position
        self.modify_position_stop_loss(deal_id= positions[-1]['position']['dealId'], new_stop_level = new_stop_level, epic = epic)

    def flip_position(self, input_position):
        result = "BUY"
        if input_position == "BUY":
            result = "SELL"
        return result

    def get_position_confirmation(self, deal_reference):
        # Modify headers
        self.session.headers['Version'] = "1"
        self.session.headers['Content-Type'] = "application/json; charset=UTF-8"

        confirmation_url = self.url + '/confirms/%s' %deal_reference
        response = self.session.get(confirmation_url)
        confirmation = response.json()
        confirmation['IG_trade_confirmation_date'] = confirmation['date'].replace("T", " ").replace('.', " .") +"MS"
        return {key: confirmation[key] for key in ["status", "IG_trade_confirmation_date", "dealStatus", "reason", "level", "stopLevel", "size"]}

    def get_market_snapshot(self, epic: str):
        self.session.headers['Version'] = "3"
        self.session.headers['_method'] = ""
        bid_offer_url = self.url + '/markets/%s' % epic

        # Get bid offer
        response = self.session.get(bid_offer_url)
        market_info = response.json()

        # Snapshot
        market_info_snapshot = market_info["snapshot"]
        market_info_snapshot["IG_last_available_bid_offer_time"] = market_info_snapshot['updateTime']

        return {key: market_info_snapshot[key] for key in ["bid", "offer", "IG_last_available_bid_offer_time"]}

if __name__ == '__main__':
    url = 'https://demo-api.ig.com/gateway/deal'
    API_KEY = 'eb533d9977119e0aa54de2d482ef9111afc7c29b'
    username = 'copydemo12'
    password = 'Copydemo12'

    connector = IGConnector(api_key=API_KEY, username=username, password= password)
    connector.open_position(epic = "IX.D.DAX.IFMM.IP",
                            direction = "BUY",
                            size = "1")

    print(len(connector.get_open_positions_for_epic(epic = "IX.D.DAX.IFMM.IP")))



