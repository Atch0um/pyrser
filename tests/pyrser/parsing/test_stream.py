import unittest

from pyrser.parsing import Stream
from pyrser.parsing.parserStream import Position


class TestParserStream(unittest.TestCase):
    def test_it_increments_position(self):
        stream = Stream(" ")
        prev_pos = stream.index
        stream.incpos()
        self.assertLess(prev_pos, stream.index)

    def test_it_increments_position_on_newline(self):
        stream = Stream("\n")
        prev_line = stream.lineno
        stream.incpos()
        self.assertEqual(1, stream.col_offset)
        self.assertLess(prev_line, stream.lineno)

    def test_it_does_not_increment_position_passed_eof(self):
        stream = Stream("")
        pos = stream.index
        stream.incpos()
        self.assertEqual(pos, stream.index)

    def test_it_decrements_position(self):
        stream = Stream("a")
        stream._cursor.step_next_char()
        stream.decpos()
        self.assertEqual(0, stream.index)

    def test_it_decrements_position_on_newline(self):
        stream = Stream("\n")
        stream._cursor.step_next_line()
        stream._cursor.step_next_char()
        stream.decpos()
        self.assertEqual(1, stream.lineno)

    def test_it_does_not_decrement_position_before_bof(self):
        stream = Stream("")
        stream.decpos()
        self.assertEqual(0, stream.index)

    def test_it_saves_context(self):
        stream = Stream()
        contexts = stream._contexts
        nb_ctx = len(contexts)
        stream.save_context()
        self.assertEqual(nb_ctx + 1, len(contexts))

    def test_it_restore_context(self):
        stream = Stream()
        pos = Position(42, 0, 0)
        stream._contexts.insert(0, pos)
        stream.restore_context()
        self.assertEqual(pos.index, stream.index)

    def test_it_validates_context(self):
        stream = Stream()
        stream._contexts.insert(0, Position(42, 0, 0))
        stream.validate_context()
        self.assertEqual(0, stream.index)
