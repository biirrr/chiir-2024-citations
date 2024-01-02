import glob
import os

import pandas as pd
from grobid_client.grobid_client import GrobidClient

from parse import make_citation_context_csv
from validate import do_validation
from parse_metadata import add_scholar_id, get_version_with_max_refs
from parse_metadata import get_title_dist, get_title_sim


def read_citation_contexts(citation_context_file: str) -> pd.DataFrame:
    """Read the citation contexts in a Pandas Dataframe and do minimal preprocessing."""
    citation_contexts = pd.read_csv(citation_context_file, sep='\t')
    citation_contexts = citation_contexts.drop('citing_id', axis=1)
    citation_contexts = citation_contexts.rename(columns={'cited_id': 'cited_bibl_id'})
    return citation_contexts


def parse_pdfs_to_tei(pdf_dir: str, tei_dir: str) -> None:
    """Process all PDFs in a dir using GROBID and create TEI versions."""
    client = GrobidClient(config_path="./config.json")
    client.process("processFulltextDocument",
                   pdf_dir,
                   output=tei_dir,
                   consolidate_citations=1,
                   include_raw_citations=1,
                   segment_sentences=1,
                   n=1)


def extract_citation_contexts(tei_dir: str, citation_contexts_file: str):
    """"Take a directory of TEI files of pubilcations and extract citation contexts."""
    # read all TEI file names
    tei_files = glob.glob(os.path.join(tei_dir, '*.xml'))

    # validate our assumptions of the structure of the TEI files
    do_validation(tei_files)

    # create a CSV file with citation contexts
    make_citation_context_csv(tei_files, citation_contexts_file)


def link_citation_contexts_and_metadata(citation_contexts_file: str,
                                        linked_citation_contexts_file: str):
    """Link citation context information to CHIIR paper metadata"""
    scholar_file = 'citation_data/chiir2024.all-scholar-IDs.tsv'
    metadata_file = 'citation_data/all-data.tsv'
    citation_file = 'citation_data/chiir2024.all-citing-docs.tsv'

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
    print('\nmering CHIIR paper metadata and citation metadata')
    citations = pd.merge(citations, metadata[['cited_id', 'meta_cited_authors', 'meta_cited_title']], on='cited_id')
    print('\tnumber of citations:', len(citations))

    # read the citation contexts
    citation_contexts = read_citation_contexts(citation_contexts_file)
    add_scholar_id(citation_contexts)
    citation_contexts = get_version_with_max_refs(citation_contexts)

    # merge CHIIR paper and citation metadata with citation contexts
    print('mering CHIIR paper and citation metadata with citation contexts')
    cited_contexts = pd.merge(citations, citation_contexts, on='citing_id')
    print('\tTotal number of citation contexts:', len(cited_contexts))

    # compute the similarity of CHIIR paper titles and titles of cited publications
    print('computing the similarity of CHIIR paper titles and titles of cited publications')
    cited_contexts['title_dist'] = cited_contexts.apply(get_title_dist, axis=1)
    cited_contexts['title_sim'] = cited_contexts.apply(get_title_sim, axis=1)

    select_cols = [
        'cited_id', 'cited_author', 'cited_title',
        'citing_id', 'citing_author', 'citing_title',
        'citation_ref', 'citation_sent', 'citation_context',
        'title_sim',
        # 'cited_title', 'meta_cited_title', 'cited_author', 'meta_cited_authors'
    ]

    # link cited paper metadata of citation context to paper metadata from Zotero+Google Scholar
    # using a title similarity score threshold of 0.6
    print('selecting citation contexts with a CHIIR title similarity score above 0.6')
    cited_contexts[cited_contexts.title_sim > 0.6][select_cols].to_csv(linked_citation_contexts_file, sep='\t')
    print('\tnumber of citation contexts above threshold: '
          f'{len(cited_contexts[cited_contexts.title_sim > 0.6])}\n')


def main():
    base_dir = "/Volumes/T7_Shield/Data/CHIIR-papers/citing_papers"
    pdf_dir = f"{base_dir}/PDF"
    tei_dir = f"{base_dir}/TEI"

    citation_contexts_file = 'citation_contexts/chiir_papers-citation_contexts.tsv'

    # set to True if you want to redo these steps
    parse_pdfs = False
    extract_contexts = False

    # create TEI versions of all PDFs
    if parse_pdfs:
        parse_pdfs_to_tei(pdf_dir, tei_dir)

    # create citation contexts
    if extract_contexts:
        print('\nextracting citation contexts')
        extract_citation_contexts(tei_dir, citation_contexts_file)

    # link citation contexts to the CHIIR paper and citation metadata
    linked_citation_contexts_file = 'citation_contexts/linked-chiir_papers-citation_contexts.tsv'
    link_citation_contexts_and_metadata(citation_contexts_file, linked_citation_contexts_file)
    print(f'\nlinked citation contexts written to file "{linked_citation_contexts_file}"\n')
    print('Done!\n')


if __name__ == "__main__":
    # keep global namespace clean and run everything from within main function
    main()
