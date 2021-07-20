from schemas.schema_combined import JournalListSchema


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


def process_only_fields(attrs):
    """
    Some fields in attrs must be renamed and added in order to make filtering work.
    Example:  If a schema field is called open_access_recent but the data_key is open_access,
    then we need to refer to the field name in order to filter results.
    """
    only = attrs.split(",")

    if "subscription_pricing" in only:
        only.remove("subscription_pricing")
        only = only + ["subscription_prices", "mini_bundles", "sub_data_source"]

    if "apc_pricing" in only:
        only.remove("apc_pricing")
        only = only + ["apc_prices", "apc_data_source"]

    if "open_access" in only:
        only.remove("open_access")
        only = only + ["open_access_recent"]

    if "currently_known_as" in only:
        only.remove("currently_known_as")
        only = only + ["current_journal"]

    if "formerly_known_as" in only:
        only.remove("formerly_known_as")
        only = only + ["journals_renamed"]

    # remove any invalid fields
    schema_fields = [j for j in JournalListSchema._declared_fields]
    for field in only:
        if field not in schema_fields:
            only.remove(field)

    return only
