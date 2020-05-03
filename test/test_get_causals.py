import unittest
import io

import extract_xml_data

class TestExtractXmls(unittest.TestCase):

    def test_extract_data(self):
        inp = io.StringIO('<root><article-id pub-id-type="pmc">123</article-id><article-title>The Title</article-title><abstract>The abstract.</abstract></root>')
        answer = ('123', 'The Title', 'The abstract.')
        result = extract_xml_data.extract_data(inp)
        self.assertEqual(result, answer)

    def test_extract_data_with_tags(self):
        inp = io.StringIO('<root><article-id pub-id-type="pmc">123</article-id><article-title>The Title</article-title><abstract>The abstract.<p>Method</p>The method goes here.</abstract></root>')
        answer = ('123', 'The Title', 'The abstract. Method The method goes here.')
        result = extract_xml_data.extract_data(inp)
        self.assertEqual(result, answer)


if __name__ == '__main__':
    unittest.main()

