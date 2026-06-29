from __future__ import annotations

import re
from dataclasses import dataclass

NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


@dataclass(slots=True)
class FiscalValidationResult:
    is_valid: bool
    formatted: str | None = None
    error_message: str | None = None


def validate(document_type: str, document_number: str, country_code: str) -> FiscalValidationResult:
    normalized_type = document_type.strip().upper()
    normalized_number = document_number.strip().upper()
    normalized_country = country_code.strip().upper()

    if normalized_type == "RUC" and normalized_country == "PER":
        return _validate_ruc(normalized_number)
    if normalized_type == "DNI" and normalized_country == "PER":
        return _validate_dni(normalized_number)
    if normalized_type == "CEDULA_FISICA" and normalized_country == "CRI":
        return _validate_cri_cedula_fisica(normalized_number)
    if normalized_type == "CEDULA_JURIDICA" and normalized_country == "CRI":
        return _validate_cri_cedula_juridica(normalized_number)
    if normalized_type == "NIF" and normalized_country == "ESP":
        return _validate_nif(normalized_number)
    if normalized_type == "NIE" and normalized_country == "ESP":
        return _validate_nie(normalized_number)
    return FiscalValidationResult(is_valid=True, formatted=normalized_number)


def _validate_ruc(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"\d{11}", number):
        return FiscalValidationResult(False, error_message="RUC invalido para Peru")
    factors = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    total = sum(int(digit) * factor for digit, factor in zip(number[:10], factors, strict=True))
    remainder = 11 - (total % 11)
    verifier = {10: 0, 11: 1}.get(remainder, remainder)
    if verifier != int(number[-1]):
        return FiscalValidationResult(False, error_message="RUC invalido para Peru")
    return FiscalValidationResult(True, formatted=number)


def _validate_dni(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"\d{8}", number):
        return FiscalValidationResult(False, error_message="DNI invalido para Peru")
    return FiscalValidationResult(True, formatted=number)


def _validate_cri_cedula_fisica(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"\d-\d{4}-\d{4}", number):
        return FiscalValidationResult(False, error_message="Cedula fisica invalida para Costa Rica")
    return FiscalValidationResult(True, formatted=number)


def _validate_cri_cedula_juridica(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"\d-\d{3}-\d{6}", number):
        return FiscalValidationResult(
            False, error_message="Cedula juridica invalida para Costa Rica"
        )
    return FiscalValidationResult(True, formatted=number)


def _validate_nif(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"\d{8}[A-Z]", number):
        return FiscalValidationResult(False, error_message="NIF invalido para Espana")
    expected = NIF_LETTERS[int(number[:8]) % 23]
    if number[-1] != expected:
        return FiscalValidationResult(False, error_message="NIF invalido para Espana")
    return FiscalValidationResult(True, formatted=number)


def _validate_nie(number: str) -> FiscalValidationResult:
    if not re.fullmatch(r"[XYZ]\d{7}[A-Z]", number):
        return FiscalValidationResult(False, error_message="NIE invalido para Espana")
    prefix = {"X": "0", "Y": "1", "Z": "2"}[number[0]]
    base = int(prefix + number[1:8])
    expected = NIF_LETTERS[base % 23]
    if number[-1] != expected:
        return FiscalValidationResult(False, error_message="NIE invalido para Espana")
    return FiscalValidationResult(True, formatted=number)
