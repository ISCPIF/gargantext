import node.models
from .NgramsExtractors import *

from collections import defaultdict

from nltk.stem.porter import PorterStemmer
st = PorterStemmer()

def stem_all(ngram):
    return " ".join(map(lambda x: st.stem(x), ngram.split(" ")))



class NgramsCache(defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time.
    This class is language-specific."""    
    def __init__(self, language):
        """The cache only works with one language,
        which is the required parameter of the constructor."""
        self.language = language
            
    def __missing__(self, terms):
        """If the terms are not yet present in the dictionary,
        retrieve it from the database or insert it."""
        
        terms = terms.strip().lower()
        
        try:
            ngram = node.models.Ngram.objects.get(terms=terms, language=self.language)
        except Exception as error:
            ngram = node.models.Ngram(terms=terms, n=len(terms.split()), language=self.language)
            ngram.save()
        
        stem_terms = stem_all(ngram.terms)

        try:
            stem = node.models.Ngram.objects.get(terms=stem_terms, language=ngram.language, n=ngram.n)
        except:
            stem = node.models.Ngram(terms=stem_terms, language=ngram.language, n=ngram.n)
            stem.save()

        type_stem = node.models.NodeType.objects.get(name='Stem')
        node_stem = node.models.Node.objects.get(name='Stem', type=type_stem)
        
        try:
            node.models.NodeNgramNgram.objects.get(node=node_stem, ngramx=stem, ngramy=ngram)
        except:
            node.models.NodeNgramNgram(node=node_stem, ngramx=stem, ngramy=ngram, score=1).save()

        self[terms] = ngram
        return self[terms]
        
class NgramsCaches(defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time."""
    def __missing__(self, language):
        """If the cache for this language is not reachable,
        add id to the dictionary."""
        self[language] = NgramsCache(language)
        return self[language]
   
class NgramsExtractorsCache(defaultdict):
    """This allows the fast retrieval of ngram ids
    from a cache instead of calling the database every time."""    
    def __missing__(self, key):
        """If the ngrams extractor is not instancianted yet
        for the given language, do it!"""
        # format the language
        if isinstance(key, str):
            language = key.strip().lower()
        elif key:
            language = key.iso2
        else:
            language = None
        # find the proper extractor
        if language in ["en", "eng", "english"]:
            Extractor = EnglishNgramsExtractor
        elif language in ["fr", "fra", "fre", "french"]:
            Extractor = FrenchNgramsExtractor
        else:
            Extractor = NgramsExtractor
        # try to see if already instanciated with another key
        found = False
        for extractor in self.values():
            if type(extractor) == Extractor:
                self[key] = extractor
                found = True
                break
        # well if not, let's instanciate it...
        if not found:
            self[key] = Extractor()
        # return the proper extractor
        return self[key]

class LanguagesCache(defaultdict):
    
    def __missing__(self, key):
        if len(self) == 0:
            for language in node.models.Language.objects.all():
                self[str(language.iso2.lower())] = language
                self[str(language.iso3.lower())] = language
                self[str(language.fullname.lower())] = language
        if key not in self.keys():
            betterKey = key.strip().lower()
            self[key] = self[betterKey] if betterKey in self.keys() else None
        return self[key]



class Caches:
    """This is THE cache of the caches.
    See NgramsCaches and NgramsExtractorsCache for better understanding."""
    def __init__(self):
        self.ngrams = NgramsCaches()
        self.extractors = NgramsExtractorsCache()
        self.languages = LanguagesCache()
