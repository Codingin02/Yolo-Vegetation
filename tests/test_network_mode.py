from ulp_project.network_mode import describe_network_modes, normalize_network_mode


def test_network_modes_cover_lan_tunnel_and_offline_queue():
    modes = describe_network_modes()
    assert {"same_lan_mode", "tunnel_mode", "offline_queue_mode"} <= set(modes)
    assert normalize_network_mode("tunnel_mode")["status"] == "NETWORK_MODE_READY"
    assert normalize_network_mode("unknown")["status"] == "NETWORK_MODE_UNKNOWN"
