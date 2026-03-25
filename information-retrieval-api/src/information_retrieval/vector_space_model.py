import logging
import math
from typing import Any, List
from db.processed_posts import get_all_processed_posts
import information_retrieval.globals
import information_retrieval.linked_list
import numpy as np

logger = logging.getLogger(__name__)

async def search_vector_space_model(query: List[str]) -> List[int]: 
    """
    Creates the Queryvector and calculates the cosine similiarity between the Queryvector and the Documentvectors
    """
    # Get all processed Posts to 
    posts = await get_all_processed_posts()
    posts = [(post.id, post.content) for post in posts]

    # Calculate the document frequency (DF) for each term
    total_documents = len(posts)
    inverse_document_frequency = {}
    # Matrix dimension 1x1

    for term in information_retrieval.globals._vocabulary:
        df = information_retrieval.globals._inverted_index[term].length()
        # Calculate the inverse document frequency (IDF) for each term
        inverse_document_frequency[term] = compute_inverse_document_frequency(total_documents, df)
 
    if not information_retrieval.globals._document_svd_matrix:
        return []

    # creating the tfidf-query vector
    tfidf_vector = [compute_tf_idf_weighting(compute_sublinear_tf_scaling(query.count(term)), inverse_document_frequency[term]) for term in information_retrieval.globals._vocabulary]

    flat_transposed_query_vector = calculate_dimension_reduced_query(tfidf_vector)

    if flat_transposed_query_vector.size == 0:
        return []

    
    # Map each document by id to the corressponding cosinec similiarity
    doc_cosine_similiarity_map = {}
    for doc_id, vector in information_retrieval.globals._document_svd_matrix.items():
        # Calculate the Cosine similiarity by using the numpy library
        # Calculating the dot product between the Queryvector and the Documentvector
        dot_product = np.dot(flat_transposed_query_vector, vector)
        # Calculate the norms for the Queryvector and the Documentvector
        magnitude_query = np.linalg.norm(flat_transposed_query_vector)
        magnitude_entry = np.linalg.norm(vector)
        if magnitude_query == 0 or magnitude_entry == 0:
            continue
        # Calculating the Cosine similiarity
        cosine_similarity = dot_product / (magnitude_query * magnitude_entry)
        # multiply cosine similarity with the date coefficient
        cosine_similarity *= information_retrieval.globals._date_coefficient[doc_id]
        # Adding the Results to the map created before
        doc_cosine_similiarity_map[doc_id] = cosine_similarity 
    # Sort the map by the highest cosine similiarity, lambda takes the second index in the tuple and used these to sort
    sorted_docs = sorted(doc_cosine_similiarity_map.items(), key=lambda x: x[1], reverse=True)
    # Extract the sorted document IDs into a list
    # In this contex "_" is a placeholder, we are not interested in it so we use this convention
    sorted_doc_ids = [doc_id for doc_id, _ in sorted_docs if _ > 0.0]
    
    return sorted_doc_ids

async def build_vector_space_model():
    """
    Build the Vector Space Model
    """
    vocabulary: List[str] = information_retrieval.globals._vocabulary
    
    logger.info("Building Vector Space Model")
        
    posts = await get_all_processed_posts()
    posts = [(post.id, post.content) for post in posts]

    # Calculate the document frequency (DF) for each term
    total_documents = len(posts)
    inverse_document_frequency = {}

    for term in vocabulary:
        # Calculate the df it is the length of the linked list of occurance documents for a particular term
        df : int = information_retrieval.globals._inverted_index[term].length()
        # Calculate the inverse document frequency (IDF) for each term
        inverse_document_frequency[term] = compute_inverse_document_frequency(total_documents, df)

    for post in posts:
        # Every post has its own vector these are created below and added in the corresponding maps
        tfidf_vector = [compute_tf_idf_weighting(compute_sublinear_tf_scaling(post[1].count(term)), inverse_document_frequency[term]) for term in vocabulary]
        # Matrix dimension is term x documents
        # matrix has now the dimension (524, 6643) => dokument to word if i want the word to ducment matrix i have to transpose the matrix
        information_retrieval.globals._document_term_weight_matrix.append(tfidf_vector)
        information_retrieval.globals._document_id_vector_map[post[0]] = tfidf_vector 
    
    
    logger.info("Vector Space Model Built")
    return None

