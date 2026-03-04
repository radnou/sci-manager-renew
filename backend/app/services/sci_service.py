from typing import List


def calculate_roi(rents: List[float], price: float) -> float:
    if price <= 0:
        return 0.0
    return sum(rents) / price * 100
