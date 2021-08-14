from unittest import main, TestCase

from nachomemes.reflow import _tokenize, reflow_text

    






class TestReflow(TestCase):

    def test_tokenize(self):
        self.assertEqual(_tokenize('"asdf"', True), ['asdf'])
        self.assertEqual(_tokenize('asdf'), ['asdf'])
        self.assertEqual(_tokenize('as df'), ['as', ' ', 'df'])
        self.assertEqual(_tokenize('as/df'), ['as/df'])
        self.assertEqual(_tokenize('as / df'), ['as', ' / ', 'df'])
        self.assertEqual(_tokenize('\n'), ['\n'])
        self.assertEqual(_tokenize('\n\n'), ['\n\n'])
        self.assertEqual(_tokenize('\n\n\n'), ['\n\n', '\n'])
        self.assertEqual(_tokenize('\n\n\nfoo'), ['\n\n', '\n', 'foo'])
        self.assertEqual(_tokenize('fo\'o\nb\'ar'), ['fo\'o', '\n', 'b\'ar'])


    def test_flow(self):
        self.assertEqual(reflow_text('foo', 1), ['foo'])
        self.assertEqual(reflow_text('foo\nbar', 1), ['foo\nbar'])
        self.assertEqual(reflow_text('fo\'o\nbar', 2), ['fo\'o', 'bar'])
        self.assertEqual(reflow_text('fo\'o\nb\'ar', 2), ['fo\'o', 'b\'ar'])


if __name__ == "__main__":
    main()
