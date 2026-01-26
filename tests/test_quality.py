"""Tests for the quality assurance module."""

from __future__ import annotations

import pytest

from quantum_pcb_builder.core.exceptions import ValidationError
from quantum_pcb_builder.core.quality import (
    DictValidator,
    NumberValidator,
    QualityAssuranceEngine,
    QualityLevel,
    QualityReport,
    RuleBasedValidator,
    StringValidator,
    ensure_valid,
)


class TestQualityReport:
    """Tests for the QualityReport class."""

    def test_create_report(self) -> None:
        """Test creating a quality report."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=100.0)
        assert report.passed is True
        assert report.level == QualityLevel.STANDARD
        assert report.score == 100.0

    def test_add_error(self) -> None:
        """Test adding an error."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=100.0)
        report.add_error("Something failed", "test_check")
        assert report.passed is False
        assert report.checks_failed == 1
        assert len(report.errors) == 1
        assert "[test_check]" in report.errors[0]

    def test_add_warning(self) -> None:
        """Test adding a warning."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=100.0)
        report.add_warning("Minor issue")
        assert report.passed is True  # Warnings don't fail
        assert len(report.warnings) == 1

    def test_pass_check(self) -> None:
        """Test passing a check."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=100.0)
        report.pass_check("validation")
        assert report.checks_passed == 1
        assert "✓ validation" in report.info

    def test_skip_check(self) -> None:
        """Test skipping a check."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=100.0)
        report.skip_check("advanced", "Not enabled")
        assert report.checks_skipped == 1
        assert "⊘ advanced" in report.info[0]

    def test_calculate_score(self) -> None:
        """Test score calculation."""
        report = QualityReport(passed=True, level=QualityLevel.STANDARD, score=0.0)
        report.checks_passed = 8
        report.checks_failed = 2
        report.calculate_score()
        assert report.score == 80.0  # 8/10 = 80%

    def test_to_dict(self) -> None:
        """Test serialization."""
        report = QualityReport(passed=True, level=QualityLevel.STRICT, score=95.0)
        data = report.to_dict()
        assert data["passed"] is True
        assert data["level"] == "strict"
        assert data["score"] == 95.0


class TestRuleBasedValidator:
    """Tests for the RuleBasedValidator class."""

    def test_create_validator(self) -> None:
        """Test creating a validator."""
        validator = RuleBasedValidator[str]("test")
        assert validator.get_name() == "test"

    def test_add_rule(self) -> None:
        """Test adding a rule."""
        validator = RuleBasedValidator[str]("test")
        validator.add_rule(
            "not_empty",
            lambda s: len(s) > 0,
            "Value cannot be empty",
        )
        assert len(validator._rules) == 1

    def test_validate_passing(self) -> None:
        """Test validation that passes."""
        validator = RuleBasedValidator[str]("test")
        validator.add_rule("not_empty", lambda s: len(s) > 0, "Cannot be empty")
        report = validator.validate("hello")
        assert report.passed is True
        assert report.checks_passed == 1

    def test_validate_failing(self) -> None:
        """Test validation that fails."""
        validator = RuleBasedValidator[str]("test")
        validator.add_rule("not_empty", lambda s: len(s) > 0, "Cannot be empty")
        report = validator.validate("")
        assert report.passed is False
        assert report.checks_failed == 1

    def test_validate_with_warning(self) -> None:
        """Test validation with warning rule."""
        validator = RuleBasedValidator[str]("test")
        validator.add_rule(
            "length_check",
            lambda s: len(s) >= 5,
            "Should be at least 5 chars",
            is_warning=True,
        )
        report = validator.validate("hi")
        assert report.passed is True  # Warning doesn't fail
        assert len(report.warnings) == 1

    def test_quality_level_filtering(self) -> None:
        """Test that rules are filtered by quality level."""
        validator = RuleBasedValidator[str]("test")
        validator.add_rule(
            "basic",
            lambda s: len(s) > 0,
            "Cannot be empty",
            level=QualityLevel.MINIMAL,
        )
        validator.add_rule(
            "premium_check",
            lambda s: s.isalpha(),
            "Should be alphabetic",
            level=QualityLevel.PREMIUM,
        )

        # At STANDARD level, PREMIUM check should be skipped
        report = validator.validate("test123", QualityLevel.STANDARD)
        assert report.checks_passed == 1
        assert report.checks_skipped == 1


class TestStringValidator:
    """Tests for the StringValidator class."""

    def test_required_string(self) -> None:
        """Test required string validation."""
        validator = StringValidator("name", required=True)
        assert validator.validate("hello").passed is True
        assert validator.validate("").passed is False
        assert validator.validate("   ").passed is False

    def test_min_length(self) -> None:
        """Test minimum length validation."""
        validator = StringValidator("name", min_length=3, required=False)
        assert validator.validate("abc").passed is True
        assert validator.validate("ab").passed is False

    def test_max_length(self) -> None:
        """Test maximum length validation."""
        validator = StringValidator("name", max_length=5, required=False)
        assert validator.validate("hello").passed is True
        assert validator.validate("hello!").passed is False

    def test_pattern(self) -> None:
        """Test pattern validation."""
        validator = StringValidator("email", pattern=r"^[\w]+@[\w]+\.[\w]+$", required=False)
        assert validator.validate("test@example.com").passed is True
        assert validator.validate("invalid").passed is False


class TestNumberValidator:
    """Tests for the NumberValidator class."""

    def test_non_zero(self) -> None:
        """Test non-zero validation."""
        validator = NumberValidator("value", allow_zero=False)
        assert validator.validate(5.0).passed is True
        assert validator.validate(0.0).passed is False

    def test_non_negative(self) -> None:
        """Test non-negative validation."""
        validator = NumberValidator("value", allow_negative=False)
        assert validator.validate(5.0).passed is True
        assert validator.validate(-1.0).passed is False

    def test_min_value(self) -> None:
        """Test minimum value validation."""
        validator = NumberValidator("value", min_value=0.0)
        assert validator.validate(5.0).passed is True
        assert validator.validate(-1.0).passed is False

    def test_max_value(self) -> None:
        """Test maximum value validation."""
        validator = NumberValidator("value", max_value=100.0)
        assert validator.validate(50.0).passed is True
        assert validator.validate(150.0).passed is False


class TestDictValidator:
    """Tests for the DictValidator class."""

    def test_required_keys(self) -> None:
        """Test required keys validation."""
        validator = DictValidator("config", required_keys=["name", "value"])
        assert validator.validate({"name": "test", "value": 1}).passed is True
        assert validator.validate({"name": "test"}).passed is False

    def test_no_extra_keys(self) -> None:
        """Test no extra keys validation."""
        validator = DictValidator(
            "config",
            required_keys=["name"],
            allow_extra_keys=False,
        )
        # Extra keys are checked at STRICT level
        report = validator.validate({"name": "test", "extra": "bad"}, QualityLevel.STRICT)
        assert report.passed is False


class TestQualityAssuranceEngine:
    """Tests for the QualityAssuranceEngine class."""

    def test_create_engine(self) -> None:
        """Test creating an engine."""
        engine = QualityAssuranceEngine(level=QualityLevel.STANDARD)
        assert engine.level == QualityLevel.STANDARD

    def test_register_validator(self) -> None:
        """Test registering a validator."""
        engine = QualityAssuranceEngine()
        validator = StringValidator("name")
        engine.register_validator("name", validator)
        assert "name" in engine._validators

    def test_run_checks(self) -> None:
        """Test running checks."""
        engine = QualityAssuranceEngine()
        engine.register_validator("name", StringValidator("name", min_length=3))
        engine.register_validator("value", NumberValidator("value", min_value=0))

        report = engine.run_checks({"name": "hello", "value": 10.0})
        assert report.passed is True

        report = engine.run_checks({"name": "hi", "value": -5.0})
        assert report.passed is False


class TestEnsureValid:
    """Tests for the ensure_valid function."""

    def test_valid_value(self) -> None:
        """Test with valid value."""
        validator = StringValidator("name", min_length=3)
        ensure_valid("hello", validator)  # Should not raise

    def test_invalid_value(self) -> None:
        """Test with invalid value."""
        validator = StringValidator("name", min_length=3)
        with pytest.raises(ValidationError):
            ensure_valid("hi", validator)
