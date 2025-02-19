import json
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from hawc.apps.common.forms import ASSESSMENT_UNIQUE_MESSAGE
from hawc.apps.lit import constants, models

DATA_ROOT = Path(__file__).parents[3] / "data/api"


@pytest.mark.django_db
class TestLiteratureAssessmentViewset:
    def _test_flat_export(self, rewrite_data_files: bool, fn: str, url: str):

        client = APIClient()
        assert client.login(username="reviewer@hawcproject.org", password="pw") is True
        resp = client.get(url)
        assert resp.status_code == 200

        path = Path(DATA_ROOT / fn)
        data = resp.json()

        if rewrite_data_files:
            path.write_text(json.dumps(data, indent=2, sort_keys=True))

        assert data == json.loads(path.read_text())

    def test_permissions(self, db_keys):
        rev_client = APIClient()
        assert rev_client.login(username="reviewer@hawcproject.org", password="pw") is True
        anon_client = APIClient()
        pm_client = APIClient()
        assert pm_client.login(username="pm@hawcproject.org", password="pw") is True

        urls = [
            reverse("lit:api:assessment-tags", args=(db_keys.assessment_working,)),
            reverse("lit:api:assessment-reference-ids", args=(db_keys.assessment_working,)),
            reverse("lit:api:assessment-reference-tags", args=(db_keys.assessment_working,)),
            reverse(
                "lit:api:assessment-reference-year-histogram", args=(db_keys.assessment_working,)
            ),
            reverse("lit:api:assessment-references-download", args=(db_keys.assessment_working,)),
            reverse("lit:api:assessment-tag-heatmap", args=(db_keys.assessment_working,)),
        ]
        for url in urls:
            assert anon_client.get(url).status_code == 403
            assert rev_client.get(url).status_code == 200

        # topic model permissions
        url = reverse("lit:api:assessment-topic-model", args=(db_keys.assessment_working,))
        assert anon_client.get(url).status_code == 403
        assert rev_client.get(url).status_code == 200

        tagtree_url = reverse("lit:api:assessment-tagtree", args=(db_keys.assessment_working,))
        # only reviewers and up can GET
        assert anon_client.get(tagtree_url).status_code == 403
        assert rev_client.get(tagtree_url).status_code == 200

        # only admins and up can POST
        assert anon_client.post(tagtree_url).status_code == 403
        assert rev_client.post(tagtree_url).status_code == 403
        assert pm_client.post(tagtree_url, None).status_code != 403

    def test_references_download(self, rewrite_data_files: bool, db_keys):
        url = reverse("lit:api:assessment-references-download", args=(db_keys.assessment_final,))
        fn = "api-lit-assessment-references-export.json"
        self._test_flat_export(rewrite_data_files, fn, url)

    def test_tags(self, db_keys):
        url = reverse("lit:api:assessment-tags", kwargs=dict(pk=db_keys.assessment_working))
        c = APIClient()
        assert c.login(email="pm@hawcproject.org", password="pw") is True
        resp = c.get(url).json()
        assert len(resp) == 11
        assert resp[0] == {"id": 2, "depth": 2, "name": "Inclusion", "nested_name": "Inclusion"}
        assert resp[-1] == {
            "id": 21,
            "depth": 4,
            "name": "c",
            "nested_name": "Exclusion|Tier III|c",
        }

    def test_tagtree(self, db_keys):
        url = reverse("lit:api:assessment-tagtree", kwargs=dict(pk=db_keys.assessment_working))
        c = APIClient()

        # test some updates
        bad_payload_no_name = {
            "tree": [{"data": {"name": "x"}}, {"data": {"name": "y"}, "children": [{"data": {}}]}]
        }
        bad_payload_bad_slug = {"tree": [{"data": {"name": "x", "slug": "this has spaces"}}]}

        good_payload = {
            "tree": [
                {"data": {"name": "This is required"}},
                {"data": {"name": "Tag Name", "slug": "custom-slug"}},
                {
                    "data": {"name": "Grandparent Tag"},
                    "children": [
                        {"data": {"name": "nested"}},
                        {
                            "data": {"name": "Parent Tag"},
                            "children": [{"data": {"name": "deeply nested"}}],
                        },
                    ],
                },
            ]
        }

        # permissions - GET/POST
        assert c.login(email="reviewer@hawcproject.org", password="pw") is True
        response = c.get(url)
        assert response.status_code == 200
        response = c.post(url, good_payload, format="json")
        assert response.status_code == 403

        # test some basic fetching
        assert c.login(email="pm@hawcproject.org", password="pw") is True
        resp = c.get(url).json()["tree"]
        assert len(resp) == 2
        assert len(resp[0]["children"]) == 3
        assert resp[1]["data"]["name"] == "Exclusion"
        assert resp[0]["children"][2]["data"]["slug"] == "mechanistic-study"

        # bad input - no data supplied
        response = c.post(url, None, format="json")
        assert response.status_code == 400
        assert response.json() == {"tree": ["This field is required."]}

        # bad input - it's JSON but not a list as we expect
        response = c.post(url, {}, format="json")
        assert response.status_code == 400
        assert response.json() == {"tree": ["This field is required."]}

        # bad input - what if the "name" attribute is missing from a node
        response = c.post(url, bad_payload_no_name, format="json")
        error = response.json()
        assert response.status_code == 400
        assert "'name' is a required property" in error["tree"][0]

        # bad input - a slug is supplied but it's not valid
        response = c.post(url, bad_payload_bad_slug, format="json")
        error = response.json()
        assert response.status_code == 400
        assert "does not match" in error["tree"][0]

        # good payload
        response = c.post(url, good_payload, format="json")
        assert response.status_code == 200
        data = response.json()["tree"]
        assert data[0]["id"] > 0
        assert data[0]["data"]["name"] == "This is required"
        assert data[0]["data"]["slug"] == "this-is-required"
        assert data[1]["data"]["name"] == "Tag Name"
        assert data[1]["data"]["slug"] == "custom-slug"
        assert data[2]["children"][0]["data"]["name"] == "nested"

    def test_reference_ids(self, db_keys):
        url = reverse("lit:api:assessment-reference-ids", kwargs=dict(pk=db_keys.assessment_final))
        c = APIClient()
        assert c.login(email="pm@hawcproject.org", password="pw") is True
        resp = c.get(url).json()
        assert resp == [
            {
                "reference_id": 5,
                "pubmed_id": 11778423,
                "doi_id": "10.1093/milmed/166.suppl_2.23",
                "hero_id": None,
            },
            {"reference_id": 6, "pubmed_id": 15907334, "doi_id": None, "hero_id": None},
            {"reference_id": 7, "pubmed_id": 21284075, "doi_id": None, "hero_id": None},
            {"reference_id": 8, "pubmed_id": 24004895, "doi_id": None, "hero_id": None},
        ]

    def test_reference_search(self, db_keys):
        url = reverse("lit:api:assessment-reference-search", args=(db_keys.assessment_working,))
        client = APIClient()
        assert client.login(username="team@hawcproject.org", password="pw") is True

        # unaccented query returns accented result
        data = {"authors": "fred"}
        response = client.post(url, data)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert "Frédéric" in response.json()["references"][0]["authors_short"]

        # invalid reference tag
        data = {"year": 2001, "tags": [12]}
        response = client.post(url, data)
        assert response.status_code == 400
        assert response.json() == {"tags": ["Invalid tag IDs"]}

        # valid reference tag
        url = reverse("lit:api:assessment-reference-search", args=(db_keys.assessment_final,))
        response = client.post(url, data)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()["references"][0]["pk"] == 5

    def test_reference_tags(self, db_keys):
        url = reverse("lit:api:assessment-reference-tags", kwargs=dict(pk=db_keys.assessment_final))
        c = APIClient()
        assert c.login(email="pm@hawcproject.org", password="pw") is True
        resp = c.get(url).json()
        assert resp == [
            {"reference_id": 5, "tag_id": 12},
            {"reference_id": 6, "tag_id": 13},
            {"reference_id": 7, "tag_id": 13},
            {"reference_id": 8, "tag_id": 12},
        ]

    def test_reference_year_histogram(self, db_keys):
        url = reverse(
            "lit:api:assessment-reference-year-histogram",
            kwargs=dict(pk=db_keys.assessment_working),
        )
        c = APIClient()
        assert c.login(email="pm@hawcproject.org", password="pw") is True
        resp = c.get(url).json()
        assert resp["data"][0]["type"] == "histogram"

    def test_tag_heatmap(self, rewrite_data_files: bool, db_keys):
        url = reverse("lit:api:assessment-tag-heatmap", args=(db_keys.assessment_final,))
        fn = "api-lit-assessment-tag-heatmap.json"
        self._test_flat_export(rewrite_data_files, fn, url)

    def test_excel_to_json(self, db_keys):
        url = reverse("lit:api:assessment-excel-to-json", args=(db_keys.assessment_working,))
        data = [{"reference_id": 1, "tag_id": 1}, {"reference_id": 1, "tag_id": 2}]
        df = pd.DataFrame(data)
        excel = BytesIO()
        df.to_excel(excel, index=False)
        excel.seek(0)
        csv = BytesIO(df.to_csv(index=False).encode())
        csv.seek(0)
        c = APIClient()

        # permission error
        disposition = "attachment; filename=test.xlsx"
        resp = c.post(url, {"file": csv}, HTTP_CONTENT_DISPOSITION=disposition)
        assert resp.status_code == 403

        assert c.login(email="pm@hawcproject.org", password="pw") is True

        # valid; assert parses successfully
        disposition = "attachment; filename=test.xlsx"
        resp = c.post(url, {"file": excel}, HTTP_CONTENT_DISPOSITION=disposition)
        assert resp.status_code == 200 and resp.json() == data

        # invalid; JSON with no file
        resp = c.post(url, {"test": 123}, format="json")
        assert resp.status_code == 400 and resp.json() == {
            "detail": "Missing filename. Request should include a Content-Disposition header with a filename parameter."
        }

        # invalid; Content-Disposition header is required
        resp = c.post(url, {"file": excel})
        assert resp.status_code == 400 and resp.json() == {
            "detail": "Missing filename. Request should include a Content-Disposition header with a filename parameter."
        }

        # invalid; non excel files return an error
        resp = c.post(url, {"file": csv}, HTTP_CONTENT_DISPOSITION="attachment; filename=test.csv")
        assert resp.status_code == 400 and resp.json() == {"file": "File extension must be .xlsx"}

        # invalid; cannot parse excel file
        resp = c.post(url, {"file": BytesIO()}, HTTP_CONTENT_DISPOSITION=disposition)
        assert resp.status_code == 400 and resp.json() == {"file": "Unable to parse excel file"}
        resp = c.post(url, {"file": csv}, HTTP_CONTENT_DISPOSITION=disposition)
        assert resp.status_code == 400 and resp.json() == {"file": "Unable to parse excel file"}


