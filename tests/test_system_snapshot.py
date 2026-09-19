from modules.system_snapshot import _network_records


def test_network_records_flatten_power_shell_values():
    records = _network_records(
        [
            {
                "InterfaceAlias": "Ethernet",
                "InterfaceDescription": "Test adapter",
                "IPv4Address": {"IPAddress": "192.168.1.10"},
                "IPv6Address": [{"IPAddress": "fe80::1"}, {"IPAddress": "2001:db8::1"}],
                "DNSServer": {"ServerAddresses": ["1.1.1.1", "8.8.8.8"]},
            }
        ]
    )

    assert records[0]["InterfaceAlias"] == "Ethernet"
    assert records[0]["IPv4Address"] == ["192.168.1.10"]
    assert records[0]["IPv6Address"] == ["fe80::1", "2001:db8::1"]
    assert records[0]["DNSServer"] == ["1.1.1.1", "8.8.8.8"]


def test_network_records_accept_strings_and_drop_empty_values():
    records = _network_records(
        [
            {
                "InterfaceAlias": "Wi-Fi",
                "IPv4Address": "192.168.0.20",
                "IPv6Address": None,
                "DNSServer": ["192.168.0.1", "8.8.8.8", ""],
            }
        ]
    )

    assert records[0]["IPv4Address"] == ["192.168.0.20"]
    assert records[0]["IPv6Address"] == []
    assert records[0]["DNSServer"] == ["192.168.0.1", "8.8.8.8"]


def test_network_records_handle_nested_address_lists():
    from modules.system_snapshot import _network_records

    records = _network_records([
        {
            "InterfaceAlias": "Ethernet 2",
            "IPv4Address": {"NetIPAddress": [{"IPAddress": "10.0.0.5"}]},
            "DNSServer": {"ServerAddresses": ["10.0.0.1"]},
        }
    ])

    assert records[0]["IPv4Address"] == ["10.0.0.5"]
    assert records[0]["DNSServer"] == ["10.0.0.1"]


def test_network_records_preserve_gateway_and_link_speed():
    records = _network_records(
        [
            {
                "InterfaceAlias": "Ethernet",
                "Status": "Up",
                "LinkSpeed": "1 Gbps",
                "IPv4DefaultGateway": ["192.168.1.1"],
                "IPv4Address": ["192.168.1.20"],
            }
        ]
    )

    assert records[0]["Status"] == "Up"
    assert records[0]["LinkSpeed"] == "1 Gbps"
    assert records[0]["IPv4DefaultGateway"] == ["192.168.1.1"]
