from django.http import HttpResponseNotFound, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.exceptions import ValidationError

from django.db.models import Avg, Max, Min, Count, Sum
# from node.models import Language, ResourceType, Resource
# from node.models import Node, NodeType, Node_Resource, Project, Corpus

from sqlalchemy import text, distinct
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

from .db import *


def DebugHttpResponse(data):
    return HttpResponse('<html><body style="background:#000;color:#FFF"><pre>%s</pre></body></html>' % (str(data), ))

import json
def JsonHttpResponse(data, status=200):
    return HttpResponse(
        content      = json.dumps(data, indent=4),
        content_type = 'application/json; charset=utf-8',
        status       = status
    )
Http400 = SuspiciousOperation
Http403 = PermissionDenied

import csv
def CsvHttpResponse(data, headers=None, status=200):
    response = HttpResponse(
        content_type = "text/csv",
        status       = status
    )
    writer = csv.writer(response, delimiter=',')
    if headers:
        writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return response

_ngrams_order_columns = {
    "frequency" : "-count",
    "alphabetical" : "terms"
}


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException as _APIException

class APIException(_APIException):
    def __init__(self, message, code=500):
        self.status_code = code
        self.detail = message



_operators = {
    "=":            lambda field, value: (field == value),
    "!=":           lambda field, value: (field != value),
    "<":            lambda field, value: (field < value),
    ">":            lambda field, value: (field > value),
    "<=":           lambda field, value: (field <= value),
    ">=":           lambda field, value: (field >= value),
    "in":           lambda field, value: (field.in_(value)),
    "contains":     lambda field, value: (field.contains(value)),
    "startswith":   lambda field, value: (field.startswith(value)),
}

from rest_framework.decorators import api_view
@api_view(('GET',))
def Root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'snippets': reverse('snippet-list', request=request, format=format)
    })


class NodesChildrenNgrams(APIView):

    def get(self, request, node_id):
        # query ngrams
        ParentNode = aliased(Node)
        ngrams_query = (Ngram
            .query(Ngram.terms, func.count().label('count'))
            # .query(Ngram.id, Ngram.terms, func.count().label('count'))
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
            .filter(Node.parent_id == node_id)
            .group_by(Ngram.terms)
            # .group_by(Ngram)
            .order_by(func.count().desc(), Ngram.terms)
            # .order_by(func.count().desc(), Ngram.id)
        )
        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        total = ngrams_query.count()
        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    # 'id': ngram.id,
                    'terms': ngram.terms,
                    'count': ngram.count,
                }
                for ngram in ngrams_query[offset : offset+limit]
            ],
        })


class NodesChildrenDuplicates(APIView):

    def _fetch_duplicates(self, request, node_id, extra_columns=[], min_count=1):
        # input validation
        if 'keys' not in request.GET:
            raise APIException('Missing GET parameter: "keys"', 400)
        keys = request.GET['keys'].split(',')
        # metadata retrieval
        metadata_query = (Metadata
            .query(Metadata)
            .filter(Metadata.name.in_(keys))
        )
        # build query elements
        columns = []
        aliases = []
        for metadata in metadata_query:
            # aliases
            _Metadata = aliased(Metadata)
            _Node_Metadata = aliased(Node_Metadata)
            aliases.append(_Node_Metadata)
            # what shall we retrieve?
            columns.append(
                getattr(_Node_Metadata, 'value_' + metadata.type)
            )
        # build the query
        groups = list(columns)
        duplicates_query = (session
            .query(*(extra_columns + [func.count()] + columns))
            .select_from(Node)
        )
        for _Node_Metadata, metadata in zip(aliases, metadata_query):
            duplicates_query = duplicates_query.outerjoin(_Node_Metadata, _Node_Metadata.node_id == Node.id)
            duplicates_query = duplicates_query.filter(_Node_Metadata.metadata_id == metadata.id)
        duplicates_query = duplicates_query.filter(Node.parent_id == node_id)
        duplicates_query = duplicates_query.group_by(*columns)
        duplicates_query = duplicates_query.order_by(func.count().desc())
        duplicates_query = duplicates_query.having(func.count() > min_count)
        # and now, return it
        return duplicates_query

    def get(self, request, node_id):
        # data to be returned
        duplicates = self._fetch_duplicates(request, node_id)
        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))
        total = duplicates.count()
        # response building
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    'count': duplicate[0],
                    'values': duplicate[1:],
                }
                for duplicate in duplicates[offset : offset+limit]
            ]
        })

    def delete(self, request, node_id):
        # get the minimum ID for each of the nodes sharing the same metadata
        kept_node_ids_query = self._fetch_duplicates(request, node_id, [func.min(Node.id).label('id')], 0)
        kept_node_ids = [kept_node.id for kept_node in kept_node_ids_query]
        duplicate_nodes =  models.Node.objects.filter( parent_id=node_id ).exclude(id__in=kept_node_ids)
        # # delete the stuff
        # delete_query = (session
        #     .query(Node)
        #     .filter(Node.parent_id == node_id)
        #     .filter(~Node.id.in_(kept_node_ids))
        # )
        count = len(duplicate_nodes)
        for node in duplicate_nodes:
            print("deleting node ",node.id)
            node.delete()
        # print(delete_query)
        # # delete_query.delete(synchronize_session=True)
        # session.flush()
        return JsonHttpResponse({
            'deleted': count
        })



