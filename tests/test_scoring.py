from kiraat.scoring import Policy, annotate

POLICY = Policy.from_dict({
    "version": "test-1",
    "rules": [
        {"metric": "speech_ratio", "min": 0.6},
        {"metric": "clip_ratio", "max": 0.002},
        {"metric": "dnsmos_ovrl", "min": 3.0, "allow_missing": True},
        {"flag_absent": ["oversize", "forced_split", "duplicate"]},
    ],
})


def test_temiz_klip_onerilir():
    ok, reasons = POLICY.evaluate({"speech_ratio": 0.9, "clip_ratio": 0.0}, [])
    assert ok and reasons == ()


def test_esik_altinda_gerekce_dondurur():
    ok, reasons = POLICY.evaluate({"speech_ratio": 0.4, "clip_ratio": 0.0}, [])
    assert not ok
    assert "speech_ratio<0.6" in reasons


def test_isaret_onerilen_kumeden_dusurur():
    ok, reasons = POLICY.evaluate({"speech_ratio": 0.9, "clip_ratio": 0.0}, ["duplicate"])
    assert not ok
    assert reasons == ("isaret:duplicate",)


def test_eksik_olcum_sessizce_gecmez():
    ok, reasons = POLICY.evaluate({"clip_ratio": 0.0}, [])
    assert not ok
    assert "eksik_olcum:speech_ratio" in reasons


def test_allow_missing_esnek_olcume_izin_verir():
    ok, _ = POLICY.evaluate({"speech_ratio": 0.9, "clip_ratio": 0.0}, [])
    assert ok  # dnsmos_ovrl yok ama allow_missing


def test_hicbir_kayit_dusmez():
    records = [
        {"id": "a", "metrics": {"speech_ratio": 0.9, "clip_ratio": 0.0}, "flags": []},
        {"id": "b", "metrics": {"speech_ratio": 0.1, "clip_ratio": 0.9}, "flags": ["oversize"]},
    ]
    out = annotate(records, POLICY)
    assert len(out) == 2
    assert out[0]["recommended"] is True
    assert out[1]["recommended"] is False
    assert out[1]["exclusion_reasons"]
    assert all(r["policy_version"] == "test-1" for r in out)
