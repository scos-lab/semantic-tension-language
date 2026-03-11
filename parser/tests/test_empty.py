from stl_parser.parser import parse

def test_empty_string():
    result = parse("")
    assert result.is_valid
    assert len(result.statements) == 0

def test_whitespace_string():
    result = parse("   \n  ")
    assert result.is_valid
    assert len(result.statements) == 0

