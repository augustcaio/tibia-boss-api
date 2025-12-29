"""Parser para extrair dados de Bosses do Wikitext."""

import logging
import re
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
    INFOBOX_CREATURE_TEMPLATE = "Infobox Creature"

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

            # Busca pelo template Infobox Boss ou Infobox Creature
            infobox = cls._find_infobox_boss(wikicode)

            if not infobox:
                raise ParserError(
                    f"Template '{cls.INFOBOX_BOSS_TEMPLATE}' ou '{cls.INFOBOX_CREATURE_TEMPLATE}' não encontrado no wikitext"
                )

            # Extrai os dados do template (já retorna BossModel com image_filename)
            return cls._extract_template_data(infobox, boss_name)

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
            template_name = str(template.name).strip().lower()

            # Verifica se é o template Infobox Boss
            if template_name == cls.INFOBOX_BOSS_TEMPLATE.lower():
                return template

            # Verifica se é o template Infobox Creature (usado para bosses também)
            if template_name == cls.INFOBOX_CREATURE_TEMPLATE.lower():
                # Verifica se é um boss (tem campo isboss = yes)
                for param in template.params:
                    param_name = str(param.name).strip().lower() if param.name else ""
                    if param_name == "isboss":
                        param_value = str(param.value).strip().lower()
                        if param_value == "yes":
                            return template
                # Se não tem isboss, ainda pode ser um boss se tiver campos de boss
                # Aceita de qualquer forma se tiver campos hp/exp
                has_hp_or_exp = False
                for param in template.params:
                    param_name = str(param.name).strip().lower() if param.name else ""
                    if param_name in ("hp", "exp", "hitpoints", "experience", "xp"):
                        has_hp_or_exp = True
                        break
                if has_hp_or_exp:
                    return template

            # Também verifica variações comuns
            if "infobox" in template_name and "boss" in template_name:
                return template

        return None

    @classmethod
    def _clean_wiki_text(cls, text: str) -> Optional[str]:
        """
        Limpa texto do wiki removendo [[links]], links com pipe e tags HTML.
        Ex: "[[Fire]], [[Energy]]" -> "Fire, Energy"
        Ex: "[[Abyssador|The Abyssador]]" -> "The Abyssador"
        """
        if not text:
            return None

        # Remove links do tipo [[Link|Texto]] -> Texto
        text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

        # Remove tags HTML comuns como <br>, <br/>
        text = re.sub(r"<br\s*/?>", ", ", text, flags=re.IGNORECASE)

        # Remove outras tags HTML simples
        text = re.sub(r"<[^>]+>", "", text)

        return text.strip()

    @classmethod
    def _normalize_image_filename(cls, image_value: str) -> str:
        """
        Normaliza o nome do arquivo de imagem removendo prefixos e links.
        Retorna apenas o nome limpo (ex: 'Morgaroth.gif').
        """
        if not image_value:
            return None

        image_value = str(image_value).strip()

        # Remove links do MediaWiki ([[File:Name.gif]] ou [[:File:Name.gif]])
        image_value = image_value.replace("[[", "").replace("]]", "")

        # Remove prefixos comuns
        for prefix in ["File:", "Image:", ":File:", ":Image:"]:
            if image_value.startswith(prefix):
                image_value = image_value[len(prefix) :].strip()

        # Remove parâmetros de formatação (ex: |200px)
        if "|" in image_value:
            image_filename = image_value.split("|")[0].strip()
        else:
            image_filename = image_value.strip()

        return image_filename

    @classmethod
    def _extract_template_data(cls, template, boss_name: Optional[str] = None) -> BossModel:
        """
        Extrai os dados do template Infobox Boss.

        Args:
            template: Template do mwparserfromhell
            boss_name: Nome do boss (fallback)

        Returns:
            Instância de BossModel com os dados extraídos
        """
        data = {
            "name": boss_name or "",
            "hp": None,
            "exp": None,
            "location": None,
            "walks_through": [],
            "elemental_weaknesses": [],
            "elemental_resistances": [],
            "immunities": [],
            "bosstiary_class": None,
            "image_filename": None,
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
            "location": "location",
            "loc": "location",
            "walks through": "walks_through",
            "walksthrough": "walks_through",
            "walks_through": "walks_through",
            "weak to": "elemental_weaknesses",
            "weakness": "elemental_weaknesses",
            "weak": "elemental_weaknesses",
            "strong to": "elemental_resistances",
            "resistance": "elemental_resistances",
            "resistant": "elemental_resistances",
            "immunities": "immunities",
            "immunity": "immunities",
            "immune": "immunities",
            "immune to": "immunities",
            "bosstiaryclass": "bosstiary_class",
            "image": "image",
            "imag": "image",
            "img": "image",
            "picture": "image",
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

                if not param_value:
                    continue

                # Atribui o valor ao campo correspondente
                if field_name == "name":
                    data["name"] = param_value
                elif field_name == "image":
                    # Normaliza o nome do arquivo de imagem
                    image_filename = cls._normalize_image_filename(param_value)
                    data["image_filename"] = image_filename
                elif field_name in ("hp", "exp"):
                    data[field_name] = param_value
                elif field_name == "location":
                    data["location"] = cls._clean_wiki_text(param_value)
                elif field_name == "bosstiary_class":
                    data["bosstiary_class"] = param_value
                elif field_name in (
                    "walks_through",
                    "elemental_weaknesses",
                    "elemental_resistances",
                    "immunities",
                ):
                    clean_val = cls._clean_wiki_text(param_value)
                    if clean_val:
                        # Se já existe valor, adiciona; senão cria lista
                        if not data[field_name]:
                            data[field_name] = clean_val
                        else:
                            # Concatena se já houver valor
                            data[field_name] = f"{data[field_name]}, {clean_val}"

        # Se o nome ainda não foi encontrado, tenta pegar do título da página
        if not data["name"] and boss_name:
            data["name"] = boss_name

        # Processa dados do Bosstiary
        bosstiary_data = None
        boss_class = data.pop("bosstiary_class", None)
        if boss_class:
            kills = None
            bc_lower = boss_class.lower()
            if "nemesis" in bc_lower:
                kills = 5
            elif "archfoe" in bc_lower:
                kills = 60
            elif "bane" in bc_lower:
                kills = 2500

            from app.models.boss import BosstiaryStats

            bosstiary_data = BosstiaryStats(class_name=boss_class, kills_required=kills)

        # Remove image_filename do dict antes de criar o modelo
        image_filename = data.pop("image_filename", None)

        # Cria o modelo
        boss_model = BossModel(**data, bosstiary=bosstiary_data)

        # Adiciona o filename ao modelo se encontrado ou usa fallback baseado no nome
        if not image_filename and data["name"]:
            image_filename = f"{data['name']}.gif"

        if image_filename:
            from app.models.boss import BossVisuals

            boss_model.visuals = BossVisuals(filename=image_filename)

        return boss_model
