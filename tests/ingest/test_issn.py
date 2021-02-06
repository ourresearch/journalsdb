from sqlalchemy import desc

from models.issn import ISSNHistory, ISSNMetaData, ISSNToISSNL, LinkedISSNL


class TestISSNImport:
    def test_issn_to_issnl_import(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # 5 records imported
        assert ISSNToISSNL.query.count() == 5

        # check for issn_pair
        issn_pair = ISSNToISSNL.query.filter_by(issn="0000-0051").first()
        assert issn_pair.issn_l == "0000-0019"

    def test_issn_import_no_changes(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # 5 records imported
        assert ISSNToISSNL.query.count() == 5

        # run command again
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # number of records is the same
        assert ISSNToISSNL.query.count() == 5

    def test_issn_new_record_added(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # run day two with added record
        run_import_issns("ISSN-to-ISSN-L-new-record.txt")

        assert ISSNToISSNL.query.count() == 6

        # sort by created_at to see new is added
        issn = ISSNToISSNL.query.order_by(desc(ISSNToISSNL.created_at)).first()
        assert issn.issn_l == "0000-0213"

        # record added to history
        h = ISSNHistory.query.filter_by(
            issn_l="0000-0213", issn="0000-0213"
        ).one_or_none()
        assert h is not None
        assert h.status == "added"

    def test_issn_new_record_added_no_duplicate(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # run day two with added record
        run_import_issns("ISSN-to-ISSN-L-new-record.txt")

        # run day three with same dataset
        run_import_issns("ISSN-to-ISSN-L-new-record.txt")

        # record added to history
        h = ISSNHistory.query.filter_by(issn_l="0000-0213", issn="0000-0213").all()
        assert len(h) == 1

    def test_issn_record_removed(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # run day two with (0000-006X, 0000-006X) removed
        run_import_issns("ISSN-to-ISSN-L-removed.txt")

        # record is still there, plan to remove manually
        assert ISSNToISSNL.query.count() == 5

        # record added to history
        h = ISSNHistory.query.filter_by(
            issn_l="0000-006X", issn="0000-006X", status="removed"
        ).one_or_none()
        assert h is not None

    def test_issn_record_removed_no_duplicate(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # run day two with (0000-006X, 0000-006X) removed
        run_import_issns("ISSN-to-ISSN-L-removed.txt")

        # run day three with same dataset
        run_import_issns("ISSN-to-ISSN-L-removed.txt")

        # record in history one time
        h = ISSNHistory.query.filter_by(
            issn_l="0000-006X", issn="0000-006X", status="removed"
        ).all()
        assert len(h) == 1

    def test_issn_mappings(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # test import count after group by
        assert ISSNMetaData.query.count() == 4

        # test single mapping
        issn_l = ISSNMetaData.query.filter_by(issn_l="0000-0043").one()
        assert issn_l.issn_org_issns == ["0000-0043"]

        # test mapping with two issns
        issn_l = ISSNMetaData.query.filter_by(issn_l="0000-0019").one()
        assert issn_l.issn_org_issns == ["0000-0051", "0000-0019"]

        # test created_at
        assert issn_l.created_at is not None

    def test_issn_mapping_change(self, client, run_import_issns):
        run_import_issns("ISSN-to-ISSN-L-initial.txt")

        # run file with changed issns
        run_import_issns("ISSN-to-ISSN-L-changed.txt")

        # test that issn_l has the new data
        issn_l = ISSNMetaData.query.filter_by(issn_l="0000-006X").one()
        assert issn_l.issn_org_issns == ["0000-006X", "0000-0507"]


class TestAPIImport:
    def test_api_import(self, client, run_import_issns_with_api):
        run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")

        issn_l = ISSNMetaData.query.filter_by(issn_l="0000-0043").one()
        assert issn_l.issn_org_raw_api is not None

        # find title that is only in the 'name' field
        assert issn_l.title_from_issn_api == "Irregular serials & annuals."

        issn_l = ISSNMetaData.query.filter_by(issn_l="0000-0027").one()

        # find title that is only in the 'mainTitle' field
        assert issn_l.title_from_issn_api == "Library journal."

        # check crossref title and publisher
        issn_l = ISSNMetaData.query.filter_by(issn_l="2291-5222").one()
        assert issn_l.crossref_raw_api["message"]["title"] == "JMIR mhealth and uhealth"
        assert (
            issn_l.crossref_raw_api["message"]["publisher"] == "JMIR Publications Inc."
        )
        assert issn_l.issns_from_crossref_api == ["2291-5222"]

    def test_linked_issnl(self, client, run_import_issns_with_api):
        """
        When an issn-l is in a separate record's crossref_issns,
        then those records should be linked in the linked_issn_l table.
        """
        run_import_issns_with_api("ISSN-to-ISSN-L-linked.txt")

        # linked
        l = LinkedISSNL.query.filter_by(
            issn_l_primary="0974-4061", issn_l_secondary="0974-4053"
        ).one_or_none()
        assert l is not None

        l = LinkedISSNL.query.filter_by(
            issn_l_primary="2582-2810", issn_l_secondary="2454-3993"
        ).one_or_none()
        assert l is not None

        # not linked
        l = LinkedISSNL.query.filter_by(issn_l_primary="0000-0043").one_or_none()
        assert l is None
