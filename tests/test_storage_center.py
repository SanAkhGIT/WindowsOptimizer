from modules.storage_center import CleanupCandidate, _size

def test_cleanup_candidate_is_immutable():
    item=CleanupCandidate("temp","Temp","C:\\Temp",100,"old files")
    assert item.size_bytes == 100
    try:
        item.size_bytes=200
        assert False
    except AttributeError:
        pass

def test_missing_path_has_zero_size(tmp_path):
    assert _size(tmp_path/"missing") == 0
