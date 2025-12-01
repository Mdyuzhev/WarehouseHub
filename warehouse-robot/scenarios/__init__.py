"""
Сценарии работы склада.
Каждый сценарий эмулирует определённый бизнес-процесс.
"""
from .base import BaseScenario
from .receiving import ReceivingScenario
from .shipping import ShippingScenario
from .inventory import InventoryScenario

# Реестр доступных сценариев
SCENARIOS = {
    "receiving": ReceivingScenario,
    "shipping": ShippingScenario,
    "inventory": InventoryScenario,
}

__all__ = [
    "BaseScenario",
    "ReceivingScenario",
    "ShippingScenario",
    "InventoryScenario",
    "SCENARIOS",
]
