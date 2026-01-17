"""
Configuration management for Quantum PCB Builder.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Application configuration."""

    # Optimization settings
    optimization_max_iterations: int = 1000
    optimization_population_size: int = 50
    optimization_convergence_threshold: float = 1e-6

    # Routing settings
    routing_via_cost: float = 10.0
    routing_turn_cost: float = 1.0
    routing_grid_resolution_mm: float = 0.25

    # Manufacturing defaults
    default_copper_weight_oz: float = 1.0
    default_board_thickness_mm: float = 1.6
    default_layer_count: int = 2

    # Design rules
    min_trace_width_mm: float = 0.15
    min_clearance_mm: float = 0.15
    min_via_diameter_mm: float = 0.4
    min_via_drill_mm: float = 0.2

    # Paths
    output_directory: str = "./output"
    temp_directory: str = "/tmp/quantum_pcb"

    # API settings (for marketplace)
    api_base_url: str = ""
    api_timeout_seconds: int = 30

    # Custom settings
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "optimization_max_iterations": self.optimization_max_iterations,
            "optimization_population_size": self.optimization_population_size,
            "optimization_convergence_threshold": self.optimization_convergence_threshold,
            "routing_via_cost": self.routing_via_cost,
            "routing_turn_cost": self.routing_turn_cost,
            "routing_grid_resolution_mm": self.routing_grid_resolution_mm,
            "default_copper_weight_oz": self.default_copper_weight_oz,
            "default_board_thickness_mm": self.default_board_thickness_mm,
            "default_layer_count": self.default_layer_count,
            "min_trace_width_mm": self.min_trace_width_mm,
            "min_clearance_mm": self.min_clearance_mm,
            "min_via_diameter_mm": self.min_via_diameter_mm,
            "min_via_drill_mm": self.min_via_drill_mm,
            "output_directory": self.output_directory,
            "temp_directory": self.temp_directory,
            "api_base_url": self.api_base_url,
            "api_timeout_seconds": self.api_timeout_seconds,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        return cls(
            optimization_max_iterations=data.get("optimization_max_iterations", 1000),
            optimization_population_size=data.get("optimization_population_size", 50),
            optimization_convergence_threshold=data.get("optimization_convergence_threshold", 1e-6),
            routing_via_cost=data.get("routing_via_cost", 10.0),
            routing_turn_cost=data.get("routing_turn_cost", 1.0),
            routing_grid_resolution_mm=data.get("routing_grid_resolution_mm", 0.25),
            default_copper_weight_oz=data.get("default_copper_weight_oz", 1.0),
            default_board_thickness_mm=data.get("default_board_thickness_mm", 1.6),
            default_layer_count=data.get("default_layer_count", 2),
            min_trace_width_mm=data.get("min_trace_width_mm", 0.15),
            min_clearance_mm=data.get("min_clearance_mm", 0.15),
            min_via_diameter_mm=data.get("min_via_diameter_mm", 0.4),
            min_via_drill_mm=data.get("min_via_drill_mm", 0.2),
            output_directory=data.get("output_directory", "./output"),
            temp_directory=data.get("temp_directory", "/tmp/quantum_pcb"),
            api_base_url=data.get("api_base_url", ""),
            api_timeout_seconds=data.get("api_timeout_seconds", 30),
            custom=data.get("custom", {}),
        )


def load_config(config_path: str | Path | None = None) -> Config:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file (JSON format)

    Returns:
        Config object
    """
    if config_path is None:
        # Check default locations
        default_paths = [
            Path("quantum_pcb_config.json"),
            Path.home() / ".config" / "quantum_pcb" / "config.json",
            Path("/etc/quantum_pcb/config.json"),
        ]

        for path in default_paths:
            if path.exists():
                config_path = path
                break

    if config_path is None or not Path(config_path).exists():
        return Config()

    with open(config_path) as f:
        data = json.load(f)

    return Config.from_dict(data)


def save_config(config: Config, config_path: str | Path) -> None:
    """
    Save configuration to file.

    Args:
        config: Config object to save
        config_path: Path to save to
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
