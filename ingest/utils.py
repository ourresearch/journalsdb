from models.journal import Journal


def find_journal(issn):
    """
    Find journal by issn_l field first, then look through mapped issns
    """
    return Journal.query.filter_by(issn_l=issn).one_or_none() or Journal.find_by_issn(issn)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance
