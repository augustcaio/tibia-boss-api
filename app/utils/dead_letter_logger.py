"""Sistema de Dead Letter Logging para erros de parsing e processamento."""

import json
import logging
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Configuração
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "parsing_errors.jsonl"
MAX_SNIPPET_LENGTH = 500


class DeadLetterLogger:
    """Logger estruturado para erros de parsing e processamento."""

    def __init__(self, log_file: Path = LOG_FILE):
        """
        Inicializa o Dead Letter Logger.

        Args:
            log_file: Caminho do arquivo de log (padrão: logs/parsing_errors.jsonl)
        """
        self.log_file = log_file
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Garante que o diretório de logs existe."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_traceback_summary(self, exception: Exception) -> str:
        """
        Extrai um resumo do traceback.

        Args:
            exception: Exceção capturada

        Returns:
            String com resumo do traceback (últimas 3 linhas)
        """
        try:
            tb_lines = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
            # Pega as últimas 3 linhas do traceback
            summary = "".join(tb_lines[-3:]).strip()
            return summary
        except Exception:
            return str(exception)

    def _truncate_snippet(self, text: str, max_length: int = MAX_SNIPPET_LENGTH) -> str:
        """
        Trunca o texto para o tamanho máximo especificado.

        Args:
            text: Texto a ser truncado
            max_length: Tamanho máximo (padrão: 500)

        Returns:
            Texto truncado
        """
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[:max_length] + "..."

    def log_parsing_error(
        self,
        boss_name: str,
        error: Exception,
        raw_data: Optional[str] = None,
    ):
        """
        Registra um erro de parsing no arquivo de log.

        Args:
            boss_name: Nome do boss que causou o erro
            error: Exceção capturada
            raw_data: Dados brutos que causaram o erro (wikitext, etc.)
        """
        try:
            # Prepara o registro estruturado
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "boss_name": boss_name,
                "error_message": self._get_traceback_summary(error),
                "raw_data_snippet": self._truncate_snippet(raw_data or ""),
            }

            # Escreve no arquivo JSONL (uma linha JSON por entrada)
            with open(self.log_file, "a", encoding="utf-8") as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write("\n")

            logger.debug(f"Erro de parsing logado para {boss_name}")

        except Exception as e:
            # Se falhar ao escrever o log, registra no logger padrão
            logger.error(f"Erro ao escrever dead letter log: {e}")

    def log_image_error(
        self,
        boss_name: str,
        error: Exception,
        image_filename: Optional[str] = None,
    ):
        """
        Registra um erro de resolução de imagem.

        Args:
            boss_name: Nome do boss
            error: Exceção capturada
            image_filename: Nome do arquivo de imagem que causou o erro
        """
        try:
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "boss_name": boss_name,
                "error_message": self._get_traceback_summary(error),
                "raw_data_snippet": f"Image filename: {image_filename or 'unknown'}",
            }

            with open(self.log_file, "a", encoding="utf-8") as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write("\n")

            logger.debug(f"Erro de imagem logado para {boss_name}")

        except Exception as e:
            logger.error(f"Erro ao escrever dead letter log: {e}")

    def get_log_count(self) -> int:
        """
        Retorna o número de entradas no arquivo de log.

        Returns:
            Número de linhas no arquivo de log
        """
        try:
            if not self.log_file.exists():
                return 0

            with open(self.log_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())

        except Exception as e:
            logger.error(f"Erro ao contar entradas no log: {e}")
            return 0

    def clear_logs(self):
        """Limpa o arquivo de log (útil para testes)."""
        try:
            if self.log_file.exists():
                self.log_file.unlink()
        except Exception as e:
            logger.error(f"Erro ao limpar log: {e}")


# Instância global do logger
dead_letter_logger = DeadLetterLogger()
