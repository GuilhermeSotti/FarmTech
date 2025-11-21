from pathlib import Path
import csv
import logging
import threading

logger = logging.getLogger("data.writer")
_lock = threading.Lock()

HEADER = ["sensor_id", "umidade", "nutriente", "ts"]

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def safe_write_row_csv(path: str, row: dict, header=HEADER):
    """
    Escrita thread-safe em CSV. Cria cabeçalho se não existir.
    """
    p = Path(path)
    ensure_parent(p)
    with _lock:
        try:
            write_header = not p.exists()
            with p.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=header)
                if write_header:
                    writer.writeheader()
                # normaliza: garante as chaves
                out = {k: row.get(k, "") for k in header}
                writer.writerow(out)
        except Exception:
            logger.exception("Falha ao gravar CSV %s", p)
            raise
