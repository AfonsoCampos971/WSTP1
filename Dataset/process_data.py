import sqlite3
import re
from rdflib import Graph, Namespace

BASE_URI = "http://pitchstats/"

def gen_uri(prefix, id):
    return f"{BASE_URI}{prefix}{id}"

def resolve_author_name(name):
    authors = set()
    duplicate_authors = {
        "alex lindhart": "alexander linhardt",
        "alexander lloyd linhardt": "alex linhardt",
        "andy o' connor": "andy o'connor",
        "ben scheim": "benjamin scheim",
        "chris weber": "christopher weber",
        "cory d. byrom": "cory byrom",
        "dr. andy beta": "andy beta",
        "edwin \"stats\" houghton": "edwin stats houghton",
        "grayson haver currin": "grayson currin",
        "josh love": "joshua love",
        "katherine st asaph": "katherine st. asaph",
        "kim fing shannon": "kim shannon",
        "malcolm seymour iii": "malcolm seymour",
        "matt stephens": "matthew stephens",
        "matt wellins": "matthew wellins",
        "mike bernstein": "michael bernstein",
        "nicholas b. sylvester": "nick sylvester",
        "pj gallagher": "p.j. gallagher",
        "saby reyes kulkarni": "savy reyes-kulkarni",
        "sean fennessey": "sean fennessy",
        "seth colter walls": "seth colter-walls",
        "stephen m. duesner": "stephen deusner",
        "stephen m. deusner": "stephen deusner",
        "stephen  m. deusner": "stephen deusner",
        "stosh \"piz\" piznarski": "stosh piz piznarski"
    }

    name = name.strip()
    if name == "choppa moussaoui, with help from mullah omar, ethan p, and": 
        authors.add("choppa moussaoui")
        authors.add("mullah omar")
        authors.add("ethan p")
    elif "," in name or "&" in name:
        for name_inner in re.split("&|,", name):
            name_inner = name_inner.strip()
            if name_inner in duplicate_authors:
                name_inner = duplicate_authors[name_inner]
            authors.add(name_inner)
    else:
        if name in duplicate_authors:
            name = duplicate_authors[name]
        authors.add(name)
    return authors
    

# SQLite Vars
con = sqlite3.connect("database.sqlite")
cur = con.cursor()

triples = []

# Create Author triples

query = cur.execute("SELECT DISTINCT author FROM reviews").fetchall()
authors = set()
for name in query:
    new_authors = resolve_author_name(name[0])
    authors = authors.union(new_authors)
author_uri_map = {author.strip() : gen_uri("ent/author/",id) for id, author in enumerate(authors)}
for name in authors: 
    name_value = name.title().replace('"','')
    triple = f"<{author_uri_map[name]}> <http://pitchstats/pred/name> \"{name_value}\" ."
    triples.append(triple)

# Create Label triples
query = cur.execute("SELECT DISTINCT label FROM labels").fetchall()
labels = {label[0].strip() for label in query if label[0]}
label_uri_map = {label.strip() : gen_uri("ent/label/",id) for id, label in enumerate(labels)}
for name in labels: 
    name_value = name.title().replace('"','')
    triple = f"<{label_uri_map[name]}> <http://pitchstats/pred/name> \"{name_value}\" ."
    triples.append(triple)

# Create Artist triples
query = cur.execute("SELECT DISTINCT artist FROM artists").fetchall()
artists = {artist[0].strip() for artist in query if artist[0]}
artist_uri_map = {artist.strip() : gen_uri("ent/artist/",id) for id, artist in enumerate(artists)}
for name in artists: 
    name_value = name.title().replace('"','')
    triple = f"<{artist_uri_map[name]}> <http://pitchstats/pred/name> \"{name_value}\" ."
    triples.append(triple)

# Create Review triples
query = cur.execute("SELECT DISTINCT reviewid, title, url, score, pub_date, best_new_music, author, author_type FROM reviews").fetchall()
review_uri_mapping = {id : gen_uri("ent/review/",id) for id, _, _, _, _, _, _, _ in query}
for review_id, album, url, score, pub_date, best_new, author, author_type in query:
    if not album or not score: continue
    new_triples = list()

    triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/id> \"{review_id}\" ."
    new_triples.append(triple)

    name_value = album.title().replace('"','').replace("\\","")
    triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/album> \"{name_value}\" ."
    new_triples.append(triple)

    triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/score> \"{score}\" ."
    new_triples.append(triple)

    triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/best_new> \"{best_new}\" ."
    new_triples.append(triple)

    if url:
        triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/url> \"{url}\" ."
        new_triples.append(triple)

    if pub_date:
        triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/date> \"{pub_date}\" ."
        new_triples.append(triple)

    if author:
        authors = resolve_author_name(author)
        for auth in authors:
            triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/author> <{author_uri_map[auth]}> ."
            new_triples.append(triple)

        if author_type:
            triple = f"<{review_uri_mapping[review_id]}> <http://pitchstats/pred/author_type> \"{author_type}\" ."
            new_triples.append(triple)
    
    triples += new_triples

query = cur.execute(f"SELECT DISTINCT artist, reviewid FROM artists").fetchall()
for artist, id in query:
    if artist:
        triple = f"<{review_uri_mapping[id]}> <http://pitchstats/pred/artist> <{artist_uri_map[artist.strip()]}> ."
        triples.append(triple)

query = cur.execute(f"SELECT DISTINCT label, reviewid FROM labels").fetchall()
for label, id in query:
    if label:
        triple = f"<{review_uri_mapping[id]}> <http://pitchstats/pred/label> <{label_uri_map[label.strip()]}> ."
        triples.append(triple)

query = cur.execute("SELECT DISTINCT genre, reviewid FROM genres").fetchall()
for genre, id in query:
    if genre:
        name_value = genre.strip().title().replace('"','')
        triple = f"<{review_uri_mapping[id]}> <http://pitchstats/pred/genre> \"{name_value}\" ."
        triples.append(triple)

with open("pitchstats.nt", "w") as f:
    for triple in triples:
        f.write(triple+"\n")

g = Graph()
g.parse('pitchstats.nt')

pred = Namespace("http://pitchstats/pred/")
ent = Namespace("http://pitchstats/ent/")

g.bind("pred", pred)
g.bind("ent", ent)

n3 = g.serialize(format='n3')

with open("pitchstats.n3", "w") as f:
    f.write(n3)

