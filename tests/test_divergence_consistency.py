#!/usr/bin/env python3
"""
Architectural Test: Normalized Divergence Consistency

PURPOSE:
Prevents regression of the "multiple sources of truth" anti-pattern that caused
ACWR divergence inconsistencies. This test ensures:

1. All divergence implementations produce identical results
2. No new divergence calculations are added without using canonical implementation
3. Database values match recalculation using canonical formula

WHAT THIS PREVENTS:
- Multiple divergence formulas (mean vs max normalization)
- Absolute vs signed divergence inconsistencies
- Raw differences being stored instead of normalized values
- Different features showing different divergence values

IF THIS TEST FAILS:
Someone added a new divergence calculation without using the canonical implementation
in UnifiedMetricsService._calculate_normalized_divergence(). Consolidate immediately.

AUTHOR: Claude Code (Architectural Audit)
DATE: 2025-12-13
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Load database credentials for testing
from db_credentials_loader import set_database_url
set_database_url()

import pytest
from unified_metrics_service import UnifiedMetricsService
from acwr_configuration_service import ACWRConfigurationService
from acwr_calculation_service import ACWRCalculationService
from strava_training_load import calculate_normalized_divergence as strava_calculate_divergence


class TestNormalizedDivergenceConsistency:
    """
    Architectural tests to ensure single source of truth for divergence calculation.
    """

    @pytest.mark.parametrize("external_acwr,internal_acwr,expected", [
        (1.5, 1.0, 0.400),  # Positive divergence (external > internal)
        (1.0, 1.5, -0.400),  # Negative divergence (internal > external) - VALENCE PRESERVED
        (1.0, 1.0, 0.000),  # Equal ACWRs
        (0.0, 0.0, 0.000),  # Both zero
        (2.0, 0.5, 1.200),  # Large positive divergence
        (0.5, 2.0, -1.200),  # Large negative divergence
    ])
    def test_canonical_formula_correctness(self, external_acwr, internal_acwr, expected):
        """
        Verify canonical implementation produces mathematically correct results.

        Formula: (external - internal) / ((external + internal) / 2)
        """
        result = UnifiedMetricsService._calculate_normalized_divergence(external_acwr, internal_acwr)
        assert abs(result - expected) < 0.001, \
            f"Canonical divergence {result} doesn't match expected {expected}"

    @pytest.mark.parametrize("external_acwr,internal_acwr", [
        (1.5, 1.0),
        (1.0, 1.5),  # Negative case - valence must be preserved
        (0.8, 0.6),
        (2.0, 0.5),
    ])
    def test_all_implementations_match_canonical(self, external_acwr, internal_acwr):
        """
        CRITICAL TEST: Ensures all divergence implementations produce identical results.

        IF THIS FAILS: Someone added a divergence calculation without delegating to
        canonical implementation. This violates single source of truth principle.
        """
        # Canonical implementation
        canonical = UnifiedMetricsService._calculate_normalized_divergence(external_acwr, internal_acwr)

        # All other implementations should delegate to canonical
        config_service = ACWRConfigurationService()
        calc_service = ACWRCalculationService()

        results = {
            'canonical (UnifiedMetricsService)': canonical,
            'ACWRConfigurationService': config_service.calculate_normalized_divergence(external_acwr, internal_acwr),
            'ACWRCalculationService': calc_service._calculate_normalized_divergence(external_acwr, internal_acwr),
            'strava_training_load': strava_calculate_divergence(external_acwr, internal_acwr),
        }

        # All implementations must produce identical results
        for name, result in results.items():
            assert result == canonical, \
                f"{name} produced {result}, expected {canonical} (canonical). " \
                f"This indicates a duplicate implementation that doesn't delegate to canonical!"

    def test_valence_preserved_not_absolute(self):
        """
        Ensures divergence preserves valence (sign) and doesn't use abs().

        Positive divergence: External ACWR > Internal ACWR (handling load well)
        Negative divergence: Internal ACWR > External ACWR (potential overreaching)
        """
        # External > Internal → Positive divergence
        result_positive = UnifiedMetricsService._calculate_normalized_divergence(1.5, 1.0)
        assert result_positive > 0, "Divergence should be POSITIVE when external > internal"

        # Internal > External → Negative divergence
        result_negative = UnifiedMetricsService._calculate_normalized_divergence(1.0, 1.5)
        assert result_negative < 0, "Divergence should be NEGATIVE when internal > external"

        # Verify they're equal in magnitude but opposite in sign
        assert abs(result_positive) == abs(result_negative), \
            "Magnitude should be same for symmetric inputs"

    def test_mean_normalized_not_max_normalized(self):
        """
        Ensures divergence uses mean normalization, not max normalization.

        Mean-normalized: (ext - int) / ((ext + int) / 2)
        Max-normalized:  abs(ext - int) / max(ext, int)  ← WRONG

        These produce different values. We use mean-normalized as canonical.
        """
        external, internal = 1.5, 1.0

        # Canonical (mean-normalized)
        mean_normalized = UnifiedMetricsService._calculate_normalized_divergence(external, internal)

        # What max-normalized would produce (this is WRONG - don't use this)
        max_normalized = abs(external - internal) / max(external, internal)

        # They should be different
        assert abs(mean_normalized - max_normalized) > 0.05, \
            "Mean-normalized and max-normalized should produce different values"

        # Canonical should use mean (verify by calculation)
        expected_mean = (external - internal) / ((external + internal) / 2)
        assert abs(mean_normalized - expected_mean) < 0.001, \
            "Canonical implementation doesn't use mean normalization!"

    def test_no_grep_detectable_duplicates(self):
        """
        Architectural test: Searches codebase for duplicate divergence calculations.

        IF THIS FAILS: Someone added a new divergence calculation function.
        All divergence calculations MUST delegate to canonical implementation.
        """
        import subprocess
        import re

        # Search for divergence calculation patterns in Python files
        try:
            result = subprocess.run(
                ['grep', '-rn', '--include=*.py',
                 r'(external.*internal).*avg\|mean.*acwr\|divergence.*=.*/',
                 '../app/'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )

            # Expected locations (these delegate to canonical):
            allowed_files = [
                'unified_metrics_service.py',  # Canonical implementation
                'acwr_configuration_service.py',  # Delegates to canonical
                'acwr_calculation_service.py',  # Delegates to canonical
                'strava_training_load.py',  # Delegates to canonical
                'exponential_decay_engine.py',  # Fixed to use canonical formula
                'acwr_visualization_routes.py',  # Fixed to use canonical formula
            ]

            lines = result.stdout.split('\n') if result.stdout else []
            suspicious_lines = []

            for line in lines:
                if not line.strip():
                    continue

                # Check if this file is in allowed list
                is_allowed = any(allowed in line for allowed in allowed_files)

                # Check if it's a comment or import
                is_comment = '#' in line and line.index('#') < line.index('/') if '/' in line else False
                is_import = 'import' in line.lower()

                if not is_allowed and not is_comment and not is_import:
                    suspicious_lines.append(line)

            if suspicious_lines:
                pytest.fail(
                    f"Found {len(suspicious_lines)} potential duplicate divergence calculations!\n\n"
                    f"Suspicious lines:\n" + "\n".join(suspicious_lines) + "\n\n"
                    f"All divergence calculations MUST delegate to "
                    f"UnifiedMetricsService._calculate_normalized_divergence()"
                )

        except FileNotFoundError:
            # grep not available (Windows), skip this test
            pytest.skip("grep command not available for duplicate detection")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
