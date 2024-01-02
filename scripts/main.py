import glob
import os
from typing import List

import pandas as pd
from grobid_client.grobid_client import GrobidClient

import parse_tei
from parse import make_citation_context_csv
from validate import validate_assumptions
from parse_metadata import add_scholar_id, get_version_with_max_refs
from parse_metadata import get_title_sim


def read_citation_contexts(citation_context_file: str) -> pd.DataFrame:
    """Read the citation contexts in a Pandas Dataframe and do minimal preprocessing."""
    citation_contexts = pd.read_csv(citation_context_file, sep='\t')
    citation_contexts = citation_contexts.drop('citing_id', axis=1)
    citation_contexts = citation_contexts.rename(columns={'cited_id': 'cited_bibl_id'})
    return citation_contexts


def do_validation(tei_files: List[str]) -> None:
    """Check our assumptions of paper metadata and citation contexts against all TEI files."""
    for tei_file in tei_files:
        tei_header, tei_text = parse_tei.parse_tei_file(tei_file)
        validate_assumptions(tei_text)
    return None


def parse_sample_pdfs(pdf_dir: str, tei_dir: str) -> None:
    """Process all PDFs in a dir using GROBID and create TEI versions."""
    client = GrobidClient(config_path="./config.json")
    client.process("processFulltextDocument",
                   pdf_dir,
                   output=tei_dir,
                   consolidate_citations=1,
                   include_raw_citations=1,
                   segment_sentences=1,
                   n=1)


def extract_citation_contexts(pdf_dir: str, tei_dir: str, citation_contexts_file: str):
    """"Take a directory of PDFs, create TEI versions and extract citation contexts."""
    # create TEI versions of all PDFs
    parse_sample_pdfs(pdf_dir, tei_dir)

    # read all TEI file names
    tei_files = glob.glob(os.path.join(tei_dir, '*.xml'))

    # validate our assumptions of the structure of the TEI files
    do_validation(tei_files)

    # create a CSV file with citation contexts
    make_citation_context_csv(tei_files, citation_contexts_file)


def link_citation_contexts_and_metadata(citation_contexts_file: str,
                                        linked_citation_contexts_file: str):
    """Link citation context information to CHIIR paper metadata"""
    scholar_file = '../citation_data/chiir2024.all-scholar-IDs.tsv'
    metadata_file = '../citation_data/all-data.tsv'
    citation_file = '../citation_data/chiir2024.all-citing-docs.tsv'

    # the scholar_file links the DOIs of CHIIR papers to their Google Scholar IDs
    scholar_ids = pd.read_csv(scholar_file, sep='\t')
    scholar_ids = scholar_ids.rename(columns={'result_id': 'cited_id', 'title': 'scholar_title'})

    # The metadata file contains DOIs, author names, paper title and annotations
    # extracted from our Zotero library
    metadata = pd.read_csv(metadata_file, sep='\t')
    column_map = {
        'DOI': 'meta_cited_doi',
        'title': 'meta_cited_title',
        'authors': 'meta_cited_authors'
    }
    metadata = metadata.rename(columns=column_map)

    # merge paper metadata and Google Scholar data
    metadata = pd.merge(metadata, scholar_ids, left_on='meta_cited_doi', right_on='doi')

    # the citation_file contains links between cited and citing papers
    citations = pd.read_csv(citation_file, sep='\t')

    # merge paper metadata with citation metadata
    citations = pd.merge(citations, metadata[['cited_id', 'meta_cited_authors', 'meta_cited_title']], on='cited_id')

    # read the citation contexts
    citation_contexts = read_citation_contexts(citation_contexts_file)
    add_scholar_id(citation_contexts)
    citation_contexts = get_version_with_max_refs(citation_contexts)

    # merge CHIIR paper and citation metadata with citation contexts
    cited_contexts = pd.merge(citations, citation_contexts, on='citing_id')

    # compute the similarity of CHIIR paper titles and titles of cited publications
    cited_contexts['title_sim'] = cited_contexts.apply(get_title_sim, axis=1)

    select_cols = [
        'cited_id', 'cited_author', 'cited_title',
        'citing_id', 'citing_author', 'citing_title',
        'citation_ref', 'citation_sent', 'citation_context',
        'title_dist', 'title_sim',
        # 'cited_title', 'meta_cited_title', 'cited_author', 'meta_cited_authors'
    ]

    # link cited paper metadata of citation context to paper metadata from Zotero+Google Scholar
    # using a title similarity score threshold of 0.6
    cited_contexts[cited_contexts.title_sim > 0.6][select_cols].to_csv(linked_citation_contexts_file, sep='\t')


def main():
    base_dir = "/Volumes/T7_Shield/Data/CHIIR-papers/citing_papers"
    pdf_dir = f"{base_dir}/PDF"
    tei_dir = f"{base_dir}/TEI"

    citation_contexts_file = '../citation_contexts/chiir_papers-citation_contexts.tsv'
    extract_citation_contexts(pdf_dir, tei_dir, citation_contexts_file)
    linked_citation_contexts_file = '../citation_contexts/linked-chiir_papers-citation_contexts.tsv'
    link_citation_contexts_and_metadata(citation_contexts_file, linked_citation_contexts_file)


if __name__ == "__main__":
    # keep global namespace clean and run everything from within main function
    main()
