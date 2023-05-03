from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from datetime import datetime
from math import ceil
from .queries import *


# Create your views here.
def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    try:
        sort_order = int(request.GET.get('order', 0))
    except ValueError:
        sort_order = 0

    try:
        page = int(request.GET.get('page', 0))
    except ValueError:
        page = 0

    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10

    filter_genre = request.GET.get('genre', None)
    filter_best_new_music = request.GET.get('best_new_music', None)
    filter_date_start = request.GET.get('start_date', None)
    filter_date_end = request.GET.get('end_date', None)
    filter_score_low = request.GET.get('score_low', None)
    filter_score_high = request.GET.get('score_high', None)
    filter_title = request.GET.get('title', None)
    filter_author = request.GET.get('author', None)
    filter_artist = request.GET.get('artist', None)
    filter_label = request.GET.get('label', None)
    sort_by = request.GET.get('sort', 'date')

    if sort_by == "": sort_by = 'date'
    if filter_genre == "": filter_genre = None
    if filter_best_new_music == "": filter_best_new_music = None
    if filter_date_start == "": filter_date_start = None
    if filter_date_end == "": filter_date_end = None
    if filter_score_low == "": filter_score_low = None
    if filter_score_high == "": filter_score_high = None
    if filter_title == "": filter_title = None
    if filter_artist == "" or not filter_artist:
        filter_artist = None
    else:
        filter_artist = f"http://pitchstats/ent/artist/{filter_artist}"
    if filter_author == "" or not filter_author:
        filter_author = None
    else:
        filter_author = f"http://pitchstats/ent/author/{filter_author}"
    if filter_label == "" or not filter_label:
        filter_label = None
    else:
        filter_label = f"http://pitchstats/ent/label/{filter_label}"

    reviews = get_reviews(sort_by=sort_by, sort_order=sort_order, filter_genre=filter_genre,
                          filter_best_new_music=filter_best_new_music, filter_date_end=filter_date_end,
                          filter_date_start=filter_date_start, filter_score_low=filter_score_low,
                          filter_score_high=filter_score_high, filter_title=filter_title, page=page,
                          page_size=page_size, filter_author=filter_author, filter_artist=filter_artist, filter_label=filter_label)

    genres = get_genres()

    artists = get_artists()

    authors = get_authors()

    labels = get_labels()

    tparams = {
        'reviews': reviews,
        'current_page': page,
        'page_size': page_size,
        'genres': genres,
        'artists': artists,
        'authors': authors,
        'labels': labels
    }
    return render(request, 'index.html', tparams)


def genre_list(request):
    assert isinstance(request, HttpRequest)
    genres = get_genres()
    return render(request, 'genres.html', {"genres": genres})


def artist_detail(request, pk):
    assert isinstance(request, HttpRequest)
    artist_uri = f"http://pitchstats/ent/artist/{pk}"
    artist = get_artist_detail(artist_uri)
    return render(request, 'artist_detail.html', {"artist": artist})


def review_detail(request, pk):
    assert isinstance(request, HttpRequest)
    review_uri = f"http://pitchstats/ent/review/{pk}"
    reviews = get_reviews(filter_review=review_uri)
    review = reviews[0]
    return render(request, 'review_detail.html', {"review": review})


def author_detail(request, pk):
    assert isinstance(request, HttpRequest)
    author_uri = f"http://pitchstats/ent/author/{pk}"
    author = get_author_detail(author_uri)

    roles = author['roles']
    roles_span = []
    if roles:
        start_date = None
        current_role = None

        for i, (role, date) in enumerate(roles):
            role = role.strip().lower().title()
            if i == 0:
                start_date = date
                current_role = role
            elif role != current_role:
                print(role, current_role)
                roles_span.append((current_role, start_date, prev_date))
                start_date = date
                current_role = role
            prev_date = date

        roles_span.append((current_role, start_date, "present"))

    return render(request, 'author_detail.html', {"author": author, "roles": roles_span})


def label_detail(request, pk):
    assert isinstance(request, HttpRequest)
    label_uri = f"http://pitchstats/ent/label/{pk}"
    label = get_label_detail(label_uri)
    return render(request, 'label_detail.html', {"label": label})


def create_review(request):
    assert isinstance(request, HttpRequest)
    artists = get_artists()

    authors = get_authors()

    labels = get_labels()

    genres = get_genres()

    types = get_author_types()

    tparams = {
        'artists': artists,
        'authors': authors,
        'labels': labels,
        'genres': genres,
        'types': types
    }
    return render(request, 'create_review.html', tparams)


def reviews(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        score = request.POST.get('score')
        best_new_music = request.POST.get('best_new_music')
        url = request.POST.get('url')
        date = request.POST.get('date')
        author = request.POST.get('author')
        author_type = request.POST.get('type')
        artist = request.POST.get('artist')
        label = request.POST.get('label')
        genre = request.POST.get('genre')

        review_id = new_review(title, score, best_new_music, url, date, author, author_type, artist, label, genre)

        return redirect(f'/reviews/{review_id}')

    if request.method == "GET":
        return redirect('home')
