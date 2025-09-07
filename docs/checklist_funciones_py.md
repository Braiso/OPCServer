# Checklist para diseño de funciones en Python

## 1. Definición básica
- [ ] **Nombre descriptivo** (usa verbos si es acción, sustantivos si devuelve datos).
- [ ] **Propósito claro** de la función.

## 2. Contrato
- [ ] **Precondiciones** (qué debe cumplirse antes de llamar a la función).
- [ ] **Parámetros de entrada** (tipos, restricciones, valores por defecto).
- [ ] **Parámetros de salida / valor de retorno** (qué devuelve y en qué formato).
- [ ] **Postcondiciones** (qué garantiza después de ejecutarse).
- [ ] **Posibles errores / excepciones** documentados.

## 3. Documentación
- [ ] Docstring redactado (PEP 257 / NumPy / Sphinx).
- [ ] Ejemplos de uso incluidos en la docstring si es útil.

## 4. Diseño y lógica
- [ ] Pseudocódigo redactado o **diagrama de flujo**.
- [ ] Revisar si modifica **argumentos mutables** (listas, dicts).

## 5. Calidad y buenas prácticas
- [ ] Reusabilidad: ¿se puede generalizar?
- [ ] Extensibilidad: ¿es fácil ampliar sin romper compatibilidad?
- [ ] Testabilidad: ¿puede probarse fácilmente con unit tests?
- [ ] Compatibilidad: ¿con entornos, versiones o librerías externas?
- [ ] Observabilidad: (logs, métricas, dumps de diagnóstico en errores críticos)

## 6. Robustez
- [ ] Manejo de errores pensado (excepciones claras, mensajes útiles).
- [ ] Validación de entradas (tipos correctos, rangos válidos).
- [ ] Invariantes: condiciones que **siempre deben cumplirse** para mantener consistencia.
- [ ] Seguridad: sanitización de datos, protección contra usos indebidos.

## 7. Testing
- [ ] Tests unitarios para precondiciones, postcondiciones e invariantes.
- [ ] Tests de casos límite y edge cases (listas vacías, nulos, valores extremos).
- [ ] Tests de integración (interacción con otros módulos/servicios).
- [ ] Automatización con `pytest`, `unittest` o framework equivalente.
- [ ] Tests de invariantes  