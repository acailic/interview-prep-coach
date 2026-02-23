"""Tests for MemoryStorage."""

import tempfile
from pathlib import Path

import pytest

from interview_prep_coach.conversation import (
    ConversationThread,
    MessageRole,
    WorkingMemory,
)
from interview_prep_coach.conversation.storage import MemoryStorage


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield MemoryStorage(tmpdir)


@pytest.fixture
def sample_thread():
    thread = ConversationThread(user_id="test_user")
    thread.add_message(MessageRole.USER, "Hello")
    thread.add_message(MessageRole.ASSISTANT, "Hi there!")
    return thread


@pytest.fixture
def sample_memory():
    memory = WorkingMemory()
    memory.set_context(company="Acme Corp", position="Engineer", days_until=5)
    memory.add_weakness("systems design")
    memory.add_strength("coding")
    memory.set_preference("detail_level", "high")
    return memory


def test_create_storage_with_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = MemoryStorage(tmpdir)
        assert storage.data_dir.exists()


def test_create_storage_creates_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "new_data_dir"
        assert not new_dir.exists()
        storage = MemoryStorage(new_dir)
        assert storage.data_dir.exists()


def test_save_and_load_thread(storage, sample_thread):
    storage.save_thread(sample_thread)

    loaded = storage.load_thread("test_user")

    assert loaded is not None
    assert loaded.user_id == "test_user"
    assert len(loaded.messages) == 2
    assert loaded.messages[0].content == "Hello"
    assert loaded.messages[0].role == MessageRole.USER
    assert loaded.messages[1].content == "Hi there!"
    assert loaded.messages[1].role == MessageRole.ASSISTANT


def test_load_nonexistent_thread_returns_none(storage):
    result = storage.load_thread("nonexistent_user")
    assert result is None


def test_save_and_load_working_memory(storage, sample_memory):
    storage.save_working_memory("test_user", sample_memory)

    loaded = storage.load_working_memory("test_user")

    assert loaded is not None
    assert loaded.current_context is not None
    assert loaded.current_context.company == "Acme Corp"
    assert loaded.current_context.position == "Engineer"
    assert loaded.current_context.days_until_interview == 5
    assert "systems design" in loaded.recent_weaknesses
    assert "coding" in loaded.recent_strengths
    assert loaded.style_preferences["detail_level"] == "high"


def test_load_nonexistent_working_memory_returns_none(storage):
    result = storage.load_working_memory("nonexistent_user")
    assert result is None


def test_list_users_empty(storage):
    assert storage.list_users() == []


def test_list_users_with_thread(storage, sample_thread):
    storage.save_thread(sample_thread)
    assert storage.list_users() == ["test_user"]


def test_list_users_with_memory(storage, sample_memory):
    storage.save_working_memory("test_user", sample_memory)
    assert storage.list_users() == ["test_user"]


def test_list_users_with_both(storage, sample_thread, sample_memory):
    storage.save_thread(sample_thread)
    storage.save_working_memory("test_user", sample_memory)
    assert storage.list_users() == ["test_user"]


def test_list_users_multiple(storage, sample_thread, sample_memory):
    thread2 = ConversationThread(user_id="user2")
    storage.save_thread(sample_thread)
    storage.save_thread(thread2)
    storage.save_working_memory("user3", sample_memory)

    assert sorted(storage.list_users()) == ["test_user", "user2", "user3"]
