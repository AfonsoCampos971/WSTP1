import json, requests
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient

endpoint = "http://localhost:7200"
repo_name = "pitchstats"
client = ApiClient(endpoint=endpoint)
accessor = GraphDBApi(client)
pred = "http://pitchstats/pred/"
ent = "http://pitchstats/ent/"


def get_review_count():
    query = """
        PREFIX pred: <http://pitchstats/pred/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT DISTINCT (COUNT(?review) as ?count) (MAX(xsd:float(?id)) as ?higher_id) WHERE {
           ?review pred:id ?id .
        }
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    return int(res['results']['bindings'][0]['count']['value']), int(res['results']['bindings'][0]['higher_id']['value'])


def get_author_types():
    query = """
        PREFIX pred: <http://pitchstats/pred/>
        
        SELECT DISTINCT ?type WHERE {
            ?author pred:author_type ?type .
        }
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    types = [_type['type']['value'] for _type in res['results']['bindings']]

    return types


def get_reviews(sort_by="date", sort_order=0, filter_genre=None, filter_best_new_music=None, filter_date_start=None,
                filter_date_end=None, filter_score_low=None, filter_score_high=None, filter_title=None,
                filter_artist=None, filter_label=None, filter_author=None, filter_review=None, page=0, page_size=10):
    offset = page * page_size if page_size else 0

    if sort_by == "date":
        sort_string = f"ORDER BY {'?date' if sort_order else 'DESC(?date)'}"
    elif sort_by == "alpha":
        sort_string = f"ORDER BY {'?title' if sort_order else 'DESC(?title)'}"
    elif sort_by == "score":
        sort_string = f"ORDER BY {'?score' if sort_order else 'DESC(?score)'}"
    else:
        sort_string = ''

    filters = []
    if filter_genre: filters.append(f"FILTER regex(?genre, \"{filter_genre}\", \"i\")")
    if filter_best_new_music is not None: filters.append(
        f"FILTER (xsd:integer(?best_new_music) = {filter_best_new_music})")
    if filter_date_start: filters.append(f"FILTER (?date >= \"{filter_date_start}\")")
    if filter_date_end: filters.append(f"FILTER (?date <= \"{filter_date_end}\")")
    if filter_score_low: filters.append(f"FILTER (xsd:float(?score) >= {filter_score_low})")
    if filter_score_high: filters.append(f"FILTER (xsd:float(?score) <= {filter_score_high})")
    if filter_title: filters.append(f"FILTER regex(?title, \"{filter_title}\", \"i\")")

    filters_inner = []
    if filter_review: filters_inner.append(f"<{filter_review}> pred:url ?url .")
    if filter_artist: filters_inner.append(f"?review pred:artist <{filter_artist}> .")
    if filter_label: filters_inner.append(f"?review pred:label <{filter_label}> .")
    if filter_author: filters_inner.append(f"?review pred:author <{filter_author}> .")

    filter_string = ''
    for filter in filters:
        filter_string += "\t" + filter + "\n"

    filter_inner_string = ''
    for filter in filters_inner:
        filter_inner_string += "\t" + filter + "\n"

    limit_string = ''
    if page_size:
        limit_string = f"LIMIT {page_size}"

    query = f"""
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?review ?title ?score ?url ?best_new_music ?date WHERE {{
        {{
            {filter_inner_string}
            ?review pred:album ?title .
            ?review pred:date ?date .
            ?review pred:score ?score .
            ?review pred:url ?url .
            OPTIONAL {{?review pred:genre ?genre}} .
            ?review pred:best_new ?best_new_music .
            {filter_string}
        }}
        
    }} {sort_string}
    OFFSET {offset}
    {limit_string}
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    reviews = [{key: val['value'] for key, val in review.items()} for review in res['results']['bindings']]

    for idx, review in enumerate(reviews):
        reviews[idx]['authors'] = get_authors(reviews[idx]['review'])
        reviews[idx]['genres'] = get_genres(filter_review=reviews[idx]['review'])
        reviews[idx]['artists'] = get_artists(filter_review=reviews[idx]['review'])
        reviews[idx]['labels'] = get_labels(filter_review=reviews[idx]['review'])
        reviews[idx]['id'] = review['review'].split("/")[-1]

    return reviews


def get_artists(filter_review=None, filter_label=None):
    review_str = f"<{filter_review}> pred:artist ?artist ." if filter_review else ""
    label_str = f"?review pred:label <{filter_label}> ." if filter_label else ""

    query = f"""
                PREFIX pred: <http://pitchstats/pred/>

                SELECT DISTINCT ?artist ?name WHERE {{
                    {review_str}
                    {label_str}
                    ?review pred:artist ?artist .
                    ?artist pred:name ?name .
                }} ORDER BY ?name
            """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    artists = [(artist['artist']['value'], artist['name']['value'], artist['artist']['value'].split("/")[-1]) for artist
               in res['results']['bindings']]

    return artists


def get_authors(filter_review=None):
    review_str = f"<{filter_review}> pred:author ?author ." if filter_review else ""

    query = f"""
        PREFIX pred: <http://pitchstats/pred/>

        SELECT DISTINCT ?author ?name WHERE {{
            {review_str}
            ?review pred:author ?author .
            ?author pred:name ?name .
        }} ORDER BY ?name
        """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    authors = [(author['author']['value'], author['name']['value'], author['author']['value'].split("/")[-1]) for author
               in res['results']['bindings']]

    return authors


def get_genres(filter_artist=None, filter_review=None, filter_author=None, filter_label=None):
    artist_str = f"?review pred:artist <{filter_artist}> ." if filter_artist else ""
    author_str = f"?review pred:author <{filter_author}> ." if filter_author else ""
    label_str = f"?review pred:label <{filter_label}> ." if filter_label else ""

    query = f"""
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?genre (COUNT(?review) as ?review_count) (AVG(xsd:float(?score)) as ?avg_score) (SUM(IF(?best_new = "1", 1, 0)) as ?best_new_count) WHERE {{
        {author_str}
        {artist_str}    
        {label_str}
        {"?review pred:genre ?genre ." if not filter_review else f"<{filter_review}> pred:genre ?genre ."}
        ?review pred:score ?score .
        ?review pred:best_new ?best_new .
    }} GROUP BY ?genre
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    genres = [(genre['genre']['value'], genre['review_count']['value'], genre['avg_score']['value'],
               genre['best_new_count']['value']) for genre in
              res['results']['bindings']]

    return genres