@pytest.mark.django_db
class TestReferenceFilterTagViewset:
    def test_references(self):
        url = reverse("lit:api:tags-references", args=(12,))
        c = APIClient()
        assert c.login(email="pm@hawcproject.org", password="pw") is True

        # base report; reference metadata plus columns for each tag
        resp = c.get(url).json()
        assert len(resp) == 2
        assert len(resp[0]) > 20
        assert resp[0]["Inclusion"] is True

        # table builder format
        resp = c.get(url, {"exporter": "table-builder"}).json()
        assert len(resp) == 2
        assert len(resp[0]) == 5
        assert resp[0]["Name"] == "Kawana N, Ishimatsu S, and Kanda K 2001"

        # invalid exporter format
        resp = c.get(url, {"exporter": "not-a-format"})
        assert resp.status_code == 400
        assert resp.json() == {"exporter": ['"not-a-format" is not a valid choice.']}


@pytest.mark.vcr
@pytest.mark.django_db
class TestSearchViewset:
    def test_success(self, db_keys):
        url = reverse("lit:api:search-list")
        c = APIClient()
        assert c.login(email="team@hawcproject.org", password="pw") is True

        payload = {
            "assessment": db_keys.assessment_working,
            "search_type": "i",
            "source": 2,
            "title": "demo title",
            "description": "",
            "search_string": "5490558",
        }
        resp = c.post(url, payload, format="json")
        assert resp.status_code == 201

    def test_validation_failures(self, db_keys):
        url = reverse("lit:api:search-list")
        c = APIClient()
        assert c.login(email="team@hawcproject.org", password="pw") is True

        # check that the "GET" method is disabled
        assert c.get(url).status_code == 405

        payload = {
            "assessment": db_keys.assessment_working,
            "search_type": "i",
            "source": 2,
            "title": "demo title",
            "description": "",
            "search_string": "5490558",
        }

        # check invalid assessment permission
        new_payload = {**payload, **{"assessment": db_keys.assessment_final}}
        resp = c.post(url, new_payload, format="json")
        assert resp.status_code == 403
        assert resp.data == {"detail": "Invalid permissions to edit assessment"}

        # title already exists for this assessment
        new_payload = {**payload, **{"title": "Manual import"}}
        resp = c.post(url, new_payload, format="json")
        assert resp.status_code == 400
        assert resp.data == {
            "non_field_errors": ["The fields assessment, title must make a unique set."]
        }

        # slug already exists for this assessment
        new_payload = {**payload, **{"title": "MANUAL IMPORT"}}
        resp = c.post(url, new_payload, format="json")
        assert resp.status_code == 400
        assert resp.data == {"slug": [ASSESSMENT_UNIQUE_MESSAGE]}

        # check type
        new_payload = {**payload, **{"search_type": "s"}}
        resp = c.post(url, new_payload, format="json")
        assert resp.status_code == 400
        assert resp.data == {"non_field_errors": ["API currently only supports imports"]}

        # check database
        new_payload = {**payload, **{"source": 1}}
        resp = c.post(url, new_payload, format="json")
        assert resp.status_code == 400
        assert resp.data == {"non_field_errors": ["API currently only supports HERO imports"]}

        # check bad csv
        bad_search_strings = [
            "",
            "just a long string of text",
            "not-numeric,but a csv",
            "1a,2b",
            "1,,2",
            "1,2, ,3",
        ]
        for bad_search_string in bad_search_strings:
            new_payload = {**payload, **{"search_string": bad_search_string}}
            resp = c.post(url, new_payload, format="json")
            assert resp.status_code == 400
            assert resp.data == {
                "non_field_errors": [
                    "Must be a comma-separated list of positive integer identifiers"
                ]
            }

        # check bad id lists
        bad_search_strings = ["-1", "123,123"]
        for bad_search_string in bad_search_strings:
            new_payload = {**payload, **{"search_string": bad_search_string}}
            resp = c.post(url, new_payload, format="json")
            assert resp.status_code == 400
            assert resp.data == {
                "non_field_errors": [
                    "At least one positive identifer must exist and must be unique"
                ]
            }

    def test_missing_id_in_hero(self, db_keys):
        """
        This should fail b/c the ID is redirected in HERO (search for HERO ID 41589):
        - https://hero.epa.gov/hero/index.cfm/search
        - https://hero.epa.gov/hero/index.cfm/reference/details/reference_id/5490558

        This is an empty return:
        - https://hero.epa.gov/hero/ws/index.cfm/api/1.0/search/criteria/41589/recordsperpage/100
        """
        url = reverse("lit:api:search-list")
        c = APIClient()
        assert c.login(email="team@hawcproject.org", password="pw") is True

        # check that the "GET" method is disabled
        assert c.get(url).status_code == 405

        # check success!
        payload = {
            "assessment": db_keys.assessment_working,
            "search_type": "i",
            "source": 2,
            "title": "demo title 1",
            "description": "",
            "search_string": "41589",
        }
        resp = c.post(url, payload, format="json")
        assert resp.status_code == 400
        assert resp.data == {
            "non_field_errors": [
                "Import failed; the following HERO IDs could not be imported: 41589"
            ]
        }


