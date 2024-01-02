# CHIIR 2024 Citation Contexts Analysis

This repository contains the code to extract citation contexts from the CHIIR papers of 2016-2023 and can be used to replicate the analyses in the CHIIR 2024 paper "The Impact of CHIIR: A Study of Eight Years of CHIIR Publications"

## Install

From the command line, run:
```console
git clone git@github.com:biirrr/chiir-2024-citations.git
pipenv install
pipenv shell
```

## Usage

The `main.py` script assumes you have the extracted citation contexts. 
If you want to create them from scratch, set the variable `parse_pdfs` and `extract_contexts`
to in `main.py` to True. This requires you to install GROBID and the python client, as GROBID is
used for processing the PDFs (see below).

```console
python3 scripts/main.py
```

## PDF processing

If you want to redo the PDF parsing and citation context extraction, you need to both the GROBID server
and python client [grobid-python-client](https://github.com/kermitt2/grobid_client_python).

To install and run the GROBID server, see: https://grobid.readthedocs.io/en/latest/Introduction/

To install the Python client:

```console
git clone https://github.com/kermitt2/grobid_client_python
cd grobid_client_python
python3 setup.py install
```