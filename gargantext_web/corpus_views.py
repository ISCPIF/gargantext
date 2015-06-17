from django.shortcuts import redirect
from django.shortcuts import render
from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

from node import models
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

# SOME FUNCTIONS

from gargantext_web import settings

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrappers.scrap_pubmed.admin import Logger

from gargantext_web.db import *

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select


from gargantext_web import about

from gargantext_web.api import JsonHttpResponse


from ngram.lists import listIds, listNgramIds, ngramList , doList


def test_page(request , project_id , corpus_id):

    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('tests/test_select-boostrap.html')

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

def get_ngrams(request , project_id , corpus_id ):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/terms.html')

    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]

    lists = dict()
    for list_type in ['MiamList', 'StopList']:
        list_id = list()
        list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
        lists["%s" % list_id[0][0]] = list_type

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
            'list_id': list_id[0][0],
            'view'   : "terms",
            }))

    return HttpResponse(html)



def test_test(request , corpus_id , doc_id):
    """Get All for a doc id"""
    corpus_id = int(corpus_id)
    doc_id = int(doc_id)
    lists = dict()
    for list_type in ['StopList']:
        list_id = list()
        list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
        lists["%s" % list_id[0][0]] = list_type
    print(list_id[0][0])


    # # # ngrams of list_id of corpus_id:
    # commeca = "StopList"
    doc_ngram_list = listNgramIds(corpus_id=corpus_id, list_id=list_id[0][0], doc_id=list_id[0][0], user_id=request.user.id)

    to_del = {}
    for n in doc_ngram_list:
        to_del[ n[0] ] = True

    print( to_del.keys() )

    results = [ "hola" , "mundo" ]
    return JsonHttpResponse(results)


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
            'view'   : "journals",
            }))

    return HttpResponse(html)

def test_journals(request , project_id, corpus_id ):
    results = ["hola" , "mundo"]

    JournalsDict = {}

    document_type_id = cache.NodeType['Document'].id

    journal_count = (session.query(Node.hyperdata['journal'].label("journal"), func.count().label("count"))
                    .filter(Node.parent_id == corpus_id, Node.type_id==cache.NodeType['Document'].id)
                    .group_by("journal")
                    .order_by(desc("count"))
                    .all())
    jc = dict()
    for journal,count in journal_count:
        jc[journal] = count

    return JsonHttpResponse(jc)

