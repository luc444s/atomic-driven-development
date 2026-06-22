from packages.sdk import PluginContext


def register(context: PluginContext) -> None:
    context.register_permissions(["logistics.delivery.read"])
    context.register_events(["logistics.delivery.created"])
