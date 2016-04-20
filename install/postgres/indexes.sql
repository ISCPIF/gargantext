--                       ____ 
--                      / ___|
--                     | |  _ 
--                     | |_| |
--                      \____|arganTexT
----------------------------------------------------------------------
--                  Gargantext optimization of Database             --
----------------------------------------------------------------------

--> Manual optimization with indexes according to usages
-- Weakness and Strengths of indexes:
    --> it can slow down the insertion(s)
    --> it can speed up  the selection(s)

--> Conventions for this document:
    --> indexes commented already have been created 
    --> indexes not commented have not been created yet

----------------------------------------------------------------------
-- Retrieve Nodes
----------------------------------------------------------------------
-- create INDEX on nodes (user_id, typename, parent_id) ;
-- create INDEX on nodes_hyperdata (node_id, key);
-- create INDEX on ngrams (id, n) ;
-- create INDEX on nodes_ngrams (node_id, ngram_id) ;
-- create INDEX on nodes_ngrams_ngrams (node_id, ngram1_id, ngram2_id) ;

----------------------------------------------------------------------
-- DELETE optimization of Nodes
create INDEX on nodes_nodes_ngrams (node1_id);
create INDEX on nodes_nodes_ngrams (node2_id);

-- Maybe needed soon:
-- create INDEX on nodes_nodes_ngrams (node1_id, node2_id);
----------------------------------------------------------------------
----------------------------------------------------------------------
----------------------------------------------------------------------
----------------------------------------------------------------------
