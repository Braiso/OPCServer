# Invariantes comunes en desarrollo de software

## 1. Invariantes de objeto
- Atributos de configuración (ej. `endpoint_url`) son inmutables tras `__init__`.
- `is_connected == (self.client is not None)`.
- Tras `__enter__` → `is_connected` debe ser `True`.
- Tras `__exit__` → `is_connected` debe ser `False`.

## 2. Invariantes de métodos (contratos)
- `connect()`:
  - Si ya está conectado, no crea nueva sesión.
  - Éxito ⇒ `is_connected == True`.
  - Fallo ⇒ lanza excepción y `self.client is None`.
- `disconnect()`:
  - Siempre termina con `self.client is None` (idempotente).
- `read_node()` / `write_node()`:
  - Requieren `is_connected == True`.
  - Ante error ⇒ lanzan excepción específica (`NodeReadError`, `NodeWriteError`).

## 3. Invariantes de errores/excepciones
- Todos los fallos se materializan como subclases de `OpcClientError`.
- Excepciones propias siempre contienen la excepción original en `original`.
- Se utiliza `raise ... from exc` para mantener el traceback encadenado.

## 4. Invariantes de logging
- Conexión y desconexión generan al menos un log `INFO`.
- Reintentos de conexión → `WARNING`.
- Fallo final → `ERROR`.
- No duplicar `handlers` en configuración de logging.

## 5. Invariantes de recursos
- Nunca dejar sockets abiertos tras un fallo.
- `disconnect()` puede llamarse varias veces sin error.
- Tras cualquier excepción en `connect()`, el objeto vuelve a estado limpio.

## 6. Invariantes de concurrencia
- Callbacks no hacen trabajo pesado.
- Si se usa en entornos multihilo, acceso a `self.client` protegido con lock.

## 7. Invariantes de entrada
- `nodeid` siempre debe ser `str` válido y no vacío.
- Si se usan alias de nodos, deben existir en el diccionario de configuración.
