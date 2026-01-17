"""
Quantum AI PCB Builder - Autonomous chip and PCB design with AI optimization.

This package provides advanced quantum-inspired algorithms for:
- PCB layout optimization
- Component selection using AI
- Circuit routing with graph algorithms
- Manufacturing integration
- Marketplace bidding system
"""

__version__ = "1.0.0"
__author__ = "Quantum PCB Team"

from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import Component, ComponentType
from quantum_pcb_builder.core.pcb import PCBBoard, PCBLayer

__all__ = [
    "__version__",
    "Component",
    "ComponentType",
    "Circuit",
    "PCBBoard",
    "PCBLayer",
]
