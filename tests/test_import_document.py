import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
async def test_import_text_document_flow():
    from vertex_grant_agent import extract_text
    content = b"Title: STEM Program\nBudget: $5,000\nTimeline: 6 months\n"
    text = await extract_text(content, filename='sample.txt')
    assert 'STEM Program' in text


