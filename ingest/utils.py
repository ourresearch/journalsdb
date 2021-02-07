import unicodedata

from models.journal import Journal


def find_journal(issn):
    """
    Find journal by ISSN.
    """
    return Journal.find_by_issn(issn)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def remove_control_characters(s):
    """
    Remove control characters such as SOS and ST from a string.
    Exists in many issn.org journal title.
    """
    if s:
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
