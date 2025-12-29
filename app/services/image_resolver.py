"""Serviço para resolver URLs de imagens do TibiaWiki usando Batch Strategy."""

import logging
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

# Constantes
BATCH_SIZE = 50
PLACEHOLDER_URL = "static/placeholder_boss.png"
BASE_URL = "https://tibia.fandom.com/api.php"
USER_AGENT = "TibiaBossApiBot/0.1 (contato@seuexemplo.com)"


class ImageResolverService:
    """Serviço para resolver URLs de imagens em lote usando a API do TibiaWiki."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0):
        """
        Inicializa o serviço de resolução de imagens.

        Args:
            base_url: URL base da API (padrão: BASE_URL)
            timeout: Timeout para requisições HTTP em segundos
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Garante que o cliente HTTP está inicializado."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
            )

    async def close(self):
        """Fecha o cliente HTTP."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _chunk_list(self, items: List[str], chunk_size: int) -> List[List[str]]:
        """
        Divide uma lista em chunks de tamanho específico.

        Args:
            items: Lista de itens para dividir
            chunk_size: Tamanho de cada chunk

        Returns:
            Lista de chunks
        """
        return [items[i: i + chunk_size] for i in range(0, len(items), chunk_size)]

    async def _resolve_batch(self, filenames: List[str]) -> Dict[str, str]:
        """
        Resolve URLs para um lote de nomes de arquivos.

        Args:
            filenames: Lista de nomes de arquivos (ex: ["File:Morgaroth.gif"])

        Returns:
            Dicionário mapeando filename -> url
        """
        if not filenames:
            return {}

        await self._ensure_client()

        # Prepara os títulos separados por pipe (|)
        titles = "|".join(filenames)

        # Parâmetros da API
        params = {
            "action": "query",
            "titles": titles,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
            "redirects": "1",
        }

        result: Dict[str, str] = {}

        try:
            # Faz POST request com os parâmetros no body (não na URL)
            # Isso evita erro de URI Too Long
            response = await self._client.post("", data=params)
            response.raise_for_status()

            data = response.json()

            # Extrai as URLs das imagens
            query = data.get("query", {})
            pages = query.get("pages", {})
            redirects = query.get("redirects", [])

            # Mapa de redirecionamentos: from -> to
            redirect_map = {r["from"]: r["to"] for r in redirects}

            # Primeiro, mapeia as URLs encontradas nas páginas para seus títulos
            url_map = {}
            for _, page_data in pages.items():
                title = page_data.get("title", "")
                imageinfo = page_data.get("imageinfo", [])

                if imageinfo and len(imageinfo) > 0:
                    url = imageinfo[0].get("url")
                    if url:
                        url_map[title] = url

            # Para cada filename original, busca a URL (diretamente ou via redirect)
            for original_filename in filenames:
                # Se houver redirecionamento, usa o título de destino
                target_title = redirect_map.get(
                    original_filename, original_filename)

                url = url_map.get(target_title)
                if url:
                    result[original_filename] = url
                else:
                    result[original_filename] = PLACEHOLDER_URL
                    logger.warning(
                        "Imagem não encontrada: %s (target: %s), usando placeholder", original_filename, target_title)

        except httpx.HTTPStatusError as e:
            logger.error("Erro HTTP ao resolver imagens: %s", e)
            # Em caso de erro, atribui placeholder para todas as imagens do lote
            for filename in filenames:
                result[filename] = PLACEHOLDER_URL
        except Exception as e:
            logger.error("Erro inesperado ao resolver imagens: %s", e)
            # Em caso de erro, atribui placeholder para todas as imagens do lote
            for filename in filenames:
                result[filename] = PLACEHOLDER_URL

        return result

    async def resolve_images(self, filenames: List[str]) -> Dict[str, str]:
        """
        Resolve URLs para uma lista de nomes de arquivos usando batch strategy.

        Agrupa os nomes em lotes de 50 e faz requisições POST para evitar
        erro de URI Too Long.

        Args:
            filenames: Lista de nomes de arquivos (ex: ["File:Morgaroth.gif", "File:Abyssador.gif"])

        Returns:
            Dicionário mapeando filename -> url. Se uma imagem não for encontrada,
            será atribuído o placeholder.

        Example:
            >>> resolver = ImageResolverService()
            >>> urls = await resolver.resolve_images(["File:Morgaroth.gif", "File:Abyssador.gif"])
            >>> print(urls["File:Morgaroth.gif"])
            https://static.wikia.nocookie.net/tibia/images/...
        """
        if not filenames:
            return {}

        # Remove duplicatas mantendo a ordem
        unique_filenames = list(dict.fromkeys(filenames))

        # Divide em chunks de BATCH_SIZE
        chunks = self._chunk_list(unique_filenames, BATCH_SIZE)

        logger.info("Resolvendo %d imagens em %d lote(s)",
                    len(unique_filenames), len(chunks))

        # Processa cada chunk
        all_results: Dict[str, str] = {}

        for i, chunk in enumerate(chunks, 1):
            logger.debug("Processando lote %d/%d (%d imagens)",
                         i, len(chunks), len(chunk))

            try:
                batch_results = await self._resolve_batch(chunk)
                all_results.update(batch_results)
            except Exception as e:
                logger.error("Erro ao processar lote %d: %s", i, e)
                # Em caso de erro no lote, atribui placeholder para todas as imagens do lote
                for filename in chunk:
                    all_results[filename] = PLACEHOLDER_URL

        # Garante que todas as imagens solicitadas tenham uma URL (placeholder se necessário)
        for filename in unique_filenames:
            if filename not in all_results:
                all_results[filename] = PLACEHOLDER_URL
                logger.warning(
                    "Imagem %s não foi resolvida, usando placeholder", filename)

        logger.info("Resolução concluída: %d URLs obtidas", len(all_results))
        return all_results
