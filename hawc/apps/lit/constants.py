import re

from django.db import models

EXTERNAL_LINK = 0


class ReferenceDatabase(models.IntegerChoices):
    PUBMED = 1, "PubMed"
    HERO = 2, "HERO"
    RIS = 3, "RIS (EndNote/Reference Manager)"
    DOI = 4, "DOI"
    WOS = 5, "Web of Science"
    SCOPUS = 6, "Scopus"
    EMBASE = 7, "Embase"


class SearchType(models.TextChoices):
    SEARCH = "s", "Search"
    IMPORT = "i", "Import"


# generalized/adapted from https://www.crossref.org/blog/dois-and-matching-regular-expressions/
DOI_EXACT = re.compile(r"^10\.\d{4,9}/[^\s]+$")
DOI_EXTRACT = re.compile(r"10\.\d{4,9}/[^\s]+")
DOI_EXAMPLE = "10.1234/s123456"
