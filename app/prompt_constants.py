"""Shared prompt constants for LLM prompt builders."""

NORMALIZED_DIVERGENCE_FORMULA = (
    "Normalized Divergence = (External ACWR − Internal ACWR) / avg(External, Internal). "
    "POSITIVE = External > Internal (safe). NEGATIVE = Internal > External (risk, threshold < −0.15). "
    "See Training Reference Guide for full interpretation."
)
