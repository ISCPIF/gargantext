from django.shortcuts import redirect
from django.shortcuts import render
from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

from node import models
# from node.models import Node_Ngram
from django.db import connection
#from node.models import Language, ResourceType, Resource, \
#        Node, NodeType, Node_Resource, Project, Corpus, \
#        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram

from node.admin import CorpusForm, ProjectForm, ResourceForm, CustomForm

from django.contrib.auth.models import User

import datetime
from itertools import *
from dateutil.parser import parse

from django.db import connection
from django import forms


from collections import defaultdict

from parsing.FileParsers import *
import os
import json
import math

# SOME FUNCTIONS

from gargantext_web import settings

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrappers.scrap_pubmed.admin import Logger

from gargantext_web.db import *

from sqlalchemy import or_, func

from gargantext_web import about

from rest_v1_0.api import JsonHttpResponse


from ngram.lists import listIds, listNgramIds, ngramList , doList


def get_ngrams(request , project_id , corpus_id ):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/terms.html')

    user = cache.User[request.user.username].id
    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]
    myamlist_type_id = cache.NodeType['MiamList'].id
    miamlist = session.query(Node).filter(Node.user_id == request.user.id , Node.parent_id==corpus_id , Node.type_id == myamlist_type_id ).first()

    try:
        processing = corpus.hyperdata['Processing']
    except Exception as error:
        print(error)
        processing = 0

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            'list_id': miamlist.id,
            }))

    return HttpResponse(html)

def get_journals(request , project_id , corpus_id ):

    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/journals.html')

    user = cache.User[request.user.username].id
    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]

    try:
        processing = corpus.hyperdata['Processing']
    except Exception as error:
        print(error)
        processing = 0

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            }))

    return HttpResponse(html)

def get_journals_json(request , project_id, corpus_id ):
    results = ["hola" , "mundo"]

    JournalsDict = {}

    user_id = request.user.id
    document_type_id = cache.NodeType['Document'].id
    documents  = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == document_type_id ).all()
    for doc in documents:
        if "journal" in doc.hyperdata:
            journal = doc.hyperdata["journal"]
            if journal not in JournalsDict:
                JournalsDict [journal] = 0
            JournalsDict[journal] += 1
    return JsonHttpResponse(JournalsDict)

from gargantext_web.db import session, cache, Node, NodeNgram
from sqlalchemy import or_, func
from sqlalchemy.orm import aliased


def get_corpuses( request , node_ids ):
    ngrams = [int(i) for i in node_ids.split("+") ]
    results = session.query(Node.id,Node.hyperdata).filter(Node.id.in_(ngrams) ).all()
    for r in results:
        print(r)
    return JsonHttpResponse( [ "tudo" , "bem" ] )


def get_cores( request ):
	import multiprocessing
	cpus = multiprocessing.cpu_count()
	return JsonHttpResponse( {"data":cpus} )


def get_corpus_state( request , corpus_id ):
    if not request.user.is_authenticated():
        return JsonHttpResponse( {"request" : "forbidden"} )
    processing = ["Waiting"]
    the_query = """ SELECT hyperdata FROM node_node WHERE id=%d """ % ( int(corpus_id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        processing = cursor.fetchone()[0]
    finally:
        connection.close()
    # processing = corpus.hyperdata['Processing']
    return JsonHttpResponse(  processing )