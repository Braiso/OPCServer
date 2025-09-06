# Uso de logs en Python con `logging`

El módulo `logging` en Python permite manejar mensajes con distintos **niveles de severidad**.

## 🔹 Niveles de log

| Nivel       | Valor numérico |
|-------------|----------------|
| `DEBUG`     | 10             |
| `INFO`      | 20             |
| `WARNING`   | 30             |
| `ERROR`     | 40             |
| `CRITICAL`  | 50             |

Cuando configuras:

```python
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
```

Esto significa: **"muéstrame todos los mensajes de nivel `DEBUG` y superiores"**.

Por eso, si eliges `DEBUG`, también aparecen `INFO`, `WARNING`, `ERROR` y `CRITICAL`.

---

## 🔹 Filtrar solo mensajes `DEBUG`

### Opción 1: Usar un filtro personalizado

```python
import logging

class OnlyDebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
handler.addFilter(OnlyDebugFilter())  # Solo permite DEBUG

logger.addHandler(handler)

logger.debug("Esto es debug")       # ✅ se muestra
logger.info("Esto es info")         # ❌ no se muestra
logger.warning("Esto es warning")   # ❌ no se muestra
```

### Opción 2: Logger separado para DEBUG

```python
import logging

debug_logger = logging.getLogger("debug_logger")
debug_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
debug_logger.addHandler(handler)

debug_logger.debug("Mensaje de depuración")
```

---

## 🔹 Filtrar categorías (loggers por nombre)

````mermaid
graph LR
    A[DEBUG - 10] --> B[INFO - 20]
    B --> C[WARNING - 30]
    C --> D[ERROR - 40]
    D --> E[CRITICAL - 50]
````

Cada **logger** en Python tiene un nombre (ej. `"app.db"`, `"app.api"`).  
Puedes configurar filtros para mostrar solo ciertas categorías:

```python
import logging

# Logger principal
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

# Handler con filtro por nombre de logger
class CategoryFilter(logging.Filter):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def filter(self, record):
        return record.name.startswith(self.name)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
handler.addFilter(CategoryFilter("app.db"))  # solo logs de app.db

logger.addHandler(handler)

# Ejemplos
db_logger = logging.getLogger("app.db")
api_logger = logging.getLogger("app.api")

db_logger.debug("Consulta ejecutada")   # ✅ se muestra
api_logger.debug("Petición recibida")   # ❌ no se muestra
```

---

✅ **Resumen**:
- `level` establece el **mínimo nivel** que se muestra.  
- Para mostrar solo `DEBUG`, necesitas filtros.  
- También puedes filtrar por **categoría (nombre de logger)**.
