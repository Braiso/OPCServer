class OpcClient:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.client = None
        self.aliases: dict[str, str] = {}     # config (alias -> nodeid_str)
        self.nodes: dict[str, Any] = {}       # runtime (alias -> ua.Node), se llena tras connect()

    def load_aliases(self, mapping: dict[str, str]) -> None:
        # validar aquí: tipos, duplicados, formato básico de nodeid
        self.aliases = dict(mapping)

    def connect(self) -> None:
        # ... abre sesión ...
        self._resolve_nodes()  # llena self.nodes usando self.client.get_node()

    def _resolve_nodes(self) -> None:
        self.nodes.clear()
        for alias, nodeid in self.aliases.items():
            self.nodes[alias] = self.client.get_node(nodeid)

    def disconnect(self) -> None:
        # ... cierra sesión ...
        self.nodes.clear()  # invalidar caché ligada a la sesión

    # Azúcar de uso con alias
    def read_alias(self, alias: str):
        node = self.nodes.get(alias) or self.client.get_node(self.aliases[alias])
        return node.get_value()

    def write_alias(self, alias: str, value):
        node = self.nodes.get(alias) or self.client.get_node(self.aliases[alias])
        node.set_value(value)
