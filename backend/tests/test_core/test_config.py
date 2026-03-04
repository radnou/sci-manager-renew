from app.core.config import Settings


def test_parse_cors_origins_json_list():
    config = Settings(cors_origins='["http://localhost:5173", "https://app.test"]')
    assert config.cors_origins == ["http://localhost:5173", "https://app.test"]


def test_parse_cors_origins_csv():
    config = Settings(cors_origins="http://localhost:5173,https://app.test")
    assert config.cors_origins == ["http://localhost:5173", "https://app.test"]
