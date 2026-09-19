from modules.storage_center import StorageItem

def test_storage_item_is_immutable():
    item=StorageItem("Temp","C:\\Temp",10)
    assert item.size_bytes == 10
