from dashboard.demo_data import DEMO_ALERTS, DEMO_TRAFFIC, lab_addresses


def test_demo_data_uses_lab_addresses_and_contract_fields() -> None:
    assert len(DEMO_TRAFFIC) >= 6
    assert len(DEMO_ALERTS) >= 3
    assert lab_addresses(DEMO_TRAFFIC, "src_ip", "dst_ip")
    assert lab_addresses(DEMO_ALERTS, "src_ip", "dst_ip")
    for row in DEMO_TRAFFIC:
        assert row["verdict"] == "Temiz"
        assert {"id", "captured_at", "protocol", "packet_size"} <= set(row)
    assert {row["label"] for row in DEMO_ALERTS} >= {"DDoS", "Port Scan", "Brute Force"}