def compute_inverse_document_frequency(N : int, df: int) -> float:
    return math.log2(N/df)

def compute_tf_idf_weighting(tf: float, idf: float) -> float:
    return tf * idf

def compute_sublinear_tf_scaling(tf: int) -> float:
    if tf > 0:
        return 1 + math.log(tf) 
    return 0

def calculate_dimension_reduced_query(tfidf_query_vector: List[float]) -> np.ndarray[Any]:
    """
    Calculate the dimension reduced query with the following formula: q = q^T * U_k * S_k^-1
    """
    if len(information_retrieval.globals._S_reduced) == 0 or len(information_retrieval.globals._U_reduced) == 0:
        return np.array([])

     # transpose tfidf vector to calculate the new dimensional reduced query vector
    square_s_reduced = np.diag(information_retrieval.globals._S_reduced)
    # Use pseudo-inverse to handle singular matrices safely.
    s_k_inv = np.linalg.pinv(square_s_reduced)
    
    # convert the tfidf_vector to a numpy matrix shape = (k,1)
    numpy_matrix_query = np.matrix(tfidf_query_vector)
    
    #calculate the new dimension reduced query with following formular q = q^T * U_k * S_k^-1
    reduced_query_vector_U = np.dot(numpy_matrix_query, information_retrieval.globals._U_reduced)
    reduced_query_vector = np.dot(reduced_query_vector_U, s_k_inv)

    # reduced query has the shape of (1,k); in order to calculate the cosine similiarity we need to transpose the vector back in the shape (k,1)
    transposed_query_vector = np.transpose(reduced_query_vector)
    #convert reduced query vector to a matrix with shape (k,) numpy specific read numpy doc for specification
    flat_transposed_query_vector = np.ravel(transposed_query_vector)

    return flat_transposed_query_vector

async def execute_singualar_value_decomposition():
    """
    Singular Value Decomposition
    """
    logger.info("Start Executing SVD")
    documents_vector_list = list(information_retrieval.globals._document_id_vector_map.items()) # get the list of documents and their vectors
    vector_list = [vector for _, vector in documents_vector_list] # get the list of vectors
    documentids_list = [doc_id for doc_id, _ in documents_vector_list] # get the list of document ids
    if not vector_list:
        information_retrieval.globals._U_reduced = np.array([])
        information_retrieval.globals._S_reduced = np.array([])
        information_retrieval.globals._V_reduced = np.array([])
        information_retrieval.globals._document_svd_matrix = {}
        logger.info("SVD skipped: no vectors available")
        return None

    original_matrix = np.matrix(vector_list) # create a matrix from the list of vectors
    original_matrix = original_matrix.transpose() # transpose the matrix to get the word to document matrix
    
    U, S, Vt = np.linalg.svd(original_matrix)
    
    # get the number of values that represent 90% of the sum
    sum_of_values = sum(S)    
    threshold = sum_of_values * 0.9
    cumulative_values = np.cumsum(S)
    k = int(np.searchsorted(cumulative_values, threshold, side="left") + 1)
    k = max(1, min(k, len(S)))
            
    # reduce the dimensionality of the matrix
    information_retrieval.globals._U_reduced = U[:, :k]
    information_retrieval.globals._S_reduced = S[:k]
    Vt_reduced = Vt[:k, :]
    information_retrieval.globals._V_reduced = Vt_reduced.transpose() # transpose the matrix to get the document to word matrix
    
    # assign reduced eigenvectors to documents    
    i = 0
    for doc_id in documentids_list:
        vector = np.ravel(information_retrieval.globals._V_reduced[i,:]) # Get the ith row of the V_reduced matrix and convert it to a 1D array
        information_retrieval.globals._document_svd_matrix[doc_id] = vector 
        i += 1
    logger.info("SVD executed")