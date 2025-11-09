from typing import List
import numpy as np

class AreaCalculation:
    def __init__(self, coordinates: List[dict]):
        self.coordinates = coordinates

    def calculate(self) -> float:
        """Calculate area using Shoelace formula"""
        coords = np.array([(p['lat'], p['lng']) for p in self.coordinates])
        x = coords[:, 0]
        y = coords[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