class NodesChildrenMetatadata(APIView):

    def get(self, request, node_id):
        
        # query metadata keys
        ParentNode = aliased(Node)
        metadata_query = (Metadata
            .query(Metadata)
            .join(Node_Metadata, Node_Metadata.metadata_id == Metadata.id)
            .join(Node, Node.id == Node_Metadata.node_id)
            .filter(Node.parent_id == node_id)
            .group_by(Metadata)
        )

        # build a collection with the metadata keys
        collection = []
        for metadata in metadata_query:
            valuesCount = 0
            values = None

            # count values and determine their span
            values_count = None
            values_from = None
            values_to = None
            if metadata.type != 'text':
                value_column = getattr(Node_Metadata, 'value_' + metadata.type)
                node_metadata_query = (Node_Metadata
                    .query(value_column)
                    .join(Node, Node.id == Node_Metadata.node_id)
                    .filter(Node.parent_id == node_id)
                    .filter(Node_Metadata.metadata_id == metadata.id)
                    .group_by(value_column)
                    .order_by(value_column)
                )
                values_count = node_metadata_query.count()
                # values_count, values_from, values_to = node_metadata_query.first()

            # if there is less than 32 values, retrieve them
            values = None
            if isinstance(values_count, int) and values_count <= 48:
                if metadata.type == 'datetime':
                    values = [row[0].isoformat() for row in node_metadata_query.all()]
                else:
                    values = [row[0] for row in node_metadata_query.all()]

            # adding this metadata to the collection
            collection.append({
                'key': metadata.name,
                'type': metadata.type,
                'values': values,
                'valuesFrom': values_from,
                'valuesTo': values_to,
                'valuesCount': values_count,
            })

        return JsonHttpResponse({
            'data': collection,
        })



