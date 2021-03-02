import pytest

from hawc.apps.assessment.models import Assessment
from hawc.apps.study.models import Study


def check_copy_lit_data(study, assessment):
    assert study.assessment == assessment
    assert study.reference_ptr.assessment == assessment
    for search in study.reference_ptr.searches.all():
        assert search.assessment == assessment


def check_copy_bioassay_data(study, assessment):
    # experiment
    assert study.experiments.count() > 0
    for exp in study.experiments.all():
        assert exp.study_id == study.id

        # animal group
        assert exp.animal_groups.count() > 0
        for ag in exp.animal_groups.all():
            assert ag.experiment_id == exp.id

            # sibling relations
            if ag.siblings_id:
                assert ag.siblings.experiment_id == exp.id

            # parents
            for parent in ag.parents.all():
                assert parent.experiment_id == exp.id

            # dosing regimes
            assert ag.dosing_regime is not None
            assert ag.dosing_regime.dosed_animals == ag
            assert ag.dosing_regime.dose_groups.count() > 0

            # endpoints
            assert ag.endpoints.count() > 0
            for ep in ag.endpoints.all():
                assert ep.assessment == assessment
                assert ep.animal_group == ag
                assert ep.baseendpoint_ptr.assessment == assessment
                assert ep.groups.count() > 0


def check_copy_epi_data(study, assessment):
    pass


class TestStudyModel:
    @pytest.mark.django_db
    def test_copy_across_assessment_bioassay(self):
        studies = list(Study.objects.filter(id__in=[7]))
        src_assessment = Assessment.objects.get(id=2)
        dst_assessment = Assessment.objects.get(id=3)

        cw = Study.copy_across_assessment(studies, dst_assessment)

        src_study = Study.objects.get(id=7)
        dst_study = Study.objects.get(id=cw["studies"][src_study.id])
        check_copy_lit_data(src_study, src_assessment)
        check_copy_lit_data(dst_study, dst_assessment)

        check_copy_bioassay_data(src_study, src_assessment)
        check_copy_bioassay_data(dst_study, dst_assessment)

    @pytest.mark.django_db
    def test_copy_across_assessment_epi(self):
        studies = list(Study.objects.filter(id__in=[5]))

        src_assessment = Assessment.objects.get(id=2)
        dst_assessment = Assessment.objects.get(id=3)
        cw = Study.copy_across_assessment(studies, dst_assessment)

        src_study = Study.objects.get(id=5)
        dst_study = Study.objects.get(id=cw["studies"][src_study.id])

        check_copy_lit_data(src_study, src_assessment)
        check_copy_lit_data(dst_study, dst_assessment)

        check_copy_epi_data(src_study, src_assessment)
        check_copy_epi_data(dst_study, dst_assessment)
