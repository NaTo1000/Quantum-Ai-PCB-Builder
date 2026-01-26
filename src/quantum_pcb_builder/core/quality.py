"""Quality assurance utilities for the Quantum PCB Builder system.

This module provides comprehensive validation, error checking, and quality
assurance utilities to ensure premium quality outcomes.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

from quantum_pcb_builder.core.exceptions import ValidationError

T = TypeVar("T")


class QualityLevel(Enum):
    """Quality levels for validation."""

    MINIMAL = "minimal"  # Basic required checks only
    STANDARD = "standard"  # Standard quality checks
    STRICT = "strict"  # Strict validation with all checks
    PREMIUM = "premium"  # Premium quality with extended checks


@dataclass
class QualityReport:
    """Report from quality assessment."""

    passed: bool
    level: QualityLevel
    score: float  # 0.0 to 100.0
    checks_passed: int = 0
    checks_failed: int = 0
    checks_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str, check_name: str | None = None) -> None:
        """Add an error to the report."""
        self.passed = False
        self.checks_failed += 1
        prefix = f"[{check_name}] " if check_name else ""
        self.errors.append(f"{prefix}{message}")

    def add_warning(self, message: str, check_name: str | None = None) -> None:
        """Add a warning to the report."""
        prefix = f"[{check_name}] " if check_name else ""
        self.warnings.append(f"{prefix}{message}")

    def add_info(self, message: str) -> None:
        """Add an info message to the report."""
        self.info.append(message)

    def pass_check(self, check_name: str) -> None:
        """Mark a check as passed."""
        self.checks_passed += 1
        self.info.append(f"✓ {check_name}")

    def skip_check(self, check_name: str, reason: str) -> None:
        """Mark a check as skipped."""
        self.checks_skipped += 1
        self.info.append(f"⊘ {check_name} (skipped: {reason})")

    def calculate_score(self) -> None:
        """Calculate quality score based on check results."""
        total = self.checks_passed + self.checks_failed
        if total == 0:
            self.score = 100.0
        else:
            # Warnings reduce score by 1 point each, errors by 10 points each
            base_score = (self.checks_passed / total) * 100
            warning_penalty = len(self.warnings) * 1
            error_penalty = len(self.errors) * 10
            self.score = max(0, base_score - warning_penalty - error_penalty)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "passed": self.passed,
            "level": self.level.value,
            "score": self.score,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "checks_skipped": self.checks_skipped,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "details": self.details,
        }


class Validator(ABC, Generic[T]):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, value: T) -> QualityReport:
        """Validate a value and return a quality report."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the validator name."""
        ...


@dataclass
class Rule(Generic[T]):
    """A single validation rule."""

    name: str
    check: Callable[[T], bool]
    error_message: str
    level: QualityLevel = QualityLevel.STANDARD
    is_warning: bool = False


