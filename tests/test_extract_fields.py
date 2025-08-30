import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
async def test_extract_fields_minimal():
    from vertex_grant_agent import extract_fields

    text = "Acme Org seeks $10,000 for STEM program over 12 months."
    class FakeGen:
        def generate_content(self, prompt):
            class R:
                text = ''
            return R()

    data = await extract_fields(text, generator=FakeGen())
    assert 'org' in data and 'project' in data and 'budget' in data
    assert data['budget']['amount'] is not None


