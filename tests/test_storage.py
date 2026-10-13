"""Совместимость JSON-хранилища и консольной версии после переноса."""
from core.attractions import Attraction
from core.storage import load_attractions, save_attractions


def test_storage_roundtrip(tmp_path):
    path = tmp_path / "places.json"
    item = Attraction(7, "Парк", "парк", 6, 23, 0)
    save_attractions(path, [item])
    assert load_attractions(path)[0].to_dict() == item.to_dict()


def test_broken_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")
    assert load_attractions(path) == []


def test_console_can_list_and_exit(monkeypatch, capsys):
    from cli.menu import main

    answers = iter(["1", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    main()
    output = capsys.readouterr().out
    assert "До встречи!" in output
    assert "Городской краеведческий музей" in output
