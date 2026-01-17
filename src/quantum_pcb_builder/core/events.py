"""Event system for the Quantum PCB Builder.

This module provides an event bus for decoupled communication between components.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4


@dataclass
class Event:
    """Represents an event in the system."""

    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


# Type alias for event handlers
EventHandler = Callable[[Event], None]


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._event_history: list[Event] = []
        self._max_history_size: int = 1000

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe a handler from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        return False

    def publish(self, event: Event) -> int:
        """Publish an event to all subscribed handlers.

        Returns the number of handlers that received the event.
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)

        # Notify handlers
        handlers = self._handlers.get(event.event_type, [])
        wildcard_handlers = self._handlers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        for handler in all_handlers:
            handler(event)

        return len(all_handlers)

    def get_history(self, event_type: str | None = None, limit: int = 100) -> list[Event]:
        """Get event history, optionally filtered by event type."""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()

    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type."""
        return len(self._handlers.get(event_type, []))
