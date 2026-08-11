from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse


DEFAULT_BRAND_REGISTRY = Path("brand_official_websites.csv")


@dataclass(frozen=True)
class BrandRecord:
    canonical_name: str
    official_website: str
    domain: str
    normalized_key: str
    aliases: tuple[str, ...]


def normalize_brand_key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


@lru_cache(maxsize=1)
def load_brand_registry(path: str = str(DEFAULT_BRAND_REGISTRY)) -> Dict[str, BrandRecord]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {}

    records: Dict[str, BrandRecord] = {}
    with registry_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            brand_name = (row.get("brand_name") or "").strip()
            website = (row.get("official_website") or "").strip()
            if not brand_name or not website:
                continue
            normalized = normalize_brand_key(brand_name)
            domain = _domain_from_url(website)
            aliases = tuple(_brand_aliases(brand_name))
            record = BrandRecord(
                canonical_name=brand_name,
                official_website=website,
                domain=domain,
                normalized_key=normalized,
                aliases=aliases,
            )
            for alias in aliases:
                records[normalize_brand_key(alias)] = record
    return records


def find_brand_record(name: str, path: str = str(DEFAULT_BRAND_REGISTRY)) -> Optional[BrandRecord]:
    registry = load_brand_registry(path)
    if not registry:
        return None

    normalized = normalize_brand_key(name)
    if normalized in registry:
        return registry[normalized]

    lowered = name.lower()
    for record in dict.fromkeys(registry.values()):
        alias_matches = sorted(record.aliases, key=len, reverse=True)
        if any(alias.lower() in lowered for alias in alias_matches):
            return record
    return None


def known_brand_names(path: str = str(DEFAULT_BRAND_REGISTRY)) -> List[str]:
    registry = load_brand_registry(path)
    unique = {record.canonical_name for record in registry.values()}
    return sorted(unique, key=len, reverse=True)


def _domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def _brand_aliases(brand_name: str) -> List[str]:
    aliases = {brand_name.strip()}
    normalized = brand_name.strip()
    aliases.add(normalized.upper())
    aliases.add(normalized.lower())

    compact = normalized.replace(" ", "")
    aliases.add(compact)
    aliases.add(compact.upper())
    aliases.add(compact.lower())

    if normalized.lower() == "one plus":
        aliases.add("OnePlus")
    if normalized.lower() == "oneplus":
        aliases.add("One Plus")
    if normalized.lower() == "oak & iron":
        aliases.add("Oak & iron tech")
    if normalized.lower() == "oak & iron tech":
        aliases.add("Oak & iron")
    if normalized.lower() == "flux":
        aliases.add("Flux Keyboard")
    if normalized.lower() == "flux keyboard":
        aliases.add("Flux")
    return [alias for alias in aliases if alias]
