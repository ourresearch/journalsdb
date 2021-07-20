def build_link_header(query, base_url, per_page):
    """
    Adds pagination link headers to an API response.
    """
    links = [
        '<{0}?page=1&per-page={1}>; rel="first"'.format(base_url, per_page),
        '<{0}?page={1}&per-page={2}>; rel="last"'.format(
            base_url, query.pages, per_page
        ),
    ]
    if query.has_prev:
        links.append(
            '<{0}?page={1}&per-page={2}>; rel="prev"'.format(
                base_url, query.prev_num, per_page
            )
        )
    if query.has_next:
        links.append(
            '<{0}?page={1}&per-page={2}>; rel="next"'.format(
                base_url, query.next_num, per_page
            )
        )

    links = ",".join(links)
    return dict(Link=links)
