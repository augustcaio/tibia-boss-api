"""Testes unitários para ImageResolverService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.image_resolver import PLACEHOLDER_URL, ImageResolverService


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
def image_resolver():
    """Fixture para criar uma instância do ImageResolverService."""
    return ImageResolverService()


@pytest.mark.asyncio
async def test_resolve_images_single_batch(image_resolver, mock_httpx_response):
    """Testa resolução de imagens em um único lote (< 50)."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "File:Morgaroth.gif",
                    "imageinfo": [{"url": "https://example.com/Morgaroth.gif"}],
                },
                "456": {
                    "pageid": 456,
                    "title": "File:Abyssador.gif",
                    "imageinfo": [{"url": "https://example.com/Abyssador.gif"}],
                },
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(return_value=mock_httpx_response(json_data=mock_data))

        filenames = ["File:Morgaroth.gif", "File:Abyssador.gif"]
        results = await image_resolver.resolve_images(filenames)

        assert len(results) == 2
        assert results["File:Morgaroth.gif"] == "https://example.com/Morgaroth.gif"
        assert results["File:Abyssador.gif"] == "https://example.com/Abyssador.gif"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_images_multiple_batches(image_resolver, mock_httpx_response):
    """Testa resolução de 55 imagens (2 lotes: 50 + 5)."""
    # Cria 55 nomes de arquivos
    filenames = [f"File:Boss{i}.gif" for i in range(55)]

    # Mock para o primeiro lote (50 imagens)
    mock_data_batch1 = {
        "query": {
            "pages": {
                str(i): {
                    "pageid": i,
                    "title": f"File:Boss{i}.gif",
                    "imageinfo": [{"url": f"https://example.com/Boss{i}.gif"}],
                }
                for i in range(50)
            }
        }
    }

    # Mock para o segundo lote (5 imagens)
    mock_data_batch2 = {
        "query": {
            "pages": {
                str(i): {
                    "pageid": i,
                    "title": f"File:Boss{i}.gif",
                    "imageinfo": [{"url": f"https://example.com/Boss{i}.gif"}],
                }
                for i in range(50, 55)
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(
            side_effect=[
                mock_httpx_response(json_data=mock_data_batch1),
                mock_httpx_response(json_data=mock_data_batch2),
            ]
        )

        results = await image_resolver.resolve_images(filenames)

        # Verifica que foram feitos 2 requests
        assert mock_client.post.call_count == 2

        # Verifica que todas as 55 imagens foram resolvidas
        assert len(results) == 55

        # Verifica algumas URLs
        assert results["File:Boss0.gif"] == "https://example.com/Boss0.gif"
        assert results["File:Boss54.gif"] == "https://example.com/Boss54.gif"


@pytest.mark.asyncio
async def test_resolve_images_missing_image(image_resolver, mock_httpx_response):
    """Testa que imagens não encontradas recebem placeholder."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "File:Morgaroth.gif",
                    "imageinfo": [{"url": "https://example.com/Morgaroth.gif"}],
                },
                "456": {
                    "pageid": 456,
                    "title": "File:Missing.gif",
                    "missing": True,
                },
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(return_value=mock_httpx_response(json_data=mock_data))

        filenames = ["File:Morgaroth.gif", "File:Missing.gif"]
        results = await image_resolver.resolve_images(filenames)

        assert results["File:Morgaroth.gif"] == "https://example.com/Morgaroth.gif"
        assert results["File:Missing.gif"] == PLACEHOLDER_URL


@pytest.mark.asyncio
async def test_resolve_images_empty_imageinfo(image_resolver, mock_httpx_response):
    """Testa que imagens com imageinfo vazio recebem placeholder."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "File:NoImageInfo.gif",
                    "imageinfo": [],
                }
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(return_value=mock_httpx_response(json_data=mock_data))

        filenames = ["File:NoImageInfo.gif"]
        results = await image_resolver.resolve_images(filenames)

        assert results["File:NoImageInfo.gif"] == PLACEHOLDER_URL


@pytest.mark.asyncio
async def test_resolve_images_http_error(image_resolver, mock_httpx_response):
    """Testa que erros HTTP não fazem o sistema crashar."""
    from httpx import HTTPStatusError

    error_response = MagicMock()
    error_response.status_code = 500
    http_error = HTTPStatusError(
        "Internal Server Error", request=MagicMock(), response=error_response
    )

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(side_effect=http_error)

        filenames = ["File:Error.gif"]
        results = await image_resolver.resolve_images(filenames)

        # Sistema não crashou, atribuiu placeholder
        assert results["File:Error.gif"] == PLACEHOLDER_URL


@pytest.mark.asyncio
async def test_resolve_images_general_exception(image_resolver):
    """Testa que exceções gerais não fazem o sistema crashar."""
    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(side_effect=Exception("Erro inesperado"))

        filenames = ["File:Exception.gif"]
        results = await image_resolver.resolve_images(filenames)

        # Sistema não crashou, atribuiu placeholder
        assert results["File:Exception.gif"] == PLACEHOLDER_URL


@pytest.mark.asyncio
async def test_resolve_images_empty_list(image_resolver):
    """Testa resolução de lista vazia."""
    results = await image_resolver.resolve_images([])
    assert results == {}


@pytest.mark.asyncio
async def test_resolve_images_duplicates(image_resolver, mock_httpx_response):
    """Testa que duplicatas são removidas antes do processamento."""
    mock_data = {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": "File:Duplicate.gif",
                    "imageinfo": [{"url": "https://example.com/Duplicate.gif"}],
                }
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(return_value=mock_httpx_response(json_data=mock_data))

        # Lista com duplicatas
        filenames = ["File:Duplicate.gif", "File:Duplicate.gif", "File:Duplicate.gif"]
        results = await image_resolver.resolve_images(filenames)

        # Deve fazer apenas 1 request (duplicatas removidas)
        assert mock_client.post.call_count == 1
        assert len(results) == 1
        assert results["File:Duplicate.gif"] == "https://example.com/Duplicate.gif"


@pytest.mark.asyncio
async def test_resolve_images_uses_post_not_get(image_resolver, mock_httpx_response):
    """Testa que a requisição usa POST e não GET."""
    mock_data = {"query": {"pages": {}}}

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(return_value=mock_httpx_response(json_data=mock_data))

        filenames = ["File:Test.gif"]
        await image_resolver.resolve_images(filenames)

        # Verifica que foi usado POST
        mock_client.post.assert_called_once()
        # Verifica que não foi usado GET
        assert not hasattr(mock_client, "get") or mock_client.get.call_count == 0


@pytest.mark.asyncio
async def test_resolve_images_batch_error_does_not_crash(image_resolver, mock_httpx_response):
    """Testa que erro em um lote não impede o processamento dos outros."""
    # Primeiro lote com erro
    from httpx import HTTPStatusError

    error_response = MagicMock()
    error_response.status_code = 500
    http_error = HTTPStatusError(
        "Internal Server Error", request=MagicMock(), response=error_response
    )

    # Segundo lote com sucesso (5 imagens)
    mock_data_batch2 = {
        "query": {
            "pages": {
                str(i): {
                    "pageid": i,
                    "title": f"File:Boss{i}.gif",
                    "imageinfo": [{"url": f"https://example.com/Boss{i}.gif"}],
                }
                for i in range(50, 55)
            }
        }
    }

    with patch.object(image_resolver, "_client", new_callable=AsyncMock) as mock_client:
        mock_client.post = AsyncMock(
            side_effect=[
                http_error,  # Primeiro lote falha
                mock_httpx_response(json_data=mock_data_batch2),  # Segundo lote sucesso
            ]
        )

        # 55 imagens (2 lotes)
        filenames = [f"File:Boss{i}.gif" for i in range(55)]
        results = await image_resolver.resolve_images(filenames)

        # Sistema não crashou
        assert len(results) == 55

        # Primeiro lote recebeu placeholders
        for i in range(50):
            assert results[f"File:Boss{i}.gif"] == PLACEHOLDER_URL

        # Segundo lote foi resolvido corretamente
        for i in range(50, 55):
            assert results[f"File:Boss{i}.gif"] == f"https://example.com/Boss{i}.gif"