class NodesChildrenQueries(APIView):

    def _parse_filter(self, filter):
            
        # validate filter keys
        filter_keys = {'field', 'operator', 'value'}
        if set(filter) != filter_keys:
            raise APIException('Every filter should have exactly %d keys: "%s"'% (len(filter_keys), '", "'.join(filter_keys)), 400)
        field, operator, value = filter['field'], filter['operator'], filter['value']

        # validate operator
        if operator not in _operators:
            raise APIException('Invalid operator: "%s"'% (operator, ), 400)

        # validate value, depending on the operator
        if operator == 'in':
            if not isinstance(value, list):
                raise APIException('Parameter "value" should be an array when using operator "%s"'% (operator, ), 400)
            for v in value:
                if not isinstance(v, (int, float, str)):
                    raise APIException('Parameter "value" should be an array of numbers or strings when using operator "%s"'% (operator, ), 400)
        else:
            if not isinstance(value, (int, float, str)):
                raise APIException('Parameter "value" should be a number or string when using operator "%s"'% (operator, ), 400)

        # parse field
        field_objects = {
            'metadata': None,
            'ngrams': ['terms', 'n'],
        }
        field = field.split('.')
        if len(field) < 2 or field[0] not in field_objects:
            raise APIException('Parameter "field" should be a in the form "object.key", where "object" takes one of the following values: "%s". "%s" was found instead' % ('", "'.join(field_objects), '.'.join(field)), 400)
        if field_objects[field[0]] is not None and field[1] not in field_objects[field[0]]:
            raise APIException('Invalid key for "%s" in parameter "field", should be one of the following values: "%s". "%s" was found instead' % (field[0], '", "'.join(field_objects[field[0]]), field[1]), 400)

        # return value
        return field, _operators[operator], value

    def _count_documents(self, query):
        return {
            'fields': []
        }

    def post(self, request, node_id):
        """ Query the children of the given node.

            Example #1
            ----------

            Input:
            {
                "pagination": {
                    "offset": 0,
                    "limit": 10
                },
                "retrieve": {
                    "type": "fields",
                    "list": ["name", "metadata.publication_date"]
                },
                "filters": [
                    {"field": "metadata.publication_date", "operator": ">", "value": "2010-01-01 00:00:00"},
                    {"field": "ngrams.terms", "operator": "in", "value": ["bee", "bees"]}
                ],
                "sort": ["name"]
            }

            Output:
            {
                "pagination": {
                    "offset": 0,
                    "limit": 10
                },
                "retrieve": {
                    "type": "fields",
                    "list": ["name", "metadata.publication_date"]
                },
                "results": [
                    {"id": 12, "name": "A document about bees", "publication_date": "2014-12-03 10:00:00"},
                    ...,
                ]
            }
        """

        metadata_aliases = {}

        # validate query
        query_fields = {'pagination', 'retrieve', 'sort', 'filters'}
        for key in request.DATA:
            if key not in query_fields:
                raise APIException('Unrecognized field "%s" in query object. Accepted fields are: "%s"' % (key, '", "'.join(query_fields)), 400)

        # selecting info
        if 'retrieve' not in request.DATA:
            raise APIException('The query should have a "retrieve" parameter.', 400)
        retrieve = request.DATA['retrieve']
        retrieve_types = {'fields', 'aggregates'}
        if 'type' not in retrieve:
            raise APIException('In the query\'s "retrieve" parameter, a "type" should be specified. Possible values are: "%s".' % ('", "'.join(retrieve_types), ), 400)
        if 'list' not in retrieve or not isinstance(retrieve['list'], list):
            raise APIException('In the query\'s "retrieve" parameter, a "list" should be provided as an array', 400)
        if retrieve['type'] not in retrieve_types:
            raise APIException('Unrecognized "type": "%s" in the query\'s "retrieve" parameter. Possible values are: "%s".' % (retrieve['type'], '", "'.join(retrieve_types), ), 400)
        
        if retrieve['type'] == 'fields':
            fields_names = ['id'] + retrieve['list'] if 'id' not in retrieve['list'] else retrieve['list']
        elif retrieve['type'] == 'aggregates':
            fields_names = list(retrieve['list'])
        fields_list = []

        for field_name in fields_names:
            split_field_name = field_name.split('.')
            if split_field_name[0] == 'metadata':
                metadata = Metadata.query(Metadata).filter(Metadata.name == split_field_name[1]).first()
                if metadata is None:
                    metadata_query = Metadata.query(Metadata.name).order_by(Metadata.name)
                    metadata_names = [metadata.name for metadata in metadata_query.all()]
                    raise APIException('Invalid key for "%s" in parameter "field", should be one of the following values: "%s". "%s" was found instead' % (field[0], '", "'.join(metadata_names), field[1]), 400)
                # check or create Node_Metadata alias; join if necessary
                if metadata.id in metadata_aliases:
                    metadata_alias = metadata_aliases[metadata.id]
                else:
                    metadata_alias = metadata_aliases[metadata.id] = aliased(Node_Metadata)
                field = getattr(metadata_alias, 'value_' + metadata.type)
                # operation on field
                if len(split_field_name) > 2:
                    # datetime truncation
                    if metadata.type == 'datetime':
                        datepart = split_field_name[2]
                        accepted_dateparts = ['year', 'month', 'day', 'hour', 'minute']
                        if datepart not in accepted_dateparts:
                            raise APIException('Invalid date truncation for "%s": "%s". Accepted values are: "%s".' % (split_field_name[1], split_field_name[2], '", "'.join(accepted_dateparts), ), 400)
                        # field = extract(datepart, field)
                        field = func.date_trunc(datepart, field)
                        # field = func.date_trunc(text('"%s"'% (datepart,)), field)
            else:
                authorized_field_names = {'id', 'name', }
                authorized_aggregates = {
                    'nodes.count': func.count(Node.id),
                    'ngrams.count': func.count(Ngram.id),
                }
                if retrieve['type'] == 'aggregates' and field_name in authorized_aggregates:
                    field = authorized_aggregates[field_name]
                elif field_name in authorized_field_names:
                    field = getattr(Node, field_name)
                else:
                    raise APIException('Unrecognized "field": "%s" in the query\'s "retrieve" parameter. Possible values are: "%s".' % (field_name, '", "'.join(authorized_field_names), ))
            fields_list.append(
                field.label(
                    field_name if '.' in field_name else 'node.' + field_name
                )
            )

        # starting the query!
        document_type_id = NodeType.query(NodeType.id).filter(NodeType.name == 'Document').scalar()
        query = (session
            .query(*fields_list)
            .select_from(Node)
            .filter(Node.type_id == document_type_id)
            .filter(Node.parent_id == node_id)
        )

        # join ngrams if necessary
        if 'ngrams.count' in fields_names:
            query = (query
                .join(Node_Ngram, Node_Ngram.node_id == Node.id)
                .join(Ngram, Ngram.id == Node_Ngram.ngram_id)
            )

        # join metadata aliases
        for metadata_id, metadata_alias in metadata_aliases.items():
            query = (query
                .join(metadata_alias, metadata_alias.node_id == Node.id)
                .filter(metadata_alias.metadata_id == metadata_id)
            )

        # filtering
        for filter in request.DATA.get('filters', []):
            # parameters extraction & validation
            field, operator, value = self._parse_filter(filter)
            # 
            if field[0] == 'metadata':
                # which metadata?
                metadata = Metadata.query(Metadata).filter(Metadata.name == field[1]).first()
                if metadata is None:
                    metadata_query = Metadata.query(Metadata.name).order_by(Metadata.name)
                    metadata_names = [metadata.name for metadata in metadata_query.all()]
                    raise APIException('Invalid key for "%s" in parameter "field", should be one of the following values: "%s". "%s" was found instead' % (field[0], '", "'.join(metadata_names), field[1]), 400)                
                # check or create Node_Metadata alias; join if necessary
                if metadata.id in metadata_aliases:
                    metadata_alias = metadata_aliases[metadata.id]
                else:
                    metadata_alias = metadata_aliases[metadata.id] = aliased(Node_Metadata)
                    query = (query
                        .join(metadata_alias, metadata_alias.node_id == Node.id)
                        .filter(metadata_alias.metadata_id == metadata.id)
                    )
                # adjust date
                if metadata.type == 'datetime':
                    value = value + '2000-01-01T00:00:00Z'[len(value):]
                # filter query
                query = query.filter(operator(
                    getattr(metadata_alias, 'value_' + metadata.type),
                    value
                ))
            elif field[0] == 'ngrams': 
                query = query.filter(
                    Node.id.in_(Node_Metadata
                        .query(Node_Ngram.node_id)
                        .filter(Node_Ngram.ngram_id == Ngram.id)
                        .filter(operator(
                            getattr(Ngram, field[1]),
                            value
                        ))
                    )
                )

        # TODO: date_trunc (psql) -> index also

        # groupping
        for field_name in fields_names:
            if field_name not in authorized_aggregates:
                # query = query.group_by(text(field_name))
                query = query.group_by('"%s"' % (
                    field_name if '.' in field_name else 'node.' + field_name
                , ))

        # sorting
        sort_fields_names = request.DATA.get('sort', ['id'])
        if not isinstance(sort_fields_names, list):
            raise APIException('The query\'s "sort" parameter should be an array', 400)
        sort_fields_list = []
        for sort_field_name in sort_fields_names:
            try:
                desc = sort_field_name[0] == '-'
                if sort_field_name[0] in {'-', '+'}:
                    sort_field_name = sort_field_name[1:]
                field = fields_list[fields_names.index(sort_field_name)]
                if desc:
                    field = field.desc()
                sort_fields_list.append(field)
            except:
                raise APIException('Unrecognized field "%s" in the query\'s "sort" parameter. Accepted values are: "%s"' % (sort_field_name, '", "'.join(fields_names)), 400)
        query = query.order_by(*sort_fields_list)

        # pagination
        pagination = request.DATA.get('pagination', {})
        for key, value in pagination.items():
            if key not in {'limit', 'offset'}:
                raise APIException('Unrecognized parameter in "pagination": "%s"' % (key, ), 400)
            if not isinstance(value, int):
                raise APIException('In "pagination", "%s" should be an integer.' % (key, ), 400)
        if 'offset' not in pagination:
            pagination['offset'] = 0
        if 'limit' not in pagination:
            pagination['limit'] = 0


        # respond to client!
        # return DebugHttpResponse(str(query))
        # return DebugHttpResponse(literalquery(query))
        results = [
            list(row)
            # dict(zip(fields_names, row))
            for row in (
                query[pagination["offset"]:pagination["offset"]+pagination["limit"]]
                if pagination['limit']
                else query[pagination["offset"]:]
            )
        ]
        pagination["total"] = query.count()
        return Response({
            "pagination": pagination,
            "retrieve": fields_names,
            "sorted": sort_fields_names,
            "results": results,
        }, 201)



