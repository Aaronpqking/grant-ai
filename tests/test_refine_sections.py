import asyncio
import os
import sys
import pytest

# Ensure repo root is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
async def test_refine_updates_only_target(monkeypatch):
    from vertex_grant_agent import InMemoryDAO, Draft, Section, Comment, Anchor, refine_sections_helper, _now_iso, _new_id

    dao = InMemoryDAO()
    draft_id = _new_id('draft')
    sections = [
        Section(id=_new_id('sec'), key='exec_summary', title='Executive Summary', content='AAA'),
        Section(id=_new_id('sec'), key='need', title='Need', content='BBB'),
        Section(id=_new_id('sec'), key='methodology', title='Methodology', content='CCC'),
    ]
    draft = Draft(id=draft_id, title='T', createdAt=_now_iso(), updatedAt=_now_iso(), initialInput={}, sections=sections)
    await dao.create_draft(draft)

    # add one comment to first section
    c = Comment(id=_new_id('c'), draftId=draft_id, sectionId=sections[0].id, anchor=Anchor(startOffset=0, endOffset=0), text='Improve clarity', createdAt=_now_iso())
    await dao.add_comments(draft_id, [c])

    class FakeGen:
        def generate_content(self, prompt):
            class R:
                text = 'AAA refined'
            return R()

    updated, ref = await refine_sections_helper(dao, draft_id, [sections[0].id], None, FakeGen())
    assert len(updated) == 1
    assert updated[0].id == sections[0].id
    # ensure only targeted changed
    new_draft = await dao.get_draft(draft_id)
    id_to = {s.id: s for s in new_draft.sections}
    assert id_to[sections[0].id].content == 'AAA refined'
    assert id_to[sections[1].id].content == 'BBB'
    assert id_to[sections[2].id].content == 'CCC'


