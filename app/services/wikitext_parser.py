"""Parser para extrair dados de Bosses do Wikitext."""

import logging
from typing import Optional

import mwparserfromhell

from app.models.boss import BossModel

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Exceção lançada quando o parser não consegue processar o wikitext."""

    pass


class WikitextParser:
    """Parser para extrair dados estruturados de wikitext do TibiaWiki."""

    INFOBOX_BOSS_TEMPLATE = "Infobox Boss"

    @classmethod
    def parse(cls, wikitext: str, boss_name: Optional[str] = None) -> BossModel:
        """
        Parseia o wikitext e retorna um BossModel.

        Args:
            wikitext: String com o conteúdo wikitext
            boss_name: Nome do boss (usado como fallback se não encontrado no template)

        Returns:
            Instância de BossModel com os dados extraídos

        Raises:
            ParserError: Se o template Infobox Boss não for encontrado
        """
        if not wikitext:
            raise ParserError("Wikitext vazio fornecido")

        try:
            # Parse do wikitext usando mwparserfromhell
            wikicode = mwparserfromhell.parse(wikitext)

            # Busca pelo template Infobox Boss
            infobox = cls._find_infobox_boss(wikicode)

            if not infobox:
                raise ParserError(
                    f"Template '{cls.INFOBOX_BOSS_TEMPLATE}' não encontrado no wikitext"
                )

            # Extrai os dados do template
            data = cls._extract_template_data(infobox, boss_name)

            # Cria e retorna o modelo
            return BossModel(**data)

        except mwparserfromhell.parser.ParserError as e:
            logger.error(f"Erro ao fazer parse do wikitext: {e}")
            raise ParserError(f"Erro ao fazer parse do wikitext: {e}") from e
        except Exception as e:
            logger.error(f"Erro inesperado ao processar wikitext: {e}")
            raise ParserError(f"Erro inesperado ao processar wikitext: {e}") from e

    @classmethod
    def _find_infobox_boss(cls, wikicode: mwparserfromhell.wikicode.Wikicode):
        """
        Encontra o template Infobox Boss no wikicode.

        Args:
            wikicode: Objeto Wikicode parseado

        Returns:
            Template encontrado ou None
        """
        templates = wikicode.filter_templates()

        for template in templates:
            # Normaliza o nome do template (remove espaços, case insensitive)
            template_name = str(template.name).strip()

            # Verifica se é o template Infobox Boss
            if template_name.lower() == cls.INFOBOX_BOSS_TEMPLATE.lower():
                return template

            # Também verifica variações comuns
            if "infobox" in template_name.lower() and "boss" in template_name.lower():
                return template

        return None

    @classmethod
    def _extract_template_data(cls, template, boss_name: Optional[str] = None) -> dict:
        """
        Extrai os dados do template Infobox Boss.

        Args:
            template: Template do mwparserfromhell
            boss_name: Nome do boss (fallback)

        Returns:
            Dicionário com os dados extraídos
        """
        data = {
            "name": boss_name or "",
            "hp": None,
            "exp": None,
            "walks_through": [],
            "immunities": [],
        }

        # Mapeia os campos do template para o modelo
        field_mapping = {
            "name": "name",
            "hp": "hp",
            "hitpoints": "hp",
            "health": "hp",
            "exp": "exp",
            "experience": "exp",
            "xp": "exp",
            "walks through": "walks_through",
            "walksthrough": "walks_through",
            "walks_through": "walks_through",
            "immunities": "immunities",
            "immunity": "immunities",
            "immune": "immunities",
        }

        # Extrai o nome do template (pode estar no primeiro parâmetro posicional ou no campo "name")
        if not data["name"]:
            # Primeiro tenta pegar do primeiro parâmetro posicional (sem nome ou com nome numérico)
            for param in template.params:
                param_name_str = str(param.name).strip() if param.name else ""
                # Parâmetros posicionais têm nome numérico ou vazio
                if not param_name_str or param_name_str.isdigit():
                    if param_name_str == "1" or not param_name_str:
                        data["name"] = str(param.value).strip()
                        break

        # Itera pelos parâmetros do template
        for param in template.params:
            param_name = str(param.name).strip().lower() if param.name else ""

            # Verifica se o parâmetro está no mapeamento
            if param_name in field_mapping:
                field_name = field_mapping[param_name]
                param_value = str(param.value).strip()

                # Atribui o valor ao campo correspondente
                if field_name == "name":
                    data["name"] = param_value
                elif field_name in ("hp", "exp"):
                    data[field_name] = param_value
                elif field_name in ("walks_through", "immunities"):
                    # Se já existe valor, adiciona; senão cria lista
                    if not data[field_name]:
                        data[field_name] = param_value
                    else:
                        # Concatena se já houver valor
                        data[field_name] = f"{data[field_name]}, {param_value}"

        # Se o nome ainda não foi encontrado, tenta pegar do título da página
        if not data["name"] and boss_name:
            data["name"] = boss_name

        return data

