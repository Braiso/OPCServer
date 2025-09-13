## 🔹 Tabla de DataTypes nativos OPC UA

| **ID** | **Nombre**       | **Descripción** |
|--------|------------------|-----------------|
| 1      | Boolean          | `true` / `false` |
| 2      | SByte            | Entero con signo de 8 bits (-128 a 127) |
| 3      | Byte             | Entero sin signo de 8 bits (0 a 255) |
| 4      | Int16            | Entero con signo de 16 bits |
| 5      | UInt16           | Entero sin signo de 16 bits |
| 6      | Int32            | Entero con signo de 32 bits |
| 7      | UInt32           | Entero sin signo de 32 bits |
| 8      | Int64            | Entero con signo de 64 bits |
| 9      | UInt64           | Entero sin signo de 64 bits |
| 10     | Float            | Número de punto flotante de 32 bits |
| 11     | Double           | Número de punto flotante de 64 bits |
| 12     | String           | Cadena de texto |
| 13     | DateTime         | Fecha y hora (64-bit, intervalo desde 1601 d.C.) |
| 14     | Guid             | Identificador único global (UUID) |
| 15     | ByteString       | Secuencia de bytes |
| 16     | XmlElement       | Fragmento XML |
| 17     | NodeId           | Identificador de nodo en el Address Space |
| 18     | ExpandedNodeId   | Versión extendida de NodeId (incluye namespace adicional) |
| 19     | StatusCode       | Código de estado con bits de diagnóstico |
| 20     | QualifiedName    | Nombre con NamespaceIndex asociado |
| 21     | LocalizedText    | Texto traducible (cadena + idioma) |
| 22     | Structure        | Tipo complejo con múltiples campos |
| 23     | DataValue        | Valor + estado + timestamps |
| 24     | BaseDataType     | Superclase de todos los DataTypes |
| 25     | DiagnosticInfo   | Información detallada de diagnóstico |