@pytest.mark.vcr
@pytest.mark.django_db
class TestHEROApis:
    @pytest.fixture(scope="function", autouse=True)
    def clear_cache(cls):
        # Reset burst throttling
        cache.clear()

    def test_replace_permissions(self, db_keys):

        assessment_id = models.Reference.objects.get(id=db_keys.reference_linked).assessment_id

        url = reverse("lit:api:assessment-replace-hero", args=(assessment_id,))
        data = {"replace": [[db_keys.reference_linked, 1]]}

        # reviewers shouldn't be able to update
        client = APIClient()
        assert client.login(username="reviewer@hawcproject.org", password="pw") is True
        response = client.post(url, data, format="json")
        assert response.status_code == 403

        # public shouldn't be able to update
        client = APIClient()
        response = client.post(url, data, format="json")
        assert response.status_code == 403

    def test_valid_replace_requests(self, db_keys):
        assessment_id = models.Reference.objects.get(id=db_keys.reference_linked).assessment_id

        url = reverse("lit:api:assessment-replace-hero", args=(assessment_id,))
        data = {"replace": [[db_keys.reference_linked, 1]]}

        client = APIClient()
        assert client.login(username="pm@hawcproject.org", password="pw") is True
        response = client.post(url, data, format="json")
        assert response.status_code == 204

        updated_reference = models.Reference.objects.get(id=db_keys.reference_linked)
        assert (
            updated_reference.title
            == "Asbestos-related diseases of the lungs and pleura: Current clinical issues"
        )
        assert updated_reference.identifiers.get(
            database=constants.ReferenceDatabase.HERO
        ).unique_id == str(1)

    def test_bad_replace_requests(self, db_keys):

        # test nonexistent assessment
        url = reverse("lit:api:assessment-replace-hero", args=(100,))
        data = {"replace": [[db_keys.reference_linked, 1]]}

        client = APIClient()
        assert client.login(username="pm@hawcproject.org", password="pw") is True
        response = client.post(url, data, format="json")
        assert response.status_code == 404

    def test_update_permissions(self, db_keys):

        assessment_id = models.Reference.objects.get(id=db_keys.reference_linked).assessment_id

        url = reverse(
            "lit:api:assessment-update-reference-metadata-from-hero", args=(assessment_id,)
        )

        # reviewers shouldn't be able to destroy
        client = APIClient()
        assert client.login(username="reviewer@hawcproject.org", password="pw") is True
        response = client.post(url)
        assert response.status_code == 403

        # public shouldn't be able to update
        client = APIClient()
        response = client.post(url)
        assert response.status_code == 403

    def test_valid_update_requests(self, db_keys):
        assessment_id = models.Reference.objects.get(id=db_keys.reference_linked).assessment_id

        url = reverse(
            "lit:api:assessment-update-reference-metadata-from-hero", args=(assessment_id,)
        )

        client = APIClient()
        assert client.login(username="pm@hawcproject.org", password="pw") is True
        response = client.post(url)
        assert response.status_code == 204

        updated_reference = models.Reference.objects.get(id=db_keys.reference_linked)
        assert updated_reference.title == "Early lung events following low-dose asbestos exposure"

    def test_bad_update_requests(self, db_keys):
        # test nonexistent assessment
        url = reverse("lit:api:assessment-replace-hero", args=(100,))

        client = APIClient()
        assert client.login(username="pm@hawcproject.org", password="pw") is True
        response = client.post(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestReferenceDestroyApi:
    def test_permissions(self, db_keys):

        url = reverse("lit:api:reference-detail", args=(db_keys.reference_linked,))

        # reviewers shouldn't be able to destroy
        client = APIClient()
        assert client.login(username="reviewer@hawcproject.org", password="pw") is True
        response = client.delete(url)
        assert response.status_code == 403

        # public shouldn't be able to destroy
        client = APIClient()
        response = client.delete(url)
        assert response.status_code == 403

        # make sure the object still exists
        assert models.Reference.objects.filter(id=db_keys.reference_linked).exists()

    def test_bad_requests(self, db_keys):
        # test bad id
        url = reverse("lit:api:reference-detail", args=(-1,))

        client = APIClient()
        assert client.login(username="team@hawcproject.org", password="pw") is True
        response = client.delete(url)
        assert response.status_code == 404

    def test_valid_requests(self, db_keys):
        # test valid id
        url = reverse("lit:api:reference-detail", args=(db_keys.reference_linked,))

        client = APIClient()
        assert client.login(username="team@hawcproject.org", password="pw") is True
        response = client.delete(url)
        # the reference is successfully deleted
        assert response.status_code == 204
        response = client.delete(url)
        # the object does not exist, since it was previously deleted
        assert response.status_code == 404
        assert not models.Reference.objects.filter(id=db_keys.reference_linked).exists()


@pytest.mark.django_db
class TestReferenceUpdateApi:
    def test_permissions(self, db_keys):

        url = reverse("lit:api:reference-detail", args=(db_keys.reference_linked,))
        data = {"title": "TestReferenceUpdateApi test"}

        pre_ref = models.Reference.objects.get(id=db_keys.reference_linked)

        # reviewers shouldn't be able to update
        client = APIClient()
        assert client.login(username="reviewer@hawcproject.org", password="pw") is True

        response = client.patch(url, data)
        assert response.status_code == 403

        # public shouldn't be able to update
        client = APIClient()
        response = client.patch(url, data)
        assert response.status_code == 403

        post_ref = models.Reference.objects.get(id=db_keys.reference_linked)

        # make sure the object hasn't changed
        assert post_ref == pre_ref

    def test_bad_requests(self, db_keys):
        # test bad id
        url = reverse("lit:api:reference-detail", args=(-1,))
        data = {"title": "TestReferenceUpdateApi test"}

        client = APIClient()
        assert client.login(username="team@hawcproject.org", password="pw") is True
        response = client.patch(url, data)
        assert response.status_code == 404

        # test bad tag
        url = reverse("lit:api:reference-detail", args=(db_keys.reference_linked,))
        tags = [2, 3, -1]
        data = {"tags": tags}
        response = client.patch(url, data)
        assert response.status_code == 400
        assert response.json() == {"tags": ["All tag ids are not from this assessment"]}

    def test_valid_requests(self, db_keys):
        url = reverse("lit:api:reference-detail", args=(db_keys.reference_linked,))
        client = APIClient()
        assert client.login(username="team@hawcproject.org", password="pw") is True

        reference = models.Reference.objects.get(id=db_keys.reference_linked)

        # test updating reference with a new title
        data = {"title": "TestReferenceUpdateApi title test"}
        response = client.patch(url, data)
        assert response.status_code == 200

        assert reference.title != data.get("title")
        updated_reference = models.Reference.objects.get(id=db_keys.reference_linked)
        assert updated_reference.title == data.get("title")

        # test updating reference with new tags
        tags = [2, 3]
        data = {"tags": tags}
        response = client.patch(url, data)
        assert response.status_code == 200

        updated_reference = models.Reference.objects.get(id=db_keys.reference_linked)
        assert updated_reference.tags.count() == len(tags)
        for id in tags:
            assert updated_reference.tags.filter(id=id).exists()

        # test updating reference with multiple fields
        tags = [2, 3, 4]
        data = {"title": "TestReferenceUpdateApi title test 2", "tags": tags}
        response = client.patch(url, data)
        assert response.status_code == 200

        updated_reference = models.Reference.objects.get(id=db_keys.reference_linked)
        assert updated_reference.title == data.get("title")
        assert updated_reference.tags.count() == len(tags)
        for id in tags:
            assert updated_reference.tags.filter(id=id).exists()