class RuleBasedValidator(Validator[T]):
    """Validator that uses a set of rules."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._rules: list[Rule[T]] = []

    def add_rule(
        self,
        name: str,
        check: Callable[[T], bool],
        error_message: str,
        level: QualityLevel = QualityLevel.STANDARD,
        is_warning: bool = False,
    ) -> RuleBasedValidator[T]:
        """Add a validation rule."""
        self._rules.append(
            Rule(
                name=name,
                check=check,
                error_message=error_message,
                level=level,
                is_warning=is_warning,
            )
        )
        return self

    def get_name(self) -> str:
        """Get the validator name."""
        return self._name

    def validate(
        self,
        value: T,
        level: QualityLevel = QualityLevel.STANDARD,
    ) -> QualityReport:
        """Validate a value against all applicable rules."""
        report = QualityReport(passed=True, level=level, score=100.0)

        level_order = [
            QualityLevel.MINIMAL,
            QualityLevel.STANDARD,
            QualityLevel.STRICT,
            QualityLevel.PREMIUM,
        ]
        max_level_index = level_order.index(level)

        for rule in self._rules:
            rule_level_index = level_order.index(rule.level)

            if rule_level_index > max_level_index:
                report.skip_check(rule.name, f"Level {rule.level.value} not enabled")
                continue

            try:
                if rule.check(value):
                    report.pass_check(rule.name)
                elif rule.is_warning:
                    report.add_warning(rule.error_message, rule.name)
                    report.checks_passed += 1  # Warnings don't fail
                else:
                    report.add_error(rule.error_message, rule.name)
            except Exception as e:
                report.add_error(f"Check raised exception: {e}", rule.name)

        report.calculate_score()
        return report


# ============================================================================
# Built-in Validators
# ============================================================================


class StringValidator(RuleBasedValidator[str]):
    """Validator for string values."""

    def __init__(
        self,
        name: str = "string",
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
    ) -> None:
        super().__init__(name)

        if required:
            self.add_rule(
                "required",
                lambda s: bool(s and s.strip()),
                f"{name} is required",
                QualityLevel.MINIMAL,
            )

        if min_length is not None:
            self.add_rule(
                "min_length",
                lambda s: len(s) >= min_length if s else False,
                f"{name} must be at least {min_length} characters",
            )

        if max_length is not None:
            self.add_rule(
                "max_length",
                lambda s: len(s) <= max_length if s else True,
                f"{name} must be at most {max_length} characters",
            )

        if pattern is not None:
            self.add_rule(
                "pattern",
                lambda s: bool(re.match(pattern, s)) if s else False,
                f"{name} must match pattern {pattern}",
            )


class NumberValidator(RuleBasedValidator[float]):
    """Validator for numeric values."""

    def __init__(
        self,
        name: str = "number",
        min_value: float | None = None,
        max_value: float | None = None,
        allow_zero: bool = True,
        allow_negative: bool = True,
    ) -> None:
        super().__init__(name)

        if not allow_zero:
            self.add_rule(
                "non_zero",
                lambda n: n != 0,
                f"{name} cannot be zero",
                QualityLevel.MINIMAL,
            )

        if not allow_negative:
            self.add_rule(
                "non_negative",
                lambda n: n >= 0,
                f"{name} cannot be negative",
                QualityLevel.MINIMAL,
            )

        if min_value is not None:
            self.add_rule(
                "min_value",
                lambda n: n >= min_value,
                f"{name} must be at least {min_value}",
            )

        if max_value is not None:
            self.add_rule(
                "max_value",
                lambda n: n <= max_value,
                f"{name} must be at most {max_value}",
            )


class DictValidator(RuleBasedValidator[dict[str, Any]]):
    """Validator for dictionary values."""

    def __init__(
        self,
        name: str = "dict",
        required_keys: list[str] | None = None,
        optional_keys: list[str] | None = None,
        allow_extra_keys: bool = True,
    ) -> None:
        super().__init__(name)
        self._required_keys = required_keys or []
        self._optional_keys = optional_keys or []
        self._allow_extra_keys = allow_extra_keys

        for key in self._required_keys:

            def make_check(k: str) -> Callable[[dict[str, Any]], bool]:
                return lambda d: k in d

            self.add_rule(
                f"required_key_{key}",
                make_check(key),
                f"Missing required key: {key}",
                QualityLevel.MINIMAL,
            )

        if not allow_extra_keys:
            all_keys = set(self._required_keys + self._optional_keys)
            self.add_rule(
                "no_extra_keys",
                lambda d: set(d.keys()).issubset(all_keys),
                f"Extra keys not allowed. Valid keys: {all_keys}",
                QualityLevel.STRICT,
            )


# ============================================================================
# Quality Assurance Engine
# ============================================================================


class QualityAssuranceEngine:
    """Engine for running quality assurance checks."""

    def __init__(self, level: QualityLevel = QualityLevel.STANDARD) -> None:
        self.level = level
        self._validators: dict[str, Validator[Any]] = {}

    def register_validator(
        self,
        name: str,
        validator: Validator[Any],
    ) -> QualityAssuranceEngine:
        """Register a validator."""
        self._validators[name] = validator
        return self

    def run_checks(
        self,
        data: dict[str, Any],
    ) -> QualityReport:
        """Run all registered validators against data.

        Args:
            data: Dictionary mapping validator names to values.

        Returns:
            Combined quality report.
        """
        combined_report = QualityReport(
            passed=True,
            level=self.level,
            score=100.0,
        )

        for name, validator in self._validators.items():
            if name in data:
                report = validator.validate(data[name])
                combined_report.checks_passed += report.checks_passed
                combined_report.checks_failed += report.checks_failed
                combined_report.checks_skipped += report.checks_skipped
                combined_report.errors.extend(report.errors)
                combined_report.warnings.extend(report.warnings)
                combined_report.info.extend(report.info)
                combined_report.details[name] = report.to_dict()

                if not report.passed:
                    combined_report.passed = False

        combined_report.calculate_score()
        return combined_report


def ensure_valid(value: Any, validator: Validator[Any]) -> None:
    """Ensure a value is valid or raise ValidationError.

    Args:
        value: The value to validate.
        validator: The validator to use.

    Raises:
        ValidationError: If validation fails.
    """
    report = validator.validate(value)
    if not report.passed:
        raise ValidationError(
            message=f"Validation failed for {validator.get_name()}",
            field=validator.get_name(),
            value=value,
            details={"report": report.to_dict()},
        )
