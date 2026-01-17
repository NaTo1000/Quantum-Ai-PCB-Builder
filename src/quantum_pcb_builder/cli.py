"""
Command Line Interface for Quantum PCB Builder.

Provides CLI commands for:
- Project initialization
- Design optimization
- Manufacturing export
- Cost estimation
"""

import argparse
import json
import sys
from pathlib import Path

from quantum_pcb_builder import __version__
from quantum_pcb_builder.ai.circuit_analyzer import CircuitAnalyzer
from quantum_pcb_builder.algorithms.genetic_algorithm import GeneticAlgorithm
from quantum_pcb_builder.algorithms.quantum_optimizer import SimulatedQuantumAnnealing
from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import Component, ComponentType, Footprint
from quantum_pcb_builder.core.pcb import PCBBoard
from quantum_pcb_builder.manufacturing.cost_estimator import CostEstimator, ManufacturingSpecs
from quantum_pcb_builder.manufacturing.exporter import BOMExporter, GerberExporter


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="quantum-pcb",
        description="Quantum AI-Powered PCB Builder - Autonomous chip and PCB design",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new PCB project")
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument("--width", type=float, default=100.0, help="Board width in mm")
    init_parser.add_argument("--height", type=float, default=100.0, help="Board height in mm")
    init_parser.add_argument("--layers", type=int, default=2, help="Number of copper layers")
    init_parser.add_argument("--output", "-o", default=".", help="Output directory")

    # Optimize command
    opt_parser = subparsers.add_parser("optimize", help="Optimize PCB design")
    opt_parser.add_argument("input", help="Input design file (JSON)")
    opt_parser.add_argument(
        "--algorithm",
        choices=["quantum", "genetic"],
        default="quantum",
        help="Optimization algorithm",
    )
    opt_parser.add_argument("--iterations", type=int, default=500, help="Max iterations")
    opt_parser.add_argument("--output", "-o", help="Output file for optimized design")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze PCB design")
    analyze_parser.add_argument("input", help="Input design file (JSON)")
    analyze_parser.add_argument("--strict", action="store_true", help="Enable strict analysis")
    analyze_parser.add_argument("--output", "-o", help="Output file for analysis report")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export manufacturing files")
    export_parser.add_argument("input", help="Input design file (JSON)")
    export_parser.add_argument(
        "--format",
        choices=["gerber", "bom", "all"],
        default="all",
        help="Export format",
    )
    export_parser.add_argument("--output", "-o", default="./output", help="Output directory")

    # Quote command
    quote_parser = subparsers.add_parser("quote", help="Get manufacturing quote")
    quote_parser.add_argument("input", help="Input design file (JSON)")
    quote_parser.add_argument("--quantity", type=int, default=10, help="Quantity to quote")
    quote_parser.add_argument("--output", "-o", help="Output file for quote")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a demonstration")
    demo_parser.add_argument(
        "--type",
        choices=["esp32", "lora", "simple"],
        default="esp32",
        help="Demo type",
    )

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new PCB project."""
    print(f"Initializing project: {args.name}")
    print(f"Board size: {args.width}x{args.height}mm, {args.layers} layers")

    # Create project structure
    output_dir = Path(args.output)
    project_dir = output_dir / args.name

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "designs").mkdir(exist_ok=True)
    (project_dir / "output").mkdir(exist_ok=True)

    # Create initial design file
    design = {
        "name": args.name,
        "version": "1.0.0",
        "board": {
            "width_mm": args.width,
            "height_mm": args.height,
            "layer_count": args.layers,
        },
        "components": [],
        "nets": [],
    }

    design_file = project_dir / "designs" / f"{args.name}.json"
    with open(design_file, "w") as f:
        json.dump(design, f, indent=2)

    print(f"Created project at: {project_dir}")
    print(f"Design file: {design_file}")

    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    """Optimize PCB design."""
    print(f"Loading design from: {args.input}")

    # Load design
    with open(args.input) as f:
        design = json.load(f)

    # Create circuit
    circuit = Circuit(name=design.get("name", "Untitled"))

    # Add components
    for comp_data in design.get("components", []):
        comp = Component(
            name=comp_data["name"],
            component_type=ComponentType[comp_data.get("type", "CUSTOM")],
            value=comp_data.get("value", ""),
            package=comp_data.get("package", ""),
        )
        if "position" in comp_data:
            comp.position = tuple(comp_data["position"])
        circuit.add_component(comp)

    if len(circuit.components) == 0:
        print("No components to optimize")
        return 1

    print(f"Optimizing {len(circuit.components)} components using {args.algorithm} algorithm...")

    # Run optimization
    if args.algorithm == "quantum":
        optimizer = SimulatedQuantumAnnealing(max_iterations=args.iterations)
        result = optimizer.optimize(
            circuit,
            design.get("board", {}).get("width_mm", 100.0),
            design.get("board", {}).get("height_mm", 100.0),
        )
    else:
        optimizer = GeneticAlgorithm(max_generations=args.iterations)
        result = optimizer.optimize(
            circuit,
            design.get("board", {}).get("width_mm", 100.0),
            design.get("board", {}).get("height_mm", 100.0),
        )

    # Update design with optimized positions
    if isinstance(result, dict):
        best_solution = result.get("best_solution", [])
        best_cost = result.get("best_fitness", 0)
        iterations = result.get("generations", 0)
    else:
        best_solution = result.best_solution
        best_cost = result.best_cost
        iterations = result.iterations

    for i, comp_data in enumerate(design.get("components", [])):
        if i < len(best_solution):
            comp_data["position"] = list(best_solution[i])

    print(f"Optimization complete after {iterations} iterations")
    print(f"Best cost: {best_cost:.2f}")

    # Save optimized design
    output_file = args.output or args.input.replace(".json", "_optimized.json")
    with open(output_file, "w") as f:
        json.dump(design, f, indent=2)

    print(f"Saved optimized design to: {output_file}")

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze PCB design."""
    print(f"Analyzing design: {args.input}")

    # Load design
    with open(args.input) as f:
        design = json.load(f)

    # Create circuit
    circuit = Circuit(name=design.get("name", "Untitled"))

    for comp_data in design.get("components", []):
        comp = Component(
            name=comp_data["name"],
            component_type=ComponentType[comp_data.get("type", "CUSTOM")],
            value=comp_data.get("value", ""),
        )
        if "position" in comp_data:
            comp.position = tuple(comp_data["position"])
        circuit.add_component(comp)

    # Run analysis
    analyzer = CircuitAnalyzer(strict_mode=args.strict)
    result = analyzer.analyze(circuit)

    # Print results
    print(f"\nAnalysis Results for: {circuit.name}")
    print("=" * 50)
    print(f"Overall Score: {result.overall_score:.2%}")
    print(f"Status: {'PASSED' if result.passed else 'FAILED'}")
    print()

    print("Scores:")
    for key, value in result.scores.items():
        print(f"  {key}: {value:.2%}")

    print()
    print("Findings:")
    for finding in result.findings:
        severity = finding.severity.name
        print(f"  [{severity}] {finding.category}: {finding.message}")
        if finding.recommendation:
            print(f"           Recommendation: {finding.recommendation}")

    # Save report if output specified
    if args.output:
        report = {
            "circuit_name": circuit.name,
            "overall_score": result.overall_score,
            "passed": result.passed,
            "scores": result.scores,
            "metrics": result.metrics,
            "findings": [
                {
                    "category": f.category,
                    "message": f.message,
                    "severity": f.severity.name,
                    "recommendation": f.recommendation,
                }
                for f in result.findings
            ],
        }

        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to: {args.output}")

    return 0 if result.passed else 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export manufacturing files."""
    print(f"Exporting design: {args.input}")

    # Load design
    with open(args.input) as f:
        design = json.load(f)

    # Create board
    board_data = design.get("board", {})
    board = PCBBoard(
        name=design.get("name", "Untitled"),
        width_mm=board_data.get("width_mm", 100.0),
        height_mm=board_data.get("height_mm", 100.0),
        layer_count=board_data.get("layer_count", 2),
    )

    # Add components
    for comp_data in design.get("components", []):
        comp = Component(
            name=comp_data["name"],
            component_type=ComponentType[comp_data.get("type", "CUSTOM")],
            value=comp_data.get("value", ""),
            package=comp_data.get("package", ""),
        )
        if "position" in comp_data:
            pos = tuple(comp_data["position"])
            board.place_component(comp, pos)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export files
    if args.format in ("gerber", "all"):
        gerber_exporter = GerberExporter()
        result = gerber_exporter.export(board)
        for filename, content in result.files.items():
            filepath = output_dir / filename
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  Created: {filepath}")

    if args.format in ("bom", "all"):
        bom_exporter = BOMExporter()
        result = bom_exporter.export(board)
        for filename, content in result.files.items():
            filepath = output_dir / filename
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  Created: {filepath}")

    print(f"\nExport complete. Files saved to: {output_dir}")

    return 0


def cmd_quote(args: argparse.Namespace) -> int:
    """Get manufacturing quote."""
    print(f"Generating quote for: {args.input}")

    # Load design
    with open(args.input) as f:
        design = json.load(f)

    # Create board
    board_data = design.get("board", {})
    board = PCBBoard(
        name=design.get("name", "Untitled"),
        width_mm=board_data.get("width_mm", 100.0),
        height_mm=board_data.get("height_mm", 100.0),
        layer_count=board_data.get("layer_count", 2),
    )

    # Generate quote
    estimator = CostEstimator()
    specs = ManufacturingSpecs(quantity=args.quantity)
    quote = estimator.estimate(board, specs)

    # Print quote
    print("\nManufacturing Quote")
    print("=" * 50)
    print(f"Board: {quote.board_name}")
    print(f"Quantity: {quote.quantity}")
    print()
    print("Cost Breakdown:")
    print(f"  Base cost: ${quote.breakdown.pcb_base_cost:.2f}")
    print(f"  Layer cost: ${quote.breakdown.layer_cost:.2f}")
    print(f"  Area cost: ${quote.breakdown.area_cost:.2f}")
    print(f"  Drill cost: ${quote.breakdown.drill_cost:.2f}")
    print(f"  Finish cost: ${quote.breakdown.finish_cost:.2f}")
    print(f"  Tooling cost: ${quote.breakdown.tooling_cost:.2f}")
    print()
    print(f"Unit Price: ${quote.unit_price:.2f}")
    print(f"Total Price: ${quote.total_price:.2f}")
    print(f"Lead Time: {quote.lead_time_days} days")

    if quote.notes:
        print()
        print("Notes:")
        for note in quote.notes:
            print(f"  - {note}")

    # Save quote if output specified
    if args.output:
        quote_data = {
            "board_name": quote.board_name,
            "quantity": quote.quantity,
            "unit_price": quote.unit_price,
            "total_price": quote.total_price,
            "lead_time_days": quote.lead_time_days,
            "breakdown": {
                "pcb_base_cost": quote.breakdown.pcb_base_cost,
                "layer_cost": quote.breakdown.layer_cost,
                "area_cost": quote.breakdown.area_cost,
                "drill_cost": quote.breakdown.drill_cost,
                "finish_cost": quote.breakdown.finish_cost,
                "tooling_cost": quote.breakdown.tooling_cost,
            },
            "notes": quote.notes,
        }

        with open(args.output, "w") as f:
            json.dump(quote_data, f, indent=2)

        print(f"\nQuote saved to: {args.output}")

    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Run a demonstration."""
    print(f"Running {args.type} demo...")
    print()

    if args.type == "esp32":
        # Create ESP32 demo
        circuit = Circuit(name="ESP32 IoT Demo")

        esp32 = Component(
            name="U1",
            component_type=ComponentType.MICROCONTROLLER,
            package="SMD",
            footprint=Footprint("ESP32-WROOM-32", 18.0, 25.5, 38),
        )
        regulator = Component(
            name="U2",
            component_type=ComponentType.VOLTAGE_REGULATOR,
            package="SOT-223",
        )
        cap1 = Component(name="C1", component_type=ComponentType.CAPACITOR, value="100nF")
        cap2 = Component(name="C2", component_type=ComponentType.CAPACITOR, value="10uF")
        res1 = Component(name="R1", component_type=ComponentType.RESISTOR, value="10k")

        circuit.add_component(esp32)
        circuit.add_component(regulator)
        circuit.add_component(cap1)
        circuit.add_component(cap2)
        circuit.add_component(res1)

        print(f"Created circuit: {circuit.name}")
        print(f"Components: {len(circuit.components)}")

        # Run optimization
        optimizer = SimulatedQuantumAnnealing(max_iterations=100)
        result = optimizer.optimize(circuit, 80.0, 60.0)

        print("\nOptimization complete:")
        print(f"  Best cost: {result.best_cost:.2f}")
        print(f"  Iterations: {result.iterations}")

        # Analyze
        analyzer = CircuitAnalyzer()
        analysis = analyzer.analyze(circuit)
        print(f"\nAnalysis score: {analysis.overall_score:.2%}")

    elif args.type == "lora":
        # Create LoRa demo
        circuit = Circuit(name="LoRa Sensor Node")

        mcu = Component(name="U1", component_type=ComponentType.MICROCONTROLLER)
        lora = Component(name="U2", component_type=ComponentType.RF_MODULE)
        sensor = Component(name="U3", component_type=ComponentType.SENSOR)
        antenna = Component(name="ANT1", component_type=ComponentType.ANTENNA)

        circuit.add_component(mcu)
        circuit.add_component(lora)
        circuit.add_component(sensor)
        circuit.add_component(antenna)

        circuit.connect(mcu.uuid, "SPI", lora.uuid, "SPI", "SPI_BUS")
        circuit.connect(mcu.uuid, "I2C", sensor.uuid, "I2C", "I2C_BUS")

        print(f"Created circuit: {circuit.name}")
        print(f"Components: {len(circuit.components)}")
        print(f"Nets: {len(circuit.nets)}")

    else:
        # Simple demo
        circuit = Circuit(name="Simple Demo")
        led = Component(name="LED1", component_type=ComponentType.LED)
        resistor = Component(name="R1", component_type=ComponentType.RESISTOR, value="330")

        circuit.add_component(led)
        circuit.add_component(resistor)
        circuit.connect(led.uuid, "anode", resistor.uuid, "1", "LED_NET")

        print(f"Created circuit: {circuit.name}")
        print(f"Components: {len(circuit.components)}")

    print("\nDemo complete!")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "init": cmd_init,
        "optimize": cmd_optimize,
        "analyze": cmd_analyze,
        "export": cmd_export,
        "quote": cmd_quote,
        "demo": cmd_demo,
    }

    handler = commands.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}")
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
