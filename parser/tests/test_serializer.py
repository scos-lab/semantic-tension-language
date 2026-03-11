#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for serializer.py

Tests serialization and deserialization of STL ParseResult objects
to/from JSON and dictionary formats, including round-trip fidelity.
"""

import pytest
import json

from stl_parser.models import Anchor, Modifier, Statement, ParseResult, ParseError, ParseWarning
from stl_parser.parser import parse
from stl_parser.serializer import STLSerializer, to_json, from_json, to_dict, from_dict, to_stl, to_rdf
from stl_parser.errors import STLSerializationError, ErrorCode


@pytest.fixture
def sample_parse_result_valid():
    """Returns a valid ParseResult object for testing."""
    stmt1 = Statement(
        source=Anchor(name="Theory_Relativity"),
        target=Anchor(name="Prediction_TimeDilation"),
        modifiers=Modifier(
            rule="logical",
            confidence=0.99,
            author="Einstein",
            time="2025-01-20T10:00:00Z"
        )
    )
    stmt2 = Statement(
        source=Anchor(name="Prediction_TimeDilation"),
        target=Anchor(name="Experiment_GPS"),
        modifiers=Modifier(
            rule="empirical",
            strength=0.95
        )
    )
    return ParseResult(statements=[stmt1, stmt2], is_valid=True)


@pytest.fixture
def sample_parse_result_with_errors_warnings():
    """Returns a ParseResult with errors and warnings for testing."""
    stmt = Statement(source=Anchor(name="A"), target=Anchor(name="B"))
    errors = [ParseError(code="E100", message="Invalid anchor", line=1)]
    warnings = [ParseWarning(code="W003", message="Low confidence", line=1)]
    return ParseResult(statements=[stmt], errors=errors, warnings=warnings, is_valid=False)


class TestSTLSerializer:
    """Tests the STLSerializer class methods."""

    def test_to_dict(self, sample_parse_result_valid):
        """Test serialization to dictionary."""
        serializer = STLSerializer()
        data = serializer.to_dict(sample_parse_result_valid)

        assert isinstance(data, dict)
        assert "statements" in data
        assert len(data["statements"]) == 2
        assert data["statements"][0]["source"]["name"] == "Theory_Relativity"
        assert data["statements"][0]["modifiers"]["confidence"] == 0.99
        assert not data.get("errors")  # Use .get() for safe access
        assert not data.get("warnings") # Use .get() for safe access
        assert data["is_valid"] is True

    def test_to_json(self, sample_parse_result_valid):
        """Test serialization to JSON string."""
        serializer = STLSerializer()
        json_string = serializer.to_json(sample_parse_result_valid, indent=None)

        assert isinstance(json_string, str)
        # Verify it's valid JSON
        parsed_json = json.loads(json_string)
        assert len(parsed_json["statements"]) == 2
        assert parsed_json["statements"][0]["source"]["name"] == "Theory_Relativity"

    def test_to_json_indented(self, sample_parse_result_valid):
        """Test serialization to indented JSON string."""
        serializer = STLSerializer()
        json_string = serializer.to_json(sample_parse_result_valid, indent=2)

        assert isinstance(json_string, str)
        # Check for indentation (simple check for newlines)
        assert "\n" in json_string
        parsed_json = json.loads(json_string)
        assert parsed_json["statements"][0]["source"]["name"] == "Theory_Relativity"

    def test_to_rdf(self, sample_parse_result_valid):
        """Test serialization to RDF string."""
        pytest.importorskip("rdflib")
        serializer = STLSerializer()
        rdf_string = serializer.to_rdf(sample_parse_result_valid, format="turtle")
        
        assert isinstance(rdf_string, str)
        assert "stl:Theory_Relativity" in rdf_string
        assert "stl:Prediction_TimeDilation" in rdf_string
        assert "stl:confidence" in rdf_string
        # Floating point numbers might be serialized in scientific notation (e.g. 9.9e-01)
        assert '9.9e-01' in rdf_string or '0.99' in rdf_string
        assert '9.5e-01' in rdf_string or '0.95' in rdf_string

    def test_from_dict(self, sample_parse_result_valid):
        """Test deserialization from dictionary."""
        serializer = STLSerializer()
        data = serializer.to_dict(sample_parse_result_valid)
        deserialized_result = serializer.from_dict(data)

        assert isinstance(deserialized_result, ParseResult)
        assert deserialized_result.is_valid == sample_parse_result_valid.is_valid
        assert len(deserialized_result.statements) == len(sample_parse_result_valid.statements)
        assert deserialized_result.statements[0].source.name == "Theory_Relativity"
        assert deserialized_result.statements[0].modifiers.confidence == 0.99

    def test_from_json(self, sample_parse_result_valid):
        """Test deserialization from JSON string."""
        serializer = STLSerializer()
        json_string = serializer.to_json(sample_parse_result_valid)
        deserialized_result = serializer.from_json(json_string)

        assert isinstance(deserialized_result, ParseResult)
        assert deserialized_result.is_valid == sample_parse_result_valid.is_valid
        assert len(deserialized_result.statements) == len(sample_parse_result_valid.statements)
        assert deserialized_result.statements[0].source.name == "Theory_Relativity"
        assert deserialized_result.statements[0].modifiers.confidence == 0.99

    def test_from_dict_invalid_data(self):
        """Test from_dict with invalid data, expecting STLSerializationError."""
        serializer = STLSerializer()
        invalid_data = {"statements": [{"source": {"name": "A"}}, {"invalid_field": "val"}]} # Missing target, etc.
        with pytest.raises(STLSerializationError) as excinfo:
            serializer.from_dict(invalid_data)
        assert excinfo.value.code == ErrorCode.E200_SERIALIZATION_FAILED

    def test_from_json_invalid_json_string(self):
        """Test from_json with malformed JSON string, expecting STLSerializationError."""
        serializer = STLSerializer()
        invalid_json = "{'statements': [invalid, json]}"
        with pytest.raises(STLSerializationError) as excinfo:
            serializer.from_json(invalid_json)
        assert excinfo.value.code == ErrorCode.E201_INVALID_JSON

    def test_serialization_of_errors_warnings(self, sample_parse_result_with_errors_warnings):
        """Test serialization and deserialization of ParseResult with errors and warnings."""
        serializer = STLSerializer()
        json_string = serializer.to_json(sample_parse_result_with_errors_warnings)
        deserialized_result = serializer.from_json(json_string)

        assert not deserialized_result.is_valid
        assert len(deserialized_result.errors) == 1
        assert deserialized_result.errors[0].code == "E100"
        assert len(deserialized_result.warnings) == 1
        assert deserialized_result.warnings[0].code == "W003"


class TestSTLSerializerConvenienceFunctions:
    """Tests the convenience functions directly exported by serializer module."""

    def test_to_dict_func(self, sample_parse_result_valid):
        data = to_dict(sample_parse_result_valid)
        assert isinstance(data, dict)
        assert data["statements"][0]["source"]["name"] == "Theory_Relativity"

    def test_to_json_func(self, sample_parse_result_valid):
        json_string = to_json(sample_parse_result_valid, indent=None)
        assert isinstance(json_string, str)
        parsed_json = json.loads(json_string)
        assert parsed_json["statements"][0]["source"]["name"] == "Theory_Relativity"

    def test_to_rdf_func(self, sample_parse_result_valid):
        pytest.importorskip("rdflib")
        rdf_string = to_rdf(sample_parse_result_valid, format="turtle")
        assert isinstance(rdf_string, str)
        assert "stl:Theory_Relativity" in rdf_string

    def test_from_dict_func(self, sample_parse_result_valid):
        data = to_dict(sample_parse_result_valid)
        deserialized_result = from_dict(data)
        assert deserialized_result.statements[0].source.name == "Theory_Relativity"

    def test_from_json_func(self, sample_parse_result_valid):
        json_string = to_json(sample_parse_result_valid)
        deserialized_result = from_json(json_string)
        assert deserialized_result.statements[0].source.name == "Theory_Relativity"

    def test_to_stl_func(self, sample_parse_result_valid):
        stl_string = to_stl(sample_parse_result_valid)
        assert isinstance(stl_string, str)
        assert "[Theory_Relativity] -> [Prediction_TimeDilation]" in stl_string
        # Check for key-value pairs individually to avoid order dependency
        assert 'rule="logical"' in stl_string
        assert 'confidence=0.99' in stl_string
        assert 'author="Einstein"' in stl_string
        assert 'time="2025-01-20T10:00:00Z"' in stl_string


class TestRDFSerialization:
    """Tests specific RDF serialization details."""
    
    def test_rdf_content_structure(self, sample_parse_result_valid):
        """Verify RDF content structure using rdflib."""
        rdflib = pytest.importorskip("rdflib")
        
        serializer = STLSerializer()
        rdf_string = serializer.to_rdf(sample_parse_result_valid, format="turtle")
        
        g = rdflib.Graph()
        g.parse(data=rdf_string, format="turtle")
        
        # Check triples count
        # 2 statements. Each has:
        # 1 direct triple: S P O
        # 1 reified statement node: 
        #   Stmt a rdf:Statement (1)
        #   Stmt rdf:subject S (1)
        #   Stmt rdf:predicate P (1)
        #   Stmt rdf:object O (1)
        #   Plus modifiers (4 for stmt1, 2 for stmt2)
        
        # Total expected triples:
        # Stmt1: 1 + 4 (reification structure) + 4 (modifiers) = 9
        # Stmt2: 1 + 4 + 2 = 7
        # Total = 16
        
        assert len(g) == 16
        
        # Verify namespace binding
        assert ("stl", rdflib.URIRef("http://stl.scos.dev/ontology/")) in g.namespaces()
        
        # Verify specific triple existence
        STL = rdflib.Namespace("http://stl.scos.dev/ontology/")
        
        # Check for Theory_Relativity node usage
        term = STL.Theory_Relativity
        assert (term, None, None) in g or (None, None, term) in g


