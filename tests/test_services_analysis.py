from modules import services

def test_recommendations():
    assert "Leave unchanged" in services.recommendation({"StartMode":"Disabled"})
    assert "hardware" in services.recommendation({"StartMode":"Auto","DisplayName":"NVIDIA Container"}).lower()
    assert "publisher" in services.recommendation({"StartMode":"Auto","DisplayName":"Example Service"}).lower()