class NodesList(APIView):

    def get(self, request):
        query = (Node
            .query(Node.id, Node.name, NodeType.name.label('type'))
            .filter(Node.user_id == request.session._session_cache['_auth_user_id'])
            .join(NodeType)
        )
        if 'type' in request.GET:
            query = query.filter(NodeType.name == request.GET['type'])
        if 'parent' in request.GET:
            query = query.filter(Node.parent_id == int(request.GET['parent']))

        return JsonHttpResponse({'data': [
            node._asdict()
            for node in query.all()
        ]})


class Nodes(APIView):

    def get(self, request, node_id):
        node = session.query(Node).filter(Node.id == node_id).first()
        if node is None:
            raise APIException('This node does not exist', 404)
        return JsonHttpResponse({
            'id': node.id,
            'name': node.name,
            # 'type': node.type__name,
            'metadata': dict(node.metadata),
        })

    # deleting node by id
    # currently, very dangerous.
    # it should take the subnodes into account as well,
    # for better constistency...
    def delete(self, request, node_id):
        node = models.Node.objects.filter(id = node_id)
        msgres = ""
        try:
            node.delete()
            msgres = node_id+" deleted!"
        except:
            msgres ="error deleting: "+node_id


class CorpusController:

    @classmethod
    def get(cls, corpus_id):
        try:
            corpus_id = int(corpus_id)
        except:
            raise ValidationError('Corpora are identified by an integer.', 400)
        corpusQuery = Node.objects.filter(id = corpus_id)
        # print(str(corpusQuery))
        # raise Http404("C'est toujours ça de pris.")
        if not corpusQuery:
            raise Http404("No such corpus: %d" % (corpus_id, ))
        corpus = corpusQuery.first()
        if corpus.type.name != 'Corpus':
            raise Http404("No such corpus: %d" % (corpus_id, ))
        # if corpus.user != request.user:
        #     raise Http403("Unauthorized access.")
        return corpus

    
    @classmethod
    def ngrams(cls, request, node_id):

        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # build query
        ParentNode = aliased(Node)
        query = (Ngram
            .query(Ngram.terms, func.count('*'))
            .join(Node_Ngram, Node_Ngram.ngram_id == Ngram.id)
            .join(Node, Node.id == Node_Ngram.node_id)
            .join(ParentNode, ParentNode.id == Node.parent_id)
            .filter(ParentNode.id == node_id)
            .filter(Ngram.terms.like('%s%%' % (startwith, )))
            .group_by(Ngram.terms)
            .order_by(func.count('*').desc())
        )

        # response building
        format = request.GET.get('format', 'json')
        if format == 'json':
            return JsonHttpResponse({
                "data": [{
                    'terms': row[0],
                    'occurrences': row[1]
                } for row in query.all()],
            })
        elif format == 'csv':
            return CsvHttpResponse(
                [['terms', 'occurences']] + [row for row in query.all()]
            )
        else:
            raise ValidationError('Unrecognized "format=%s", should be "csv" or "json"' % (format, ))

   
