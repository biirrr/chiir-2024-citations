import os

import pandas as pd
from Levenshtein import distance


def get_title_dist(row):
    if isinstance(row['meta_cited_title'], str) and isinstance(row['cited_title'], str):
        return distance(row['meta_cited_title'].lower(), row['cited_title'].lower())
    elif isinstance(row['meta_cited_title'], str):
        return len(row['meta_cited_title'])
    elif isinstance(row['cited_title'], str):
        return len(row['cited_title'])
    else:
        return 200


def get_title_sim(row):
    len_title = len(row['meta_cited_title'])
    return 1 - (row['title_dist'] / len_title)


def parse_doc_id(doc_id):
    fdir, fname = os.path.split(doc_id)
    scholar_id, version, *rest = fname.split('.')
    return scholar_id, version


def add_scholar_id(citation_contexts):
    citation_contexts['parsed_doc_id'] = citation_contexts.doc_id.apply(parse_doc_id)
    citation_contexts['citing_id'] = citation_contexts.parsed_doc_id.apply(lambda x: x[0])
    citation_contexts['citing_version'] = citation_contexts.parsed_doc_id.apply(lambda x: x[1])


def get_version_with_max_refs(citation_contexts):
    citation_contexts['num_refs'] = citation_contexts.groupby('parsed_doc_id').parsed_doc_id.transform('count')
    max_versions = list(
        citation_contexts.loc[citation_contexts.groupby(['citing_id'])["num_refs"].idxmax()].parsed_doc_id)
    return citation_contexts[citation_contexts.parsed_doc_id.isin(max_versions)]
