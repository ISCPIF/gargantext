# Gargantext lib
from gargantext.util.db           import session
from gargantext.util.http         import JsonHttpResponse
from gargantext.models            import Node, Ngram, NodeNgram, NodeNgramNgram

#from gargantext.util.toolchain.ngram_coocs import compute_coocs
from graphExplorer.cooccurrences  import countCooccurrences
from graphExplorer.distances      import clusterByDistances
from graphExplorer.bridgeness     import filterByBridgeness

# Prelude lib
from copy                         import copy, deepcopy
from collections                  import defaultdict
from sqlalchemy.orm               import aliased

# Math/Graph lib
import math
import pandas                     as pd
import numpy                      as np

import networkx                   as nx


def get_graph( request=None         , corpus=None
            , field1='ngrams'       , field2='ngrams'
            , mapList_id = None     , groupList_id = None
            , cooc_id=None          , type='node_link'
            , start=None            , end=None
            , threshold=1
            , distance='conditional'
            , isMonopartite=True                # By default, we compute terms/terms graph
            , bridgeness=5
            #, size=1000
        ):
    '''
    Get_graph : main steps:
    1) count Cooccurrences  (function countCooccurrences)
            main parameters: threshold

    2) filter and cluster By Distances (function clusterByDistances)
            main parameter: distance

    3) filter By Bridgeness (filter By Bridgeness)
            main parameter: bridgness

    4) format the graph     (formatGraph)
            main parameter: format_

    '''

    from datetime import datetime

    before_cooc = datetime.now()

    # TODO change test here (always true)
    #      to something like "if cooc.status threshold == required_threshold
    #                         and group.creation_time < cooc.creation_time"
    #      if False => read and give to clusterByDistances
    #      if True => compute and give to clusterByDistances  <==
    if cooc_id == None:
        cooc_matrix = countCooccurrences( corpus=corpus
                                   #, field1="ngrams", field2="ngrams"
                                    , start=start           , end =end
                                    , mapList_id=mapList_id , groupList_id=groupList_id
                                    , isMonopartite=True    , threshold = threshold
                                    , just_pass_result = True
                                   #, limit=size
                                    )
    else:
        cooc_matrix = WeightedMatrix(cooc_id)

    # fyi
    after_cooc = datetime.now()
    print("... Cooccurrences took %f s." % (after_cooc - before_cooc).total_seconds())

    G, partition, ids, weight = clusterByDistances ( cooc_matrix
                                                   , field1="ngrams", field2="ngrams"
                                                   , distance=distance
                                                   )

    after_cluster = datetime.now()
    print("... Clustering took %f s." % (after_cluster - after_cooc).total_seconds())

    data = filterByBridgeness(G,partition,ids,weight,bridgeness,type,field1,field2)

    after_filter = datetime.now()
    print("... Filtering took %f s." % (after_filter - after_cluster).total_seconds())

    return data