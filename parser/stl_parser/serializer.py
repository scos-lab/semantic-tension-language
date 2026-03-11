# -*- coding: utf-8 -*-
"""
STL Parser Serializer

This module provides functionality to serialize STL ParseResult objects
to various formats (e.g., JSON, YAML) and deserialize them back.
"""

import json
from typing import Dict, Any, Union, Optional
from pydantic import ValidationError

# Optional import for rdflib to avoid hard dependency if not installed (though it is in requirements)
try:
    from rdflib import Graph, URIRef, Literal, BNode, RDF, RDFS, Namespace
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False

from .models import ParseResult, Statement, Anchor, Modifier, ParseError, ParseWarning
from .errors import STLSerializationError, ErrorCode


class STLSerializer:
    """
    Serializes and deserializes STL ParseResult objects.
    Leverages Pydantic's serialization capabilities for efficiency and consistency.
    """

    def __init__(self):
        pass

    def to_dict(self, parse_result: ParseResult) -> Dict[str, Any]:
        """
        Serializes a ParseResult object to a Python dictionary.

        Args:
            parse_result: The ParseResult object to serialize.

        Returns:
            A dictionary representation of the ParseResult.
        """
        return parse_result.model_dump(mode='json', exclude_unset=True)

    def to_json(self, parse_result: ParseResult, indent: Optional[int] = 2) -> str:
        """
        Serializes a ParseResult object to a JSON string.

        Args:
            parse_result: The ParseResult object to serialize.
            indent: Number of spaces for JSON indentation. None for compact output.

        Returns:
            A JSON string representation of the ParseResult.
        """
        return parse_result.model_dump_json(indent=indent, exclude_unset=True)

    def to_rdf(self, parse_result: ParseResult, format: str = "turtle") -> str:
        """
        Serializes a ParseResult object to an RDF string.
        Uses standard reification to attach modifiers to statements.

        Args:
            parse_result: The ParseResult object to serialize.
            format: The RDF format (e.g., "turtle", "xml", "nt").

        Returns:
            An RDF string representation of the ParseResult.

        Raises:
            STLSerializationError: If rdflib is not installed or serialization fails.
        """
        if not RDFLIB_AVAILABLE:
            raise STLSerializationError(
                code=ErrorCode.E200_SERIALIZATION_FAILED,
                message="rdflib is not installed. Cannot serialize to RDF."
            )

        try:
            g = Graph()
            STL = Namespace("http://stl.scos.dev/ontology/")
            g.bind("stl", STL)

            for stmt in parse_result.statements:
                # Create Subject and Object nodes
                subj = self._create_rdf_node(stmt.source, STL)
                obj = self._create_rdf_node(stmt.target, STL)

                # Determine Predicate
                # Default to 'relatedTo', use 'rule' or 'path_type' if available for more specific relation
                pred = STL.relatedTo
                if stmt.modifiers and stmt.modifiers.rule:
                    pred = STL[stmt.modifiers.rule]
                elif stmt.path_type:
                    pred = STL[stmt.path_type.value.lower()]

                # Add the direct triple (Subject, Predicate, Object)
                g.add((subj, pred, obj))

                # Reification: Create a Statement node to attach modifiers
                # [StmtNode] a rdf:Statement; rdf:subject S; rdf:predicate P; rdf:object O
                stmt_node = BNode()
                g.add((stmt_node, RDF.type, RDF.Statement))
                g.add((stmt_node, RDF.subject, subj))
                g.add((stmt_node, RDF.predicate, pred))
                g.add((stmt_node, RDF.object, obj))

                # Add modifiers to the statement node
                if stmt.modifiers:
                    mod_dict = stmt.modifiers.model_dump(exclude_none=True, exclude={'custom'})
                    for k, v in mod_dict.items():
                        g.add((stmt_node, STL[k], Literal(v)))
                    
                    # Add custom modifiers
                    if stmt.modifiers.custom:
                        for k, v in stmt.modifiers.custom.items():
                            g.add((stmt_node, STL[k], Literal(v)))

            return g.serialize(format=format)

        except Exception as e:
            raise STLSerializationError(
                code=ErrorCode.E203_INVALID_RDF,
                message=f"RDF serialization failed: {e}",
                context={"original_error": str(e)}
            )

    def _create_rdf_node(self, anchor: Anchor, namespace: Any) -> Any:
        """Helper to create an RDF node from an Anchor."""
        # Use namespace + name as URI fragment
        # Sanitize name for URI compatibility if needed, but rdflib handles most utf-8
        name = anchor.name
        if anchor.namespace:
            name = f"{anchor.namespace}.{name}"
        
        # Simple URI construction
        return namespace[name]

    def from_dict(self, data: Dict[str, Any]) -> ParseResult:
        """
        Deserializes a dictionary into a ParseResult object.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A ParseResult object.

        Raises:
            STLSerializationError: If deserialization fails due to invalid data format.
        """
        try:
            return ParseResult.model_validate(data)
        except ValidationError as e:
            raise STLSerializationError(
                code=ErrorCode.E200_SERIALIZATION_FAILED,
                message=f"Failed to deserialize from dict: {e}",
                context={"validation_errors": e.errors()}
            )

    def from_json(self, json_string: str) -> ParseResult:
        """
        Deserializes a JSON string into a ParseResult object.

        Args:
            json_string: The JSON string to deserialize.

        Returns:
            A ParseResult object.

        Raises:
            STLSerializationError: If deserialization fails due to invalid JSON or data format.
        """
        try:
            data = json.loads(json_string)
            return self.from_dict(data)
        except json.JSONDecodeError as e:
            raise STLSerializationError(
                code=ErrorCode.E201_INVALID_JSON,
                message=f"Failed to decode JSON string: {e}",
                context={"json_error": str(e)}
            )
        except STLSerializationError as e:
            # Re-raise STLSerializationError from from_dict
            raise e
        except Exception as e:
            raise STLSerializationError(
                code=ErrorCode.E200_SERIALIZATION_FAILED,
                message=f"An unexpected error occurred during JSON deserialization: {e}",
                context={"original_error": str(e)}
            )

    def to_stl(self, parse_result: ParseResult) -> str:
        """
        Converts a ParseResult object back into an STL formatted string.

        Args:
            parse_result: The ParseResult object to convert.

        Returns:
            A string containing the STL representation of the statements.
        """
        return "\n".join(str(stmt) for stmt in parse_result.statements)


# Convenience functions for direct use without instantiating STLSerializer
_serializer_instance = STLSerializer()

def to_dict(parse_result: ParseResult) -> Dict[str, Any]:
    return _serializer_instance.to_dict(parse_result)

def to_json(parse_result: ParseResult, indent: Optional[int] = 2) -> str:
    return _serializer_instance.to_json(parse_result, indent)

def to_rdf(parse_result: ParseResult, format: str = "turtle") -> str:
    return _serializer_instance.to_rdf(parse_result, format)

def from_dict(data: Dict[str, Any]) -> ParseResult:
    return _serializer_instance.from_dict(data)

def from_json(json_string: str) -> ParseResult:
    return _serializer_instance.from_json(json_string)

def to_stl(parse_result: ParseResult) -> str:
    return _serializer_instance.to_stl(parse_result)
