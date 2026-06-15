import unittest

from biomed_ref_pipeline.pubmed import parse_pubmed_xml


SAMPLE_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Example biomedical title.</ArticleTitle>
        <AuthorList><Author><LastName>Smith</LastName><Initials>AB</Initials></Author></AuthorList>
        <Abstract><AbstractText>Example abstract.</AbstractText></Abstract>
        <Journal>
          <Title>Example Journal</Title>
          <ISOAbbreviation>Ex J</ISOAbbreviation>
          <JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue>
        </Journal>
        <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
      </Article>
      <MeshHeadingList><MeshHeading><DescriptorName>Heart Failure</DescriptorName></MeshHeading></MeshHeadingList>
    </MedlineCitation>
    <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/example</ArticleId></ArticleIdList></PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class PubmedParseTests(unittest.TestCase):
    def test_parse_pubmed_xml(self):
        rows = parse_pubmed_xml(SAMPLE_XML)
        self.assertEqual(rows[0]["pmid"], "12345678")
        self.assertEqual(rows[0]["journal"], "Example Journal")
        self.assertEqual(rows[0]["authors"], "Smith AB")
        self.assertEqual(rows[0]["year"], "2025")
        self.assertEqual(rows[0]["doi"], "10.1000/example")
        self.assertIn("Heart Failure", rows[0]["mesh_terms"])


if __name__ == "__main__":
    unittest.main()
