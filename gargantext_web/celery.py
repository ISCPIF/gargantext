# -*- coding: utf-8 -*-


#import os
#import djcelery
#
#from celery import Celery
#
#from django.conf import settings
#
## set the default Django settings module for the 'celery' program.
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gargantext_web.settings')
#
#app = Celery('gargantext_web')
#
#
#app.conf.update(
#    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
#)
#
#
#app.conf.update(
#    CELERY_RESULT_BACKEND='djcelery.backends.cache:CacheBackend',
#)
#
## Using a string here means the worker will not have to
## pickle the object when using Windows.
##app.config_from_object('django.conf:settings')
#app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
#
from celery import shared_task
from node import models

#@app.task(bind=True)
@shared_task
def debug_task(request):
    print('Request: {0!r}'.format(request))

from gargantext_web.db import session, Node

@shared_task
def apply_sum(x, y):
    print(x+y)
    print(session.query(Node.name).first())


from parsing.corpustools import add_resource, parse_resources, extract_ngrams, compute_tfidf


@shared_task
def apply_workflow(corpus_id):
    corpus = session.query(Node).filter(Node.id==corpus_id).first()

    parse_resources(corpus)
    
    try:
        print("-" *60)
        
        # With Django ORM 
        corpus_django = models.Node.objects.get(id=corpus_id)
        corpus_django.metadata['Processing'] = 0
        corpus_django.save()
        
        #TODO With SLA ORM (KO why?)
#        corpus.metadata['Processing'] = 0
#        session.add(corpus)
#        session.flush()

    except Exception as error:
        print(error)

       
    extract_ngrams(corpus, ['title'])
    compute_tfidf(corpus)


