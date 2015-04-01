import re
import locale
from lxml import etree
from datetime import datetime, date
from django.utils import timezone
import dateutil.parser

from .FileParser import FileParser
from ..NgramsExtractors import *



class EuropressFileParser(FileParser):
  
    def _parse(self, file):

        localeEncoding = "fr_FR"
        codif      = "UTF-8"
        count = 0

        if isinstance(file, str):
            file = open(file, 'rb')
        # print(file)
        contents = file.read()
        #print(len(contents))
        #return []
        encoding = self.detect_encoding(contents)
        #print(encoding)
        if encoding != "utf-8":
            try:
                contents = contents.decode("latin1", errors='replace').encode(codif)
            except Exception as error:
                print(error)
#                try:
#                    contents = contents.decode(encoding, errors='replace').encode(codif)
#                except Exception as error:
#                    print(error)

        try:
            html_parser = etree.HTMLParser(encoding=codif)
            html = etree.fromstring(contents, html_parser)
            
            try:
                
                format_europresse = 50
                html_articles = html.xpath('/html/body/table/tbody')

                if len(html_articles) < 1:
                    html_articles = html.xpath('/html/body/table')
                    
                    if len(html_articles) < 1:
                        format_europresse = 1
                        html_articles = html.xpath('//div[@id="docContain"]')
            except Exception as error:
                print(error)
            
            if format_europresse == 50:
                name_xpath = "./tr/td/span[@class = 'DocPublicationName']"
                header_xpath = "//span[@class = 'DocHeader']"
                title_xpath = "string(./tr/td/span[@class = 'TitreArticleVisu'])"
                text_xpath  = "./tr/td/descendant-or-self::*[not(self::span[@class='DocHeader'])]/text()"
            elif format_europresse == 1:
                name_xpath = "//span[@class = 'DocPublicationName']"
                header_xpath = "//span[@class = 'DocHeader']"
                title_xpath = "string(//div[@class = 'titreArticleVisu'])"
                text_xpath  = "./descendant::*[\
                        not(\
                           self::div[@class='Doc-SourceText'] \
                        or self::span[@class='DocHeader'] \
                        or self::span[@class='DocPublicationName'] \
                        or self::span[@id='docNameVisu'] \
                        or self::span[@class='DocHeader'] \
                        or self::div[@class='titreArticleVisu'] \
                        or self::span[@id='docNameContType'] \
                        or descendant-or-self::span[@id='ucPubliC_lblCertificatIssuedTo'] \
                        or descendant-or-self::span[@id='ucPubliC_lblEndDate'] \
                        or self::td[@class='txtCertificat'] \
                        )]/text()"
                doi_xpath  = "//span[@id='ucPubliC_lblNodoc']/text()"
                

        except Exception as error:
            print(error)

        # parse all the articles, one by one
        try:
            for html_article in html_articles:
                
                metadata = {}
                
                if len(html_article):
                    for name in html_article.xpath(name_xpath):
                        if name.text is not None:
                            format_journal = re.compile('(.*), (.*)', re.UNICODE)
                            test_journal = format_journal.match(name.text)
                            if test_journal is not None:
                                metadata['journal'] = test_journal.group(1)
                                metadata['volume'] = test_journal.group(2)
                            else:
                                metadata['journal'] = name.text.encode(codif)

                    for header in html_article.xpath(header_xpath):
                        try:
                            text = header.text
                            #print("header", text)
                        except Exception as error:
                            print(error)

                        
                        if isinstance(text, bytes):
                            text = text.decode(encoding)
                        format_date_fr = re.compile('\d*\s*\w+\s+\d{4}', re.UNICODE)
                        if text is not None:
                            test_date_fr = format_date_fr.match(text)
                            format_date_en = re.compile('\w+\s+\d+,\s+\d{4}', re.UNICODE)
                            test_date_en = format_date_en.match(text)
                            format_sect = re.compile('(\D+),', re.UNICODE)
                            test_sect = format_sect.match(text)
                            format_page = re.compile(', p. (\w+)', re.UNICODE)
                            test_page = format_page.match(text)
                        else:
                            test_date_fr = None
                            test_date_en = None
                            test_sect = None
                            test_page = None
                        
                        
                        
                        if test_date_fr is not None:
                            self.localeEncoding = "fr_FR"
                            locale.setlocale(locale.LC_ALL, localeEncoding)
                            if encoding != "utf-8":
                                text = text.replace('י', 'é')
                                text = text.replace('ű', 'û')
                                text = text.replace(' aot ', ' août ')

                            try :
                                metadata['publication_date'] = datetime.strptime(text, '%d %B %Y')
                            except :
                                try:
                                    metadata['publication_date'] = datetime.strptime(text, '%B %Y')
                                except :
                                    try:
                                        locale.setlocale(locale.LC_ALL, "fr_FR")
                                        metadata['publication_date'] = datetime.strptime(text, '%d %B %Y')
                                        # metadata['publication_date'] = dateutil.parser.parse(text)
                                    except Exception as error:
                                        print(error)
                                        print(text)
                                        pass
                        
                        
                        
                        if test_date_en is not None:
                            localeEncoding = "en_GB.UTF-8"
                            locale.setlocale(locale.LC_ALL, localeEncoding)
                            try :
                                metadata['publication_date'] = datetime.strptime(text, '%B %d, %Y')
                            except :
                                try :
                                    metadata['publication_date'] = datetime.strptime(text, '%B %Y')
                                except :
                                    pass

                        if test_sect is not None:
                            metadata['section'] = test_sect.group(1).encode(codif)
                        
                        if test_page is not None:
                            metadata['page'] = test_page.group(1).encode(codif)

                    metadata['title'] = html_article.xpath(title_xpath).encode(codif)
                    metadata['abstract']  = html_article.xpath(text_xpath)
                   
                    line = 0
                    br_tag = 10
                    for i in html_articles[count].iter():
                       # print line, br, i, i.tag, i.attrib, i.tail
                        if i.tag == "span":
                            if "class" in i.attrib:
                                if i.attrib['class'] == 'TitreArticleVisu':
                                    line = 1
                                    br_tag = 2
                        if line == 1 and i.tag == "br":
                            br_tag -= 1
                        if line == 1 and br_tag == 0:
                            try:
                                metadata['authors'] = str.title(etree.tostring(i, method="text", encoding=codif)).encode(codif)#.split(';')
                            except:
                                metadata['authors'] = 'not found'
                            line = 0
                            br_tag = 10
                    
                    
                    try:
                        if metadata['publication_date'] is not None or metadata['publication_date'] != '':
                            try:
                                back = metadata['publication_date']
                            except Exception as e: 
                                #print(e)
                                pass
                        else:
                            try:
                                metadata['publication_date'] = back
                            except Exception as e:
                                print(e)
                    except :
                        metadata['publication_date'] = timezone.now()

                    #if lang == 'fr':
                    #metadata['language_iso2'] = 'fr'
                    #elif lang == 'en':
                    #    metadata['language_iso2'] = 'en'
                    
                    
                    metadata['publication_year']  = metadata['publication_date'].strftime('%Y')
                    metadata['publication_month'] = metadata['publication_date'].strftime('%m')
                    metadata['publication_day']  = metadata['publication_date'].strftime('%d')
                    metadata.pop('publication_date')
                    
                    if len(metadata['abstract'])>0 and format_europresse == 50: 
                        metadata['doi'] = str(metadata['abstract'][-9])
                        metadata['abstract'].pop()
# Here add separator for paragraphs
                        metadata['abstract'] = str(' '.join(metadata['abstract']))
                        metadata['abstract'] = str(re.sub('Tous droits réservés.*$', '', metadata['abstract']))
                    elif format_europresse == 1:
                        metadata['doi'] = ' '.join(html_article.xpath(doi_xpath))
                        metadata['abstract'] = metadata['abstract'][:-9]
# Here add separator for paragraphs
                        metadata['abstract'] = str(' '.join(metadata['abstract']))

                    else: 
                        metadata['doi'] = "not found"
                    
                    metadata['length_words'] = len(metadata['abstract'].split(' '))
                    metadata['length_letters'] = len(metadata['abstract'])
                    
                    metadata['bdd']  = u'europresse'
                    metadata['url']  = u''
                    
                  #metadata_str = {}
                    for key, value in metadata.items():
                        metadata[key] = value.decode() if isinstance(value, bytes) else value
                    yield metadata
                    count += 1
            file.close()

        except Exception as error:
            print(error)
            pass
