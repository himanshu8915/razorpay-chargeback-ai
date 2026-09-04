ALLOWED_CASE_FIELDS = {
    "transaction": [
        "transaction_id",
        "payment_type",
        "payment_installments",
        "payment_value",
        "payment_total",
        "payment_count",
        "transaction_status",
        "authorization_status",
    ],
    "order": [
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_delay_days",
        "purchase_to_delivery_days",
        "derived_delivery_state",
        "order_channel",
    ],
    "delivery": [
        "delivery_id",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_delay_days",
        "delivery_state",
        "tracking_id",
        "carrier_name",
    ],
    "customer": [
        "customer_city",
        "customer_state",
        "customer_zip_code_prefix",
        "customer_region",
        # PII fields (name, email, phone) explicitly EXCLUDED
    ],
    "merchant": [
        "seller_city",
        "seller_state",
        "seller_zip_code_prefix",
        "merchant_region",
        # PII fields EXCLUDED
    ]
}
