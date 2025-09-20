## Built-in DataTypes OPC UA

| Id | Nombre OPC UA     | Equivalente en Python (`python-opcua`) | Descripción |
|----|-------------------|-----------------------------------------|-------------|
| 1  | Boolean           | `bool` | Verdadero/Falso |
| 2  | SByte             | `int` (−128 … 127) | Entero con signo de 8 bits |
| 3  | Byte              | `int` (0 … 255) | Entero sin signo de 8 bits |
| 4  | Int16             | `int` (−32 768 … 32 767) | Entero con signo de 16 bits |
| 5  | UInt16            | `int` (0 … 65 535) | Entero sin signo de 16 bits |
| 6  | Int32             | `int` (−2 147 483 648 … 2 147 483 647) | Entero con signo de 32 bits |
| 7  | UInt32            | `int` (0 … 4 294 967 295) | Entero sin signo de 32 bits |
| 8  | Int64             | `int` (−2^63 … 2^63−1) | Entero con signo de 64 bits |
| 9  | UInt64            | `int` (0 … 2^64−1) | Entero sin signo de 64 bits |
| 10 | Float             | `float` (32-bit) | Número en coma flotante simple |
| 11 | Double            | `float` (64-bit) | Número en coma flotante doble |
| 12 | String            | `str` | Cadena de caracteres Unicode |
| 13 | DateTime          | `datetime.datetime` | Fecha y hora con precisión de 100 ns |
| 14 | Guid              | `uuid.UUID` | Identificador único global (128 bits) |
| 15 | ByteString        | `bytes` | Secuencia arbitraria de bytes |
| 16 | XmlElement        | `str` o `xml.etree.Element` | Fragmento de XML |
| 17 | NodeId            | `ua.NodeId` | Identificador único de nodo en OPC UA |
| 18 | ExpandedNodeId    | `ua.ExpandedNodeId` | NodeId extendido con namespace adicional |
| 19 | StatusCode        | `ua.StatusCode` | Código de estado de una operación OPC |
| 20 | QualifiedName     | `ua.QualifiedName` | Nombre con un índice de namespace |
| 21 | LocalizedText     | `ua.LocalizedText` | Texto con localización (traducción) |
| 22 | ExtensionObject   | objetos complejos (structs) | Encapsula tipos de datos definidos por el usuario |
| 23 | DataValue         | `ua.DataValue` | Valor de variable con metadatos (timestamp, status) |
| 24 | Variant           | `ua.Variant` | Contenedor genérico que envuelve cualquier tipo |
| 25 | DiagnosticInfo    | `ua.DiagnosticInfo` | Información diagnóstica adicional |
