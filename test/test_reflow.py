from unittest import main, TestCase

from nachomemes.reflow import _tokenize, reflow_text

    






class TestReflow(TestCase):

    def test_tokenize(self):
        self.assertEqual(_tokenize('"asdf"'), ['asdf'])
        self.assertEqual(_tokenize('asdf'), ['asdf'])
        self.assertEqual(_tokenize('as df'), ['as', ' ', 'df'])
        self.assertEqual(_tokenize('as/df'), ['as/df'])
        self.assertEqual(_tokenize('as / df'), ['as', ' / ', 'df'])
        self.assertEqual(_tokenize('\n'), ['\n'])
        self.assertEqual(_tokenize('\n\n'), ['\n\n'])
        self.assertEqual(_tokenize('\n\n\n'), ['\n\n', '\n'])
        self.assertEqual(_tokenize('\n\n\nfoo'), ['\n\n', '\n', 'foo'])


    def test_flow(self):
        self.assertEqual(reflow_text('foo', 1), ['foo'])
        self.assertEqual(reflow_text('foo\nbar', 1), ['foo\nbar'])


if __name__ == "__main__":
    main()
