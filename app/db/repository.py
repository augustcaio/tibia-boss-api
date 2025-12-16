"""Repositório MongoDB para operações de persistência de Bosses."""

import logging
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.boss import BossModel

logger = logging.getLogger(__name__)


class BossRepository:
    """Repositório para operações de persistência de Bosses no MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Inicializa o repositório.

        Args:
            database: Instância do AsyncIOMotorDatabase
        """
        self.db = database
        self.collection = database.bosses

    async def upsert(self, boss: BossModel) -> bool:
        """
        Insere ou atualiza um boss no banco de dados usando slug como chave.

        Args:
            boss: Instância de BossModel

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Gera o slug se não fornecido
            slug = boss.slug or boss.get_slug()

            # Converte o modelo para dict
            boss_dict = boss.model_dump(exclude={"slug"})
            boss_dict["slug"] = slug

            # Usa find_one_and_update com upsert=True
            result = await self.collection.find_one_and_update(
                {"slug": slug},
                {"$set": boss_dict},
                upsert=True,
                return_document=True,
            )

            if result:
                logger.debug(f"Boss upserted: {boss.name} (slug: {slug})")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao fazer upsert do boss {boss.name}: {e}")
            return False

    async def upsert_batch(self, bosses: List[BossModel]) -> int:
        """
        Insere ou atualiza múltiplos bosses em lote.

        Args:
            bosses: Lista de instâncias de BossModel

        Returns:
            Número de bosses processados com sucesso
        """
        if not bosses:
            return 0

        success_count = 0

        # Processa cada boss individualmente (pode ser otimizado com bulk_write no futuro)
        for boss in bosses:
            if await self.upsert(boss):
                success_count += 1

        logger.info(f"Batch upsert: {success_count}/{len(bosses)} bosses processados")
        return success_count

    async def find_by_slug(self, slug: str) -> Optional[BossModel]:
        """
        Busca um boss pelo slug.

        Args:
            slug: Slug do boss

        Returns:
            Instância de BossModel ou None se não encontrado
        """
        try:
            document = await self.collection.find_one({"slug": slug})

            if document:
                # Remove o _id do MongoDB antes de criar o modelo
                document.pop("_id", None)
                return BossModel(**document)

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar boss por slug {slug}: {e}")
            return None

    async def find_by_name(self, name: str) -> Optional[BossModel]:
        """
        Busca um boss pelo nome.

        Args:
            name: Nome do boss

        Returns:
            Instância de BossModel ou None se não encontrado
        """
        try:
            document = await self.collection.find_one({"name": name})

            if document:
                document.pop("_id", None)
                return BossModel(**document)

            return None

        except Exception as e:
            logger.error(f"Erro ao buscar boss por nome {name}: {e}")
            return None

    async def count(self) -> int:
        """
        Retorna o número total de bosses no banco.

        Returns:
            Número total de documentos
        """
        try:
            return await self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Erro ao contar bosses: {e}")
            return 0

    async def list_bosses(self, skip: int = 0, limit: int = 20) -> List[BossModel]:
        """
        Lista bosses com paginação usando projection para otimizar.

        Args:
            skip: Número de documentos a pular
            limit: Número máximo de documentos a retornar

        Returns:
            Lista de instâncias de BossModel (apenas campos essenciais)
        """
        try:
            # Projection: retorna apenas os campos necessários para listagem
            # Não retorna raw_wikitext ou outros campos pesados
            projection = {
                "name": 1,
                "slug": 1,
                "visuals": 1,
                "hp": 1,
                "_id": 0,  # Exclui _id do MongoDB
            }

            cursor = self.collection.find({}, projection).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)

            # Converte documentos para BossModel
            bosses = []
            for doc in documents:
                try:
                    boss = BossModel(**doc)
                    bosses.append(boss)
                except Exception as e:
                    logger.warning(f"Erro ao converter documento para BossModel: {e}")
                    continue

            return bosses

        except Exception as e:
            logger.error(f"Erro ao listar bosses: {e}")
            return []

