"""Testes unitários para TibiaWikiClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tibiawiki_client import TibiaWikiClient


@pytest.fixture
def mock_httpx_response():
    """Fixture para criar respostas mockadas do httpx."""

    def _create_response(status_code=200, json_data=None):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.raise_for_status = MagicMock()
        return response

    return _create_response


@pytest.fixture
def tibiawiki_client():
    """Fixture para criar uma instância do TibiaWikiClient."""
    return TibiaWikiClient()


@pytest.mark.asyncio
async def test_get_all_bosses_single_page(tibiawiki_client, mock_httpx_response):
    """Testa get_all_bosses() quando há apenas uma página de resultados."""
    mock_data = {
        "query": {
            "categorymembers": [
                {"pageid": 1, "title": "Boss 1"},
                {"pageid": 2, "title": "Boss 2"},
            ]
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_httpx_response(json_data=mock_data)

        bosses = await tibiawiki_client.get_all_bosses()

        assert len(bosses) == 2
        assert bosses[0]["title"] == "Boss 1"
        assert bosses[1]["title"] == "Boss 2"
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_bosses_with_pagination(tibiawiki_client, mock_httpx_response):
    """Testa get_all_bosses() com paginação (cmcontinue)."""
    # Primeira página
    mock_data_page1 = {
        "query": {
            "categorymembers": [
                {"pageid": 1, "title": "Boss 1"},
                {"pageid": 2, "title": "Boss 2"},
            ]
        },
        "continue": {"cmcontinue": "next_page_token"},
    }

    # Segunda página (última)
    mock_data_page2 = {
        "query": {
            "categorymembers": [
                {"pageid": 3, "title": "Boss 3"},
            ]
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.side_effect = [
            mock_httpx_response(json_data=mock_data_page1),
            mock_httpx_response(json_data=mock_data_page2),
        ]

        bosses = await tibiawiki_client.get_all_bosses()

        assert len(bosses) == 3
        assert bosses[0]["title"] == "Boss 1"
        assert bosses[2]["title"] == "Boss 3"
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_get_boss_wikitext_by_pageid(tibiawiki_client, mock_httpx_response):
    """Testa get_boss_wikitext() usando pageid."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "Test Boss",
                    "revisions": [
                        {"slots": {"main": {"*": "{{Infobox Boss|hp=50000|exp=10000}}"}}}
                    ],
                }
            }
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_httpx_response(json_data=mock_data)

        wikitext = await tibiawiki_client.get_boss_wikitext(pageid=123)

        assert wikitext == "{{Infobox Boss|hp=50000|exp=10000}}"
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_boss_wikitext_by_title(tibiawiki_client, mock_httpx_response):
    """Testa get_boss_wikitext() usando title."""
    mock_data = {
        "query": {
            "pages": {
                "456": {
                    "pageid": 456,
                    "title": "Test Boss",
                    "revisions": [{"slots": {"main": {"*": "{{Infobox Boss|hp=30000}}"}}}],
                }
            }
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_httpx_response(json_data=mock_data)

        wikitext = await tibiawiki_client.get_boss_wikitext(title="Test Boss")

        assert wikitext == "{{Infobox Boss|hp=30000}}"
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_boss_wikitext_missing_page(tibiawiki_client, mock_httpx_response):
    """Testa get_boss_wikitext() quando a página não existe."""
    mock_data = {
        "query": {
            "pages": {
                "999": {
                    "pageid": 999,
                    "title": "Non-existent Boss",
                    "missing": True,
                }
            }
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_httpx_response(json_data=mock_data)

        wikitext = await tibiawiki_client.get_boss_wikitext(pageid=999)

        assert wikitext is None


@pytest.mark.asyncio
async def test_get_boss_wikitext_no_revisions(tibiawiki_client, mock_httpx_response):
    """Testa get_boss_wikitext() quando não há revisões."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "Test Boss",
                    "revisions": [],
                }
            }
        }
    }

    with patch.object(
        tibiawiki_client, "_request_with_backoff", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_httpx_response(json_data=mock_data)

        wikitext = await tibiawiki_client.get_boss_wikitext(pageid=123)

        assert wikitext is None


@pytest.mark.asyncio
async def test_get_boss_wikitext_raises_without_params(tibiawiki_client):
    """Testa que get_boss_wikitext() levanta ValueError sem pageid ou title."""
    with pytest.raises(ValueError, match="Deve fornecer pageid ou title"):
        await tibiawiki_client.get_boss_wikitext()


@pytest.mark.asyncio
async def test_exponential_backoff_on_429(tibiawiki_client, mock_httpx_response):
    """Testa exponential backoff para erros 429."""
    from httpx import HTTPStatusError

    # Primeira tentativa: 429, Segunda tentativa: sucesso
    error_response = MagicMock()
    error_response.status_code = 429
    error_response.raise_for_status = MagicMock(
        side_effect=HTTPStatusError("Rate limited", request=MagicMock(), response=error_response)
    )

    success_response = mock_httpx_response(
        json_data={"query": {"categorymembers": [{"pageid": 1, "title": "Boss 1"}]}}
    )

    # Mock do cliente HTTP interno
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=[error_response, success_response])

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        tibiawiki_client._client = mock_client

        bosses = await tibiawiki_client.get_all_bosses()

        assert len(bosses) == 1
        # Verifica que sleep foi chamado (backoff)
        assert mock_sleep.called
        # Verifica que houve 2 tentativas (1 erro + 1 sucesso)
        assert mock_client.request.call_count == 2


@pytest.mark.asyncio
async def test_context_manager(tibiawiki_client):
    """Testa uso do cliente como context manager."""
    async with TibiaWikiClient() as client:
        assert client._client is not None

    # Após sair do context, cliente deve estar fechado
    assert tibiawiki_client._client is None or tibiawiki_client._client.is_closed
