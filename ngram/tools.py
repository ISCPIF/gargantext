
from gargantext_web.db import Ngram, NodeNgramNgram

from gargantext_web.db import get_cursor, bulk_insert


def insert_ngrams(ngrams,get='terms-id'):
    '''
    insert_ngrams :: [String, Int] -> dict[terms] = id
    '''
    db, cursor = get_cursor()
    
    cursor.execute('''    
        CREATE TEMPORARY TABLE tmp__ngram (
            id INT,
            terms VARCHAR(255) NOT NULL,
            n INT
            );
        ''')

    bulk_insert('tmp__ngram', ['terms', 'n'], ngrams, cursor=cursor)
    
    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            tmp__ngram.terms = ngram.terms
            ''' % (Ngram.__table__.name,))
    
    cursor.execute('''
        INSERT INTO
            %s (terms, n)
        SELECT
            terms, n
        FROM
            tmp__ngram
        WHERE
            id IS NULL
            ''' % (Ngram.__table__.name,))
    
    
    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngram.terms
        AND
            ngram.n = tmp__ngram.n
        AND
            tmp__ngram.id IS NULL
            ''' % (Ngram.__table__.name,))
    
    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngram')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]

    db.commit()
    return(ngram_ids)

def insert_nodengramngram(nodengramngram):
    db, cursor = get_cursor()
    
    cursor.execute('''    
        CREATE TEMPORARY TABLE tmp__nnn (
            id INT,
            node_id INT,
            ngramx_id INT,
            ngramy_id  INT
            );
        ''')

    bulk_insert('tmp__nnn', ['node_id', 'ngramx_id', 'ngramy_id'], nodengramngram, cursor=cursor)

    # nnn = NodeNgramNgram
    cursor.execute('''
        UPDATE
             tmp__nnn
        SET
            id = nnn.id
        FROM
            %s AS nnn
        WHERE
            tmp__nnn.node_id = nnn.node_id
        AND
            tmp__nnn.ngramx_id = nnn.ngramx_id
        AND
            tmp__nnn.ngramy_id = nnn.ngramy_id
            ''' % (NodeNgramNgram.__table__.name,))
    
    
    cursor.execute('''
        INSERT INTO
            %s (node_id, ngramx_id, ngramy_id, score)
        SELECT
            node_id, ngramx_id, ngramy_id, 1
        FROM 
            tmp__nnn
        WHERE
            id is NULL
            ''' % (NodeNgramNgram.__table__.name,))
        
    db.commit()



#def queryNodeNodeNgram(nodeMeasure_id=None, corpus_id=None, limit=None):
#    '''
#    queryNodeNodeNgram :: Int -> Int -> Int -> (Int, String, Float)
#    Get list of ngrams according to a measure related to the corpus: maybe tfidf
#    cvalue.
#    '''
#    query = (session.query(Ngram.id, Ngram.terms, NodeNodeNgram.score)
#                    .join(NodeNodeNgram, NodeNodeNgram.ngram_id == Ngram.id)
#                    .join(Node, Node.id == NodeNodeNgram.nodex_id)
#                    .filter(NodeNodeNgram.nodex_id == nodeMeasure_id)
#                    .filter(NodeNodeNgram.nodey_id == corpus_id)
#                    .group_by(Ngram.id, Ngram.terms, NodeNodeNgram.score)
#                    .order_by(desc(NodeNodeNgram.score))
#            )
#
#    if limit is None:
#        query = query.count()
#    elif limit == 0 :
#        query = query.all()
#    else:
#        query = query.limit(limit)
#
#    return(query)
#
