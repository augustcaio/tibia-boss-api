"""Cliente assíncrono para comunicação com a API do TibiaWiki."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class TibiaWikiClient:
    """Cliente assíncrono para interagir com a API do TibiaWiki."""

    BASE_URL = "https://tibia.fandom.com/api.php"
    USER_AGENT = "TibiaBossApiBot/0.1 (contato@seuexemplo.com)"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1  # segundos

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Inicializa o cliente TibiaWiki.

        Args:
            base_url: URL base da API (padrão: BASE_URL)
            timeout: Timeout para requisições HTTP em segundos
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

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
                headers={"User-Agent": self.USER_AGENT},
                timeout=self.timeout,
            )

    async def close(self):
        """Fecha o cliente HTTP."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request_with_backoff(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Faz uma requisição HTTP com exponential backoff para erros 429.

        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL da requisição
            **kwargs: Argumentos adicionais para httpx

        Returns:
            Resposta HTTP

        Raises:
            httpx.HTTPStatusError: Se a requisição falhar após todas as tentativas
        """
        await self._ensure_client()
        backoff = self.INITIAL_BACKOFF

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = backoff * (2**attempt)
                        logger.warning(
                            f"Rate limit (429) atingido. Aguardando {wait_time}s antes de tentar novamente..."
                        )
                        await asyncio.sleep(wait_time)
                        backoff = wait_time
                        continue
                    else:
                        logger.error(f"Rate limit (429) após {self.MAX_RETRIES} tentativas")
                        raise
                else:
                    raise
            except httpx.RequestError as e:
                logger.error(f"Erro na requisição: {e}")
                raise

    async def get_all_bosses(self) -> List[Dict[str, Any]]:
        """
        Busca todos os bosses da categoria Category:Bosses.

        Lida automaticamente com paginação usando cmcontinue.

        Returns:
            Lista de dicionários contendo informações dos bosses (pageid, title, etc.)
        """
        all_bosses = []
        cmcontinue = None

        while True:
            params: Dict[str, Any] = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": "Category:Bosses",
                "cmlimit": 500,
                "cmnamespace": 0,  # Apenas artigos principais (ignora arquivos, categorias, etc.)
                "cmtype": "page",  # Garante que só pega páginas
                "format": "json",
            }

            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            logger.info(f"Buscando bosses... (já encontrados: {len(all_bosses)})")

            response = await self._request_with_backoff("GET", "", params=params)
            data = response.json()

            query = data.get("query", {})
            categorymembers = query.get("categorymembers", [])
            all_bosses.extend(categorymembers)

            # Verifica se há mais páginas
            if "continue" in data:
                cmcontinue = data["continue"].get("cmcontinue")
                if not cmcontinue:
                    break
            else:
                break

        logger.info(f"Total de bosses encontrados: {len(all_bosses)}")
        return all_bosses

    async def get_boss_wikitext(
        self, pageid: Optional[int] = None, title: Optional[str] = None
    ) -> Optional[str]:
        """
        Busca o conteúdo wikitext de uma página de boss.

        Args:
            pageid: ID da página (prioritário se fornecido)
            title: Título da página (usado se pageid não fornecido)

        Returns:
            String com o conteúdo wikitext ou None se não encontrado

        Raises:
            ValueError: Se nem pageid nem title forem fornecidos
        """
        if not pageid and not title:
            raise ValueError("Deve fornecer pageid ou title")

        params: Dict[str, Any] = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
        }

        if pageid:
            params["pageids"] = pageid
        else:
            params["titles"] = title

        logger.debug(f"Buscando wikitext para: pageid={pageid}, title={title}")

        response = await self._request_with_backoff("GET", "", params=params)
        data = response.json()

        query = data.get("query", {})
        pages = query.get("pages", {})

        # Se usou pageid, busca pela chave do pageid
        if pageid:
            page_data = pages.get(str(pageid))
        else:
            # Se usou title, precisa encontrar a chave da página
            page_data = None
            for page_key, page_info in pages.items():
                if page_info.get("title") == title:
                    page_data = page_info
                    break

        if not page_data:
            logger.warning(f"Página não encontrada: pageid={pageid}, title={title}")
            return None

        # Verifica se a página foi encontrada mas está vazia (página não existe)
        if "missing" in page_data:
            logger.warning(f"Página não existe: pageid={pageid}, title={title}")
            return None

        revisions = page_data.get("revisions", [])
        if not revisions:
            logger.warning(f"Nenhuma revisão encontrada: pageid={pageid}, title={title}")
            return None

        content = revisions[0].get("slots", {}).get("main", {}).get("*")
        return content
