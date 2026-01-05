import pytest
from pathlib import Path
from datetime import datetime
from src.cctop.parsers.jsonl_parser import JSONLParser
from src.cctop.models.usage import TokenUsage


def test_parse_log_file():
    test_file = Path(__file__).parent / "fixtures" / "sample_logs.jsonl"
    parser = JSONLParser()

    entries = parser.parse_log_file(test_file)

    assert len(entries) == 4
    assert entries[0]['type'] == 'user'
    assert entries[1]['type'] == 'assistant'


def test_extract_usage_data():
    parser = JSONLParser()

    log_entry = {
        'timestamp': '2026-01-04T10:00:05Z',
        'requestId': 'req-789',
        'message': {
            'model': 'claude-sonnet-4-5-20250929',
            'usage': {
                'input_tokens': 100,
                'output_tokens': 50,
                'cache_creation_input_tokens': 10,
                'cache_read_input_tokens': 5,
            }
        }
    }

    usage = parser.extract_usage_data(log_entry)

    assert usage is not None
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.cache_creation_tokens == 10
    assert usage.cache_read_tokens == 5
    assert usage.model == 'claude-sonnet-4-5-20250929'
    assert usage.request_id == 'req-789'


def test_get_agent_info_from_log():
    test_file = Path(__file__).parent / "fixtures" / "sample_logs.jsonl"
    parser = JSONLParser()

    entries = parser.parse_log_file(test_file)
    agent_info = parser.get_agent_info_from_log(entries)

    assert agent_info['agent_id'] == 'test-agent-123'
    assert agent_info['slug'] == 'test-agent'
    assert agent_info['session_id'] == 'session-456'
    assert agent_info['total_input_tokens'] == 250
    assert agent_info['total_output_tokens'] == 125
    assert agent_info['total_cache_creation_tokens'] == 10
    assert agent_info['total_cache_read_tokens'] == 25
    assert agent_info['message_count'] == 4
    assert agent_info['model'] == 'claude-sonnet-4-5-20250929'


def test_is_waiting_for_user():
    test_file = Path(__file__).parent / "fixtures" / "sample_logs.jsonl"
    parser = JSONLParser()

    entries = parser.parse_log_file(test_file)

    is_waiting = parser.is_waiting_for_user(entries)
    assert is_waiting is True


def test_nonexistent_file():
    parser = JSONLParser()
    entries = parser.parse_log_file(Path("/nonexistent/file.jsonl"))
    assert entries == []


def test_empty_usage():
    parser = JSONLParser()

    log_entry = {
        'timestamp': '2026-01-04T10:00:05Z',
        'message': {}
    }

    usage = parser.extract_usage_data(log_entry)
    assert usage is None
