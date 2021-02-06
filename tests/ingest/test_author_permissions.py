import pandas as pd

from ingest.author_permissions import import_author_permissions
from models.author_permissions import AuthorPermissions
from models.journal import Journal
from views import app


test_data = {
    "id": ["1876-2859"],
    "Has Policy?": ["Yes"],
    "Version(s) archivable": ["Postprint, Preprint"],
    "Archiving Locations Allowed": ["Institutional Repository"],
    "Post-Print Embargo": [12],
    "Licence(s) Allowed": ["CC-BY-NC-ND"],
    "Deposit Statement Required": [
        "© This manuscript version is made available under the CC-BY-NC-ND 4.0 license https://creativecommons.org/licenses/by-nc-nd/4.0/"
    ],
    "Post-publication Pre-print Update Allowed": ["Yes"],
    "Permissions Request Contact Email": [""],
    "Can Authors Opt Out": [""],
    "Enforcement Date": [""],
    "Policy Full Text": [
        "https://www.elsevier.com/__data/promis_misc/external-embargo-list.pdf, https://www.elsevier.com/about/policies/sharing"
    ],
    "Record Last Updated": ["01/01/2019, 12/07/2017"],
    "Contributed By": ["joe@openaccessbutton.org, libraryrepository@pobox.upenn.edu"],
    "Added by": ["joe@openaccessbutton.org, libraryrepository@pobox.upenn.edu"],
    "Reviewer(s)": [""],
    "Public Notes": [""],
    "Notes": [""],
    "Permission type": ["Journal"],
    "Subject Coverage": [""],
    "Monitoring Type": ["Automatic"],
    "Policy Landing Page": [""],
    "Archived Full Text Link": [
        "https://web.archive.org/web/20200106202134/https://www.elsevier.com/__data/promis_misc/external-embargo-list.pdf"
    ],
    "Author Affiliation Requirement": [""],
    "Funding Proportion Required": [""],
    "Parent Policy": ["Elsevier BV, Elsevier"],
    "Record First Added": ["01/01/2019, 12/07/2017"],
    "If funded by": [""],
    "Author Affiliation Department Requirement": [""],
}


def test_import_author_permission(client, run_import_issns_with_api, mocker):
    mocker.patch(
        "ingest.author_permissions.pd.read_csv",
        return_value=pd.DataFrame(data=test_data),
    )
    run_import_issns_with_api("ISSN-to-ISSN-L-api.txt")

    # run command
    runner = app.test_cli_runner()
    runner.invoke(import_author_permissions)

    j = Journal.query.filter_by(issn_l="1876-2859").one()
    a = AuthorPermissions.query.filter_by(journal_id=j.id).one()

    assert a.has_policy is True
    assert a.version_archivable == "Postprint, Preprint"
