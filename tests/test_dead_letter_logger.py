"""Testes para o Dead Letter Logger."""

import json
import tempfile
from pathlib import Path

import pytest

from app.services.wikitext_parser import ParserError
from app.utils.dead_letter_logger import DeadLetterLogger


@pytest.fixture
def temp_log_file(tmp_path):
    """Fixture para criar um arquivo de log temporário."""
    log_file = tmp_path / "test_parsing_errors.jsonl"
    return log_file


@pytest.fixture
def dead_letter_logger(temp_log_file):
    """Fixture para criar uma instância do logger com arquivo temporário."""
    logger = DeadLetterLogger(log_file=temp_log_file)
    # Limpa o arquivo antes de cada teste
    if temp_log_file.exists():
        temp_log_file.unlink()
    return logger


def test_log_parsing_error_creates_file(dead_letter_logger, temp_log_file):
    """Testa que o log de erro cria o arquivo."""
    error = ParserError("Template não encontrado")
    dead_letter_logger.log_parsing_error(
        boss_name="Test Boss",
        error=error,
        raw_data="Some wikitext content",
    )

    assert temp_log_file.exists()


def test_log_parsing_error_contains_required_fields(dead_letter_logger, temp_log_file):
    """Testa que o log contém todos os campos obrigatórios."""
    error = ParserError("Template não encontrado")
    dead_letter_logger.log_parsing_error(
        boss_name="Morgaroth",
        error=error,
        raw_data="Some wikitext content here",
    )

    # Lê o arquivo de log
    with open(temp_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        log_entry = json.loads(line)

    # Verifica campos obrigatórios
    assert "timestamp" in log_entry
    assert "boss_name" in log_entry
    assert "error_message" in log_entry
    assert "raw_data_snippet" in log_entry

    # Verifica valores
    assert log_entry["boss_name"] == "Morgaroth"
    assert "Template não encontrado" in log_entry["error_message"]


def test_log_parsing_error_truncates_long_snippet(dead_letter_logger, temp_log_file):
    """Testa que snippets longos são truncados para 500 caracteres."""
    long_text = "A" * 1000  # Texto de 1000 caracteres
    error = ParserError("Erro de parsing")

    dead_letter_logger.log_parsing_error(
        boss_name="Test Boss",
        error=error,
        raw_data=long_text,
    )

    with open(temp_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        log_entry = json.loads(line)

    snippet = log_entry["raw_data_snippet"]
    assert len(snippet) == 503  # 500 + "..."
    assert snippet.endswith("...")


def test_log_parsing_error_multiple_entries(dead_letter_logger, temp_log_file):
    """Testa que múltiplas entradas são escritas corretamente."""
    error1 = ParserError("Erro 1")
    error2 = ParserError("Erro 2")

    dead_letter_logger.log_parsing_error("Boss 1", error1, "Data 1")
    dead_letter_logger.log_parsing_error("Boss 2", error2, "Data 2")

    # Lê todas as linhas
    with open(temp_log_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 2

    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert entry1["boss_name"] == "Boss 1"
    assert entry2["boss_name"] == "Boss 2"


def test_log_parsing_error_with_empty_raw_data(dead_letter_logger, temp_log_file):
    """Testa que o log funciona mesmo com raw_data vazio."""
    error = ParserError("Erro sem dados")

    dead_letter_logger.log_parsing_error(
        boss_name="Test Boss",
        error=error,
        raw_data=None,
    )

    with open(temp_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        log_entry = json.loads(line)

    assert log_entry["raw_data_snippet"] == ""


def test_log_image_error(dead_letter_logger, temp_log_file):
    """Testa logging de erro de imagem."""
    error = Exception("Imagem não encontrada")

    dead_letter_logger.log_image_error(
        boss_name="Test Boss",
        error=error,
        image_filename="File:Test.gif",
    )

    with open(temp_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        log_entry = json.loads(line)

    assert log_entry["boss_name"] == "Test Boss"
    assert "Image filename: File:Test.gif" in log_entry["raw_data_snippet"]


def test_get_log_count(dead_letter_logger, temp_log_file):
    """Testa contagem de entradas no log."""
    assert dead_letter_logger.get_log_count() == 0

    dead_letter_logger.log_parsing_error("Boss 1", ParserError("Erro 1"), "Data 1")
    assert dead_letter_logger.get_log_count() == 1

    dead_letter_logger.log_parsing_error("Boss 2", ParserError("Erro 2"), "Data 2")
    assert dead_letter_logger.get_log_count() == 2


def test_clear_logs(dead_letter_logger, temp_log_file):
    """Testa limpeza do arquivo de log."""
    dead_letter_logger.log_parsing_error("Boss 1", ParserError("Erro"), "Data")
    assert temp_log_file.exists()

    dead_letter_logger.clear_logs()
    assert not temp_log_file.exists()


def test_log_parsing_error_with_real_wikitext(dead_letter_logger, temp_log_file):
    """Testa logging com wikitext real (simulando erro proposital)."""
    # Wikitext que causaria erro (sem template Infobox)
    invalid_wikitext = """
    == Description ==
    This is a boss description.
    No Infobox template here.
    """

    error = ParserError("Template 'Infobox Boss' ou 'Infobox Creature' não encontrado no wikitext")

    dead_letter_logger.log_parsing_error(
        boss_name="Test Boss",
        error=error,
        raw_data=invalid_wikitext,
    )

    with open(temp_log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        log_entry = json.loads(line)

    # Verifica que o snippet contém parte do wikitext
    assert "Description" in log_entry["raw_data_snippet"]
    assert len(log_entry["raw_data_snippet"]) <= 503  # Máximo 500 + "..."
    assert log_entry["boss_name"] == "Test Boss"
    assert "Template" in log_entry["error_message"]

