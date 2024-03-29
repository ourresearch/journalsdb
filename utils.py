from urllib.parse import unquote

from exceptions import APIPaginationError
from models.journal import Publisher, JournalStatus
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

    # remove any invalid fields
    schema_fields = [j for j in JournalListSchema._declared_fields]
    for field in only:
        if field not in schema_fields:
            only.remove(field)

    return only


def get_publisher_ids(publisher_names):
    publisher_names = publisher_names.split(",")
    publisher_ids = []
    for name in publisher_names:
        name = unquote(name)  # convert special characters back to string
        publisher = Publisher.query.filter(Publisher.name.ilike(name)).first()
        if publisher:
            publisher_ids.append(publisher.id)

    return publisher_ids


def validate_per_page(per_page):
    if per_page and per_page > 100 or per_page < 1:
        raise APIPaginationError("per-page parameter must be between 1 and 100")

    return per_page


def validate_status(status):
    valid_status_values = [j.value for j in JournalStatus]
    if status and status in valid_status_values:
        return status
