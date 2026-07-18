import unittest

from broker.websocket import FyersDataStream, FyersSubscriptionError, normalize_symbols, to_fyers_symbol


class FakeDataSocket:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.subscriptions = []
        self.closed = False

    def connect(self):
        self.kwargs["on_connect"]()

    def subscribe(self, symbols, data_type):
        self.subscriptions.append((symbols, data_type))

    def close_connection(self):
        self.closed = True


class FyersWebsocketTests(unittest.TestCase):
    def test_converts_yahoo_symbols_to_fyers_equity_symbols(self):
        self.assertEqual(to_fyers_symbol("tcs.ns"), "NSE:TCS-EQ")
        self.assertEqual(to_fyers_symbol("NSE:INFY-EQ"), "NSE:INFY-EQ")
        self.assertEqual(
            normalize_symbols(["TCS.NS", "NSE:TCS-EQ", "INFY.NS"]),
            ["NSE:TCS-EQ", "NSE:INFY-EQ"],
        )

    def test_rejects_more_symbols_than_configured_limit(self):
        with self.assertRaisesRegex(FyersSubscriptionError, "Requested 2"):
            normalize_symbols(["TCS.NS", "INFY.NS"], max_symbols=1)

    def test_stream_subscribes_and_normalizes_messages_without_network(self):
        ticks = []
        stream = FyersDataStream(
            ["TCS.NS"],
            token="header.payload.signature",
            socket_factory=FakeDataSocket,
            on_tick=ticks.append,
        )

        stream.start()
        socket = stream._socket
        self.assertEqual(socket.subscriptions, [(["NSE:TCS-EQ"], "SymbolUpdate")])

        socket.kwargs["on_message"](
            {
                "symbol": "NSE:TCS-EQ",
                "ltp": 3500.25,
                "timestamp": 1729912302,
                "open_price": 3480.0,
                "high_price": 3510.0,
                "low_price": 3475.0,
                "vol_traded_today": 12345,
            }
        )

        self.assertEqual(ticks[0].ltp, 3500.25)
        self.assertEqual(ticks[0].volume, 12345.0)
        self.assertEqual(stream.latest("TCS.NS"), ticks[0])
        stream.stop()
        self.assertTrue(socket.closed)