def get_labels(filter_artist=None, filter_review=None):
    artist_str = f"?review pred:artist <{filter_artist}> ." if filter_artist else ""
    review_str = f"<{filter_review}> pred:label ?label ." if filter_review else ""

    query = f"""
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?label ?name WHERE {{
        {review_str}
        {artist_str}
        ?review pred:label ?label .
        ?label pred:name ?name .
    }} ORDER BY ?name
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    labels = [(label['label']['value'], label['name']['value'], label['label']['value'].split("/")[-1]) for label in
              res['results']['bindings']]

    return labels


def get_artist_detail(artist_uri):
    info = dict()

    query = f"""
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?name (AVG(xsd:float(?score)) as ?avg_score) WHERE {{
        <{artist_uri}> pred:name ?name .
        ?review pred:artist <{artist_uri}> .
        ?review pred:score ?score .
    }} GROUP BY ?name 
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    if res['results']['bindings']:
        info["name"] = res['results']['bindings'][0]['name']['value']
        info["avg_score"] = res['results']['bindings'][0]['avg_score']['value']
        info["id"] = artist_uri.split("/")[-1]
    else:
        return None

    info["reviews"] = get_reviews(filter_artist=artist_uri, page_size=None)

    info["labels"] = get_labels(filter_artist=artist_uri)

    info["genres"] = get_genres(filter_artist=artist_uri)

    return info


def get_author_detail(author_uri):
    info = dict()

    query = f"""
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?name (AVG(xsd:float(?score)) as ?avg_score) WHERE {{
        <{author_uri}> pred:name ?name .
        ?review pred:author <{author_uri}> .
        ?review pred:score ?score .
    }} GROUP BY ?name
    """
    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    if res['results']['bindings']:
        info["name"] = res['results']['bindings'][0]['name']['value']
        info["avg_score"] = res['results']['bindings'][0]['avg_score']['value']
        info["id"] = author_uri.split("/")[-1]
    else:
        return None

    info["reviews"] = get_reviews(filter_author=author_uri, page_size=None)

    info["genres"] = get_genres(filter_author=author_uri)

    query = f"""
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?type ?date WHERE {{
        ?review pred:author <{author_uri}> .
        ?review pred:author_type ?type .
        ?review pred:date ?date .
    }} ORDER BY ?date
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    info["roles"] = [(role["type"]["value"], role["date"]["value"]) for role in res["results"]["bindings"]]

    return info


def get_label_detail(label_uri):
    info = dict()

    query = f"""
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX pred: <http://pitchstats/pred/>

    SELECT DISTINCT ?name (AVG(xsd:float(?score)) as ?avg_score) WHERE {{
        <{label_uri}> pred:name ?name .
        ?review pred:label <{label_uri}> .
        ?review pred:score ?score .
    }} GROUP BY ?name
    """

    payload_query = {"query": query}
    res = accessor.sparql_select(body=payload_query, repo_name=repo_name)

    res = json.loads(res)

    if res['results']['bindings']:
        info["name"] = res['results']['bindings'][0]['name']['value']
        info["avg_score"] = res['results']['bindings'][0]['avg_score']['value']
        info["id"] = label_uri.split("/")[-1]
    else:
        return None

    info["reviews"] = get_reviews(filter_label=label_uri, page_size=None)

    info["artists"] = get_artists(filter_label=label_uri)

    info["genres"] = get_genres(filter_label=label_uri)

    return info


def new_review(title, score, best_new, url, date, author_uri, author_type, artist_uri, label_uri, genre):
    _, review_id = get_review_count()
    review_id += 1

    query = f"""
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX pred: <http://pitchstats/pred/>
        PREFIX rev: <http://pitchstats/ent/review/>

        INSERT DATA {{
            rev:{review_id} pred:id "{review_id}" ;
                            pred:album "{title}" ;
                            pred:score "{score}" ;
                            pred:best_new "{best_new}" ;
                            pred:url "{url}" ;
                            pred:date "{date}" ;
                            pred:author <{author_uri}> ;
                            pred:author_type "{author_type}" ;
                            pred:artist <{artist_uri}> ;
                            pred:label <{label_uri}> ;
                            pred:genre "{genre}" .
        }}
    """

    payload_query = {"update": query}
    res = accessor.sparql_update(body=payload_query, repo_name=repo_name)

    return review_id