def test_ngrams(request , project_id, corpus_id ):
    results = ["hola" , "mundo"]

    user_id = request.user.id
    whitelist_type_id = cache.NodeType['WhiteList'].id
    document_type_id = cache.NodeType['Document'].id

    corpus_id = int(corpus_id)
    lists = dict()
    for list_type in ['StopList']:
        list_id = list()
        list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
        lists["%s" % list_id[0][0]] = list_type
    doc_ngram_list = listNgramIds(corpus_id=corpus_id, list_id=list_id[0][0], doc_id=list_id[0][0], user_id=request.user.id)
    StopList = {}
    for n in doc_ngram_list:
        StopList[ n[0] ] = True

    # # 13099  clinical benefits
    # # 7492   recent data
    # # 14279  brain development
    # # 50681  possible cause
    # # 47111  psychological symptoms
    # # 3944   common form
    # ngram_of_interest = 14279

    # documents  = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == document_type_id ).all()
    # to_print = []

    # for doc in documents:
    #     NgramOccs = session.query(Node_Ngram).filter( Node_Ngram.node_id==doc.id).all()
    #     # print( len(NgramOccs) )
    #     for ngram in NgramOccs:
    #         if ngram.ngram_id == ngram_of_interest:
    #             to_print.append( [doc.id,doc.name] )
    #             break

    # if len(to_print)>0:
    #     for doc in to_print:
    #         doc_id = doc[0]
    #         doc_name = doc[1]
    #         print("doc_id:",doc_id)
    #         NgramOccs = session.query(Node_Ngram).filter( Node_Ngram.node_id==doc_id).all()
    #         for ngram in NgramOccs:
    #             if ngram.ngram_id == ngram_of_interest:
    #                 print("\t" , ngram.ngram_id , "\t" , ngram.weight )

    # print (" - - - - -- - - - ")
    # print("Calculation using the DB:")
    # white_list = session.query(Node).filter( Node.parent_id==corpus_id , Node.type_id==whitelist_type_id).first()
    # NgramOccs = session.query(Node_Ngram).filter( Node_Ngram.node_id==white_list.id).all()
    # for ngram in NgramOccs:
    #     if ngram.ngram_id == ngram_of_interest:
    #         print( ngram.weight, "\t" , ngram.ngram_id)
    # print( "= = = = = = = = == = =  ")

    # NgramTFIDF = session.query(NodeNodeNgram).filter( NodeNodeNgram.nodex_id==corpus_id ).all()

    # for ngram in NgramTFIDF:
    #     print( "docid:", ngram.nodey_id , ngram.ngram_id  , ngram.score)


    Ngrams_Scores = {}

    ## < Getting the Effective nro de OCCS ##
    documents  = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == document_type_id ).all()
    for doc in documents:
        NgramOccs = session.query(Node_Ngram).filter( Node_Ngram.node_id==doc.id).all()
        for ngram in NgramOccs:
            if ngram.ngram_id not in StopList:
                if ngram.ngram_id not in Ngrams_Scores:
                    Ngrams_Scores[ngram.ngram_id] = {}
                    Ngrams_Scores[ngram.ngram_id]["scores"] = {
                        "occ_sum": 0.0,
                        "occ_uniq": 0.0,
                        "tfidf_sum": 0.0
                    }
                Ngrams_Scores[ngram.ngram_id]["scores"]["occ_sum"]+=ngram.weight
                Ngrams_Scores[ngram.ngram_id]["scores"]["occ_uniq"]+=1
            # print("\t" , ngram.ngram_id , "\t" , ngram.weight )
    ## Getting the Effective nro de OCCS / >##

    # # CA MARCHE PAS POUR TOUT LES NGRAMS!!
    # ## < Getting the unique number of OCCS ##
    # summ1 = len(Ngrams_Scores.keys())
    # white_list = session.query(Node).filter( Node.parent_id==corpus_id , Node.type_id==whitelist_type_id).first()# get whitelist id from corpus
    # NgramOccs = session.query(Node_Ngram).filter( Node_Ngram.node_id==white_list.id).all()

    # summ2 = 0
    # for ngram in NgramOccs:
    #     Ngrams_Scores[ngram.ngram_id]["occ_uniq"] = ngram.weight
    #     summ2+=1
    #     # print("\t" , ngram.ngram_id , "\t" , ngram.weight )
    # print (" -  - -- - - - - - ")
    # print ("Sum numero 01:",summ1)
    # print ("Sum numero 02:",summ2)
    # ## Getting the unique number of OCCS /> ##


    Sum = 0
    NgramTFIDF = session.query(NodeNodeNgram).filter( NodeNodeNgram.nodex_id==corpus_id ).all()
    for ngram in NgramTFIDF:
        if ngram.ngram_id not in StopList:
            Ngrams_Scores[ngram.ngram_id]["scores"]["tfidf_sum"] += ngram.score
            Sum += Ngrams_Scores[ngram.ngram_id]["scores"]["occ_uniq"]
            # print( "docid:", ngram.nodey_id , ngram.ngram_id  , ngram.score)


    # import pprint
    # pprint.pprint( Ngrams_Scores )



    # # select * from node_nodenodengram where ngram_id=14279;
    # NodeNodeNgram
    #     nodex_id = real corpus id
    #     nodey_id = document id
    #     ngram_id = duh

    # id   | nodex_id | nodey_id | ngram_id |       score


    ngrams_ids = Ngrams_Scores.keys()

    import math

    if len(ngrams_ids) != 0:
        occs_threshold = min ( 10 , math.sqrt(Sum / len(ngrams_ids)) )
    else:
        occs_threshold = 10

    Metrics = {
        "ngrams":[],
        "scores": {}
    }


    query = session.query(Ngram).filter(Ngram.id.in_( ngrams_ids ))
    ngrams_data = query.all()
    for ngram in ngrams_data:
        if ngram.id not in StopList:
            occ_uniq = Ngrams_Scores[ngram.id]["scores"]["occ_uniq"]
            if occ_uniq > occs_threshold:
                Ngrams_Scores[ngram.id]["name"] = ngram.terms
                Ngrams_Scores[ngram.id]["id"] = ngram.id
                Ngrams_Scores[ngram.id]["scores"]["tfidf"] = Ngrams_Scores[ngram.id]["scores"]["tfidf_sum"] / occ_uniq
                del Ngrams_Scores[ngram.id]["scores"]["tfidf_sum"]
                Metrics["ngrams"].append( Ngrams_Scores[ngram.id] )



    Metrics["scores"] = {
    	"initial":"occ_uniq",
    	"nb_docs":len(documents),
    	"orig_nb_ngrams":len(ngrams_ids),
    	"nb_ngrams":len(Metrics["ngrams"]),
    	"occs_threshold":occs_threshold
    }

    return JsonHttpResponse(Metrics)


