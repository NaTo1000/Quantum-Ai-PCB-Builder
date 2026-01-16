"""API endpoints for the Quantum-Ai-PCB-Builder platform.

This module defines the REST API for design submission,
job management, and result retrieval.
"""

import json
from dataclasses import asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlparse, parse_qs

from ..ai import DesignSynthesizer, OpenAIAdapter
from ..validation import DesignRuleChecker
from ..vendor import VendorMatcher, DesignRequirements, PackagingType


class DesignAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Design API."""

    synthesizer: Optional[DesignSynthesizer] = None
    drc_checker: Optional[DesignRuleChecker] = None
    vendor_matcher: Optional[VendorMatcher] = None

    def _send_json_response(self, data: dict, status: int = 200):
        """Send a JSON response.

        Args:
            data: Dictionary to send as JSON.
            status: HTTP status code.
        """
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error_response(self, message: str, status: int = 400):
        """Send an error response.

        Args:
            message: Error message.
            status: HTTP status code.
        """
        self._send_json_response({"error": message}, status)

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._handle_root()
        elif path == "/health":
            self._handle_health()
        elif path == "/api/v1/status":
            self._handle_status()
        else:
            self._send_error_response("Not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error_response("Invalid JSON")
            return

        if path == "/api/v1/design/synthesize":
            self._handle_synthesize(data)
        elif path == "/api/v1/design/validate":
            self._handle_validate(data)
        elif path == "/api/v1/vendor/match":
            self._handle_vendor_match(data)
        else:
            self._send_error_response("Not found", 404)

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_root(self):
        """Handle root endpoint."""
        self._send_json_response(
            {
                "name": "Quantum-Ai-PCB-Builder API",
                "version": "0.1.0",
                "endpoints": [
                    "GET /health",
                    "GET /api/v1/status",
                    "POST /api/v1/design/synthesize",
                    "POST /api/v1/design/validate",
                    "POST /api/v1/vendor/match",
                ],
            }
        )

    def _handle_health(self):
        """Handle health check endpoint."""
        self._send_json_response({"status": "healthy"})

    def _handle_status(self):
        """Handle status endpoint."""
        self._send_json_response(
            {
                "status": "running",
                "components": {
                    "synthesizer": self.synthesizer is not None,
                    "drc_checker": self.drc_checker is not None,
                    "vendor_matcher": self.vendor_matcher is not None,
                },
            }
        )

    def _handle_synthesize(self, data: dict):
        """Handle design synthesis request.

        Args:
            data: Request data with 'prompt' field.
        """
        prompt = data.get("prompt")
        if not prompt:
            self._send_error_response("Missing 'prompt' field")
            return

        if self.synthesizer is None:
            self._send_error_response("Synthesizer not initialized", 503)
            return

        result = self.synthesizer.synthesize(prompt)

        response = {
            "success": result.success,
            "architecture": result.architecture_description,
            "rtl_stub": result.rtl_stub,
            "components": [
                {
                    "name": c.name,
                    "type": c.component_type,
                    "description": c.description,
                }
                for c in result.components
            ],
        }

        self._send_json_response(response)

    def _handle_validate(self, data: dict):
        """Handle design validation request.

        Args:
            data: Request data with design data.
        """
        if self.drc_checker is None:
            self._send_error_response("DRC checker not initialized", 503)
            return

        result = self.drc_checker.check(data)

        response = {
            "passed": result.passed,
            "total_checks": result.total_checks,
            "passed_checks": result.passed_checks,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity.value,
                    "message": v.message,
                }
                for v in result.violations
            ],
        }

        self._send_json_response(response)

    def _handle_vendor_match(self, data: dict):
        """Handle vendor matching request.

        Args:
            data: Request data with design requirements.
        """
        if self.vendor_matcher is None:
            self._send_error_response("Vendor matcher not initialized", 503)
            return

        try:
            requirements = DesignRequirements(
                process_node=data.get("process_node", "7nm"),
                packaging_type=PackagingType(data.get("packaging_type", "standard")),
                estimated_volume=data.get("volume", 10000),
            )
        except (KeyError, ValueError) as e:
            self._send_error_response(f"Invalid requirements: {e}")
            return

        quotes = self.vendor_matcher.get_quotes(requirements)

        response = {
            "requirements": {
                "process_node": requirements.process_node,
                "packaging_type": requirements.packaging_type.value,
                "volume": requirements.estimated_volume,
            },
            "quotes": [
                {
                    "vendor": q.vendor_name,
                    "unit_cost_usd": q.unit_cost_usd,
                    "nre_cost_usd": q.nre_cost_usd,
                    "lead_time_weeks": q.lead_time_weeks,
                    "min_order": q.min_order_quantity,
                }
                for q in quotes
            ],
        }

        self._send_json_response(response)


def create_app(host: str = "0.0.0.0", port: int = 8080) -> HTTPServer:
    """Create and configure the HTTP server.

    Args:
        host: Host address to bind to.
        port: Port number to listen on.

    Returns:
        Configured HTTPServer instance.
    """
    # Initialize components
    llm_adapter = OpenAIAdapter()
    DesignAPIHandler.synthesizer = DesignSynthesizer(llm_adapter)
    DesignAPIHandler.drc_checker = DesignRuleChecker()
    DesignAPIHandler.vendor_matcher = VendorMatcher()

    server = HTTPServer((host, port), DesignAPIHandler)
    return server


def main():
    """Run the API server."""
    host = "0.0.0.0"
    port = 8080

    print(f"Starting Quantum-Ai-PCB-Builder API server on {host}:{port}")
    server = create_app(host, port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
