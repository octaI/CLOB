import time
import unittest
from decimal import Decimal

from clob_main import Order, IcebergOrder


class TestOrders(unittest.TestCase):

    def test_order_not_completed(self):
        order = Order("1", Decimal("100.1"), 100, "B", time.time())
        assert not order.is_complete()

    def test_order_completed(self):
        order = Order("1", Decimal("100.1"), 100, "B", time.time())
        amount = order.trade(100)
        assert amount == 100
        assert order.is_complete()
        assert not order.should_restart()

    def test_order_should_not_restart(self):
        order = Order("1", Decimal("100.1"), 100, "B", time.time())
        assert not order.should_restart()


class TestIcebergOrders(unittest.TestCase):

    def test_iceberg_order_not_completed(self):
        order = IcebergOrder("1", Decimal("100.1"), 100, "B", time.time(), 10)
        assert not order.is_complete()

    def test_iceberg_order_get_volume_property_returns_visible_volume(self):
        order = IcebergOrder("1", Decimal("100.1"), 100, "B", time.time(), 10)
        assert order.get_volume == 10

    def test_iceberg_order_should_restart(self):
        order = IcebergOrder("1", Decimal("100.1"), 100, "B", time.time(), 10)
        amount = order.trade(20, matching_order_timestamp=time.time())
        assert amount == 10
        assert order.is_complete()
        assert order.should_restart()

    def test_iceberg_order_full_should_not_restart_after_complete(self):
        order = IcebergOrder("1", Decimal("100.1"), 20, "B", time.time(), 10)
        amount = order.trade(10, matching_order_timestamp=time.time())
        assert amount == 10
        assert order.should_restart()
        amount = order.trade(10, matching_order_timestamp=time.time())
        assert amount == 10
        assert order.is_complete()
        assert not order.should_restart()


if __name__ == '__main__':
    unittest.main()
