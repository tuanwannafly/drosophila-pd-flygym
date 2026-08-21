# Validation Experiment Protocol

## Objective

Validate software behavior, reproducibility, computational robustness, or
qualitative literature concordance using existing artifacts and declared
checks.

## Required steps

1. Declare validation class and acceptance semantics before execution.
2. Hash all inputs and record their source commits.
3. Run the smallest relevant validation command.
4. Preserve failed checks and unsupported endpoints in the report.
5. Review the report independently before publication use.

## Boundary

Validation PASS means only that the declared checks passed. It does not imply
biological or clinical validation.
