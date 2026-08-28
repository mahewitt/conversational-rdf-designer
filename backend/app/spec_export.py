"""Render the semantic graph as a spec-kit-style feature specification (spec.md)."""

from typing import Any


def generate_speckit_spec(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    namespace: dict[str, str] | None = None,
) -> str:
    """Turn the current ontology into a spec-kit `/specify`-compatible spec.md.

    The result is a plain functional specification (entities, relationships,
    and requirements) with no implementation detail, so it can seed a
    spec-kit `/plan` and `/tasks` workflow that builds the data product.
    """
    namespace = namespace or {}
    prefix = namespace.get("prefix", "vg")
    ns = namespace.get("namespace", "http://example.com/vibegraph#")
    title = f"{prefix.upper()} Data Product Specification"

    lines: list[str] = [
        f"# Feature Specification: {title}",
        "",
        "**Status**: Draft",
        f"**Source**: Generated from semantic model ({len(nodes)} entities, {len(edges)} relationships)",
        f"**Ontology namespace**: `{prefix}: {ns}`",
        "",
        "## Summary",
        "",
        f"A data product that exposes the **{title}** domain model as queryable, governed entities "
        "with defined relationships, semantics, and lineage.",
        "",
        "## Key Entities",
        "",
    ]

    for node in nodes:
        label = _label(node)
        description = _description(node)
        properties = _properties(node)
        lines.append(f"- **{label}** — {description}")
        if properties:
            attribute_list = ", ".join(_format_attribute(key, value) for key, value in properties.items())
            lines.append(f"  - Attributes: {attribute_list}")
        outgoing = [f"{label} {edge['label']} {_label_by_id(nodes, edge['target'])}" for edge in edges if edge["source"] == node["id"]]
        if outgoing:
            lines.append(f"  - Relationships: {'; '.join(outgoing)}")

    lines += ["", "## Functional Requirements", ""]
    requirement_number = 1
    for node in nodes:
        label = _label(node)
        fields = ["id", *list(_properties(node).keys())]
        lines.append(f"- FR-{requirement_number:03d}: System MUST expose a `{label}` entity with fields: {', '.join(fields)}.")
        requirement_number += 1
    for edge in edges:
        source_label = _label_by_id(nodes, edge["source"])
        target_label = _label_by_id(nodes, edge["target"])
        lines.append(
            f'- FR-{requirement_number:03d}: System MUST enforce the relationship "{source_label} {edge["label"]} '
            f'{target_label}" with referential integrity.'
        )
        requirement_number += 1
    lines.append(
        f"- FR-{requirement_number:03d}: System MUST publish the data product schema as OWL/RDF for semantic "
        "discoverability (see the accompanying .ttl export)."
    )

    lines += [
        "",
        "## Non-Functional Considerations",
        "",
        "- Data quality rules and freshness SLAs are not yet defined and should be captured during `/plan`.",
        "- Access control and data classification should be confirmed with the data governance owner.",
        "",
        "## Out of Scope",
        "",
        "- Ingestion pipelines, orchestration schedules, and UI are not defined by this specification.",
        "",
        "## Review Checklist",
        "",
        "- [ ] Every entity has an owner and a data quality rule",
        "- [ ] Every relationship has a defined cardinality",
        "- [ ] Namespace and versioning strategy agreed with governance",
        "",
        "## Appendix: Ontology Reference",
        "",
        "This specification was generated from the accompanying OWL/Turtle ontology. Refer to the exported .ttl "
        "file for the full machine-readable class and property definitions.",
        "",
    ]
    return "\n".join(lines)


def _label(node: dict[str, Any]) -> str:
    return node.get("data", {}).get("label", node["id"])


def _label_by_id(nodes: list[dict[str, Any]], node_id: str) -> str:
    return next((_label(node) for node in nodes if node["id"] == node_id), node_id)


def _description(node: dict[str, Any]) -> str:
    return node.get("data", {}).get("description") or f"A {_label(node)} in this semantic model."


def _properties(node: dict[str, Any]) -> dict[str, Any]:
    return node.get("data", {}).get("properties", {}) or {}


def _format_attribute(key: str, value: Any) -> str:
    return f"{key} ({value})" if value not in (None, "") else key
