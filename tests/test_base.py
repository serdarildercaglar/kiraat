import pytest

from kiraat.base import ClipStage


class Fake(ClipStage):
    name = "fake"

    def process_clips(self, clips):
        return clips


def test_olcum_ciktisi_gecerli():
    Fake.validate_output([{"id": "a", "metrics": {"x": 1.0}, "flags": []}])


def test_klip_asamasi_karar_veremez():
    with pytest.raises(ValueError, match="karar veremez"):
        Fake.validate_output([{"id": "a", "recommended": True}])


def test_id_zorunlu():
    with pytest.raises(ValueError, match="'id' yok"):
        Fake.validate_output([{"metrics": {}}])
