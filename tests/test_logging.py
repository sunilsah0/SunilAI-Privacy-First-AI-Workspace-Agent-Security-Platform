import logging
from tests.helpers import client, make_user_info

def test_secrets_do_not_appear_in_logs(caplog):
    caplog.set_level(logging.DEBUG)
    u = make_user_info()
    client.get("/me", headers=u["h"])
    token = u["h"]["Authorization"].split()[1]
    assert "correct-horse-battery" not in caplog.text
    assert token not in caplog.text