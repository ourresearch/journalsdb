from sqlalchemy.dialects.postgresql import JSONB

from app import db
from models.mixins import TimestampMixin


class AuthorPermissions(db.Model, TimestampMixin):
    __tablename__ = "author_permissions"

    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(
        db.Integer, db.ForeignKey("journals.id", ondelete="CASCADE"), unique=True
    )
    has_policy = db.Column(db.Boolean)
    version_archivable = db.Column(JSONB)
    archiving_locations_allowed = db.Column(JSONB)
    post_print_embargo = db.Column(db.Integer)
    licence_allowed = db.Column(JSONB)
    deposit_statement_required = db.Column(db.Text)

    def to_dict(self):
        dict_ = {}
        for key in self.__mapper__.c.keys():
            dict_[key] = getattr(self, key)

        fields_to_remove = ["id", "journal_id", "created_at", "updated_at"]
        for field in fields_to_remove:
            dict_.pop(field)

        dict_["provenance"] = "https://shareyourpaper.org/permissions/about#data"

        return dict_

    # post_publication = db.Column(db.Boolean)
    # provenance = db.Column(db.Text)
    # year = db.Column(db.Integer, index=True)

    # ['has_policy', 'version_archivable', 'archiving_locations_allowed', 'post_print_embargo', 'licence_allowed',
    #  'deposit_statement_required', 'post_publication_pre_print_update_allowed', 'permissions_request_contact_email',
    #  'can_authors_opt_out', 'enforcement_date', 'policy_full_text', 'record_last_updated', 'contributed_by', 'added_by',
    #  'reviewer', 'public_notes', 'notes', 'permission_type', 'subject_coverage', 'monitoring_type',
    #  'policy_landing_page', 'archived_full_text_link', 'author_affiliation_requirement', 'funding_proportion_required',
    #  'parent_policy', 'record_first_added', 'if_funded_by', 'author_affiliation_department_requirement']
