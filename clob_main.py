import sys
import heapq
import time
from decimal import Decimal


class Order:
    """
    A regular trade order
    """
    def __init__(self, id: str, price: Decimal, volume: int, type: str, timestamp: float):
        self.id = id
        self.price = price
        self.volume = volume
        self.type = type
        self.timestamp = timestamp

    def trade(self, amount, **kwargs) -> int:
        possible_amount = min(self.volume, amount)
        self.volume -= possible_amount
        return possible_amount

    def is_complete(self):
        return self.volume == 0

    def should_restart(self):
        return False

    @property
    def get_volume(self):
        return self.volume

    def __str__(self):
        return f"{self.id} | {self.type} | {self.volume} | {self.price}"


class IcebergOrder(Order):
    """
    Iceberg orders differ from Orders in that they have a recurring behaviour, related to their volume and
    visible quantity in the trade book.
    """
    def __init__(self, id: str, price: Decimal, volume: int, type: str, timestamp: float, visible_quantity: int):
        self.visible_quantity = visible_quantity
        self.visible_volume = visible_quantity
        super().__init__(id, price, volume, type, timestamp)

    def trade(self, amount, **kwargs) -> int:
        """
        Iceberg orders need to know whether this trade is aggressive or passive.
        Passive trade presents a similar behaviour to regular orders, with the
        exception of handling visible_volume alongside volume.
        Aggressive trading first consumes all prior matching orders, without having an
        impact on the visible_volume, unless the actual volume is less than the visible_quantity.
        :param amount: the amount intended to buy/sell from the other order.
        :param kwargs: matching_order_timestamp should be supplied
        :return: the actual amount that got transacted
        """
        matching_order_timestamp = kwargs["matching_order_timestamp"]
        is_aggressive = self.timestamp > matching_order_timestamp
        if is_aggressive:
            possible_amount = min(self.volume, amount)
        else:
            possible_amount = min(self.visible_volume, amount)
            self.visible_volume = self.visible_volume - possible_amount
        self.volume = self.volume - possible_amount
        self.visible_volume = min(self.volume, self.visible_volume)
        return possible_amount

    def should_restart(self) -> bool:
        if self.visible_volume == 0 and self.volume > 0:
            self.visible_volume = min(self.volume, self.visible_quantity)
            return True
        return False

    @property
    def get_volume(self):
        return self.visible_volume

    def is_complete(self):
        return self.visible_volume == 0



class CLOB:
    """
    Central Limit Order Book
    This class contains all the information regarding the orders book, as well as defining relative timestamps for
    orders as they are processed and matched.
    Buy and sell order books are represented with a heap. A match occurs each time the root of the buy heap price is
    greater than or equal to the sell price of the root of the sell heap.
    """
    def __init__(self):
        self.orders_book = {"B": {}, "S": {}}
        self.buy_orders, self.sell_orders = [], []
        self.epoch = time.time()


    def get_timestamp(self):
        return time.time() - self.epoch

    def start_trades(self):
        for line in sys.stdin.readlines():
            fields = line.rstrip().split(",")
            if len(fields) > 4:
                order = IcebergOrder(fields[0], Decimal(fields[2]), int(fields[3]), fields[1], self.get_timestamp(),
                                     int(fields[4]))
            else:
                order = Order(fields[0], Decimal(fields[2]), int(fields[3]), fields[1], self.get_timestamp())
            self.orders_book[fields[1]][fields[0]] = order
            if order.type == "S":
                heapq.heappush(self.sell_orders, (order.price, order.timestamp, order.id))
            else:
                heapq.heappush(self.buy_orders, (-order.price, order.timestamp, order.id))
            self.check_matches()

    def check_matches(self):
        match_log = {}
        while self.buy_orders and self.sell_orders and -self.buy_orders[0][0] >= self.sell_orders[0][0]:
            buy_order = self.orders_book["B"][self.buy_orders[0][2]]
            sell_order = self.orders_book["S"][self.sell_orders[0][2]]
            amount = buy_order.get_volume
            traded_amount = sell_order.trade(amount, matching_order_timestamp=buy_order.timestamp)
            if buy_order.timestamp > sell_order.timestamp:
                match_key = (buy_order.id, sell_order.id, sell_order.price)
            else:
                match_key = (sell_order.id, buy_order.id, buy_order.price)
            if match_key in match_log:
                match_log[match_key][1] += traded_amount
            else:
                match_log[match_key] = [time.time(), traded_amount]
            buy_order.trade(traded_amount, matching_order_timestamp=sell_order.timestamp)
            if sell_order.is_complete():
                heapq.heappop(self.sell_orders)
                if sell_order.should_restart():
                    heapq.heappush(self.sell_orders, (sell_order.price, self.get_timestamp(), sell_order.id))
            if buy_order.is_complete():
                heapq.heappop(self.buy_orders)
                if buy_order.should_restart():
                    heapq.heappush(self.buy_orders, (-buy_order.price, self.get_timestamp(), buy_order.id))
        sorted_logs = list(match_log.items())
        sorted_logs.sort(key=lambda x: x[1][0])
        for log in sorted_logs:
            print(f"trade {log[0][0]}, {log[0][1]}, {log[0][2]}, {log[1][1]}")

    def print_output(self):
        print(f"{'Buyers': <{19}}  Sellers")
        while self.buy_orders or self.sell_orders:
            order_line = ""
            if self.buy_orders:
                buy_order = self.orders_book["B"][heapq.heappop(self.buy_orders)[2]]
                order_line += f"{buy_order.get_volume: <{11},} {buy_order.price: <{5}} | "
            else:
                order_line += f"{'': <{11}} {'': <{11}} | "
            if self.sell_orders:
                sell_order = self.orders_book["S"][heapq.heappop(self.sell_orders)[2]]
                order_line += f"{sell_order.price: <{11}} {sell_order.get_volume: <{11},}"
            else:
                order_line += f"{'': <{11}} {'': <{11}}"
            print(order_line)


if __name__ == "__main__":
    clob = CLOB()
    clob.start_trades()
    clob.print_output()
