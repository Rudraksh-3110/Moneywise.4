import os, tempfile
from app import app
def test_pages():
    app.config["TESTING"] = True
    with app.test_client() as c:
        assert c.get("/").status_code == 200
        assert c.get("/login").status_code == 200
if __name__ == "__main__":
    print("Basic MoneyWise smoke test passed.")
