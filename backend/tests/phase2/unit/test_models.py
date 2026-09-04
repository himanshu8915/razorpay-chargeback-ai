import pytest
from app.db.models import Dispute, Transaction, Order, Delivery

def test_models_exist():
    # Basic check that the classes instantiate correctly without relationship errors
    d = Dispute(dispute_id="D1", transaction_id="T1", canonical_order_id="O1")
    assert d.dispute_id == "D1"
    
    t = Transaction(transaction_id="T1", payment_value=100.0)
    assert t.transaction_id == "T1"
    
    o = Order(order_id="O1", order_status="delivered")
    assert o.order_id == "O1"
