import json

from django import forms
from django.db.models import Q
from django.forms.models import BaseModelFormSet, inlineformset_factory, modelformset_factory
from django.forms.widgets import Select
from django.urls import reverse

from ..assessment.lookups import DssToxIdLookup, EffectTagLookup
from ..assessment.models import DoseUnits
from ..common import selectable
from ..common.forms import BaseFormHelper, form_actions_apply_filters
from ..study.lookups import InvitroStudyLookup
from . import lookups, models


class IVChemicalForm(forms.ModelForm):
    HELP_TEXT_CREATE = "Describes the chemical used in the current experiment."
    HELP_TEXT_UPDATE = "Update an existing chemical."

    source = forms.CharField(
        label="Source of chemical",
        widget=selectable.AutoCompleteWidget(lookups.IVChemicalSourceLookup, allow_new=True),
    )

    class Meta:
        model = models.IVChemical
        exclude = ("study",)

    def __init__(self, *args, **kwargs):
        study = kwargs.pop("parent", None)
        super().__init__(*args, **kwargs)
        if study:
            self.instance.study = study

        self.fields["source"].widget.update_query_parameters(
            {"related": self.instance.study.assessment.id}
        )

        self.fields["dtxsid"].widget = selectable.AutoCompleteSelectWidget(
            lookup_class=DssToxIdLookup
        )

    @property
    def helper(self):
        for fld in list(self.fields.keys()):
            widget = self.fields[fld].widget
            if type(widget) == forms.Textarea:
                widget.attrs["rows"] = 3

        if self.instance.id:
            inputs = {
                "legend_text": f"Update {self.instance}",
                "help_text": self.HELP_TEXT_UPDATE,
                "cancel_url": self.instance.get_absolute_url(),
            }
        else:
            inputs = {
                "legend_text": "Create new experimental chemical",
                "help_text": self.HELP_TEXT_CREATE,
                "cancel_url": self.instance.study.get_absolute_url(),
            }

        helper = BaseFormHelper(self, **inputs)

        helper.add_row("cas", 2, "col-md-6")
        helper.add_row("cas_inferred", 2, "col-md-6")
        helper.add_row("source", 3, "col-md-4")
        helper.add_row("purity_confirmed_notes", 2, "col-md-6")
        helper.add_create_btn("dtxsid", reverse("assessment:dtxsid_create"), "Add new DTXSID")
        helper.form_id = "ivchemical-form"

        return helper


class IVCellTypeForm(forms.ModelForm):
    HELP_TEXT_CREATE = "Describes the cell type used in the current experiment."
    HELP_TEXT_UPDATE = "Update an existing cell type."

    species = forms.CharField(
        label="Species",
        widget=selectable.AutoCompleteWidget(lookups.IVCellTypeSpeciesLookup, allow_new=True),
    )
    strain = forms.CharField(
        label="Strain",
        widget=selectable.AutoCompleteWidget(lookups.IVCellTypeStrainLookup, allow_new=True),
    )
    cell_type = forms.CharField(
        label="Cell type",
        widget=selectable.AutoCompleteWidget(lookups.IVCellTypeCellTypeLookup, allow_new=True),
    )
    tissue = forms.CharField(
        label="Tissue",
        widget=selectable.AutoCompleteWidget(lookups.IVCellTypeTissueLookup, allow_new=True),
    )
    source = forms.CharField(
        label="Source of cell cultures",
        widget=selectable.AutoCompleteWidget(lookups.IVCellTypeSourceLookup, allow_new=True),
    )

    class Meta:
        model = models.IVCellType
        exclude = ("study",)

    def __init__(self, *args, **kwargs):
        study = kwargs.pop("parent", None)
        super().__init__(*args, **kwargs)
        if study:
            self.instance.study = study

        for field in ("species", "strain", "cell_type", "tissue", "source"):
            self.fields[field].widget.update_query_parameters(
                {"related": self.instance.study.assessment.id}
            )

    @property
    def helper(self):
        for fld in list(self.fields.keys()):
            widget = self.fields[fld].widget
            if type(widget) == forms.Textarea:
                widget.attrs["rows"] = 3

        if self.instance.id:
            inputs = {
                "legend_text": f"Update {self.instance}",
                "help_text": self.HELP_TEXT_UPDATE,
                "cancel_url": self.instance.get_absolute_url(),
            }
        else:
            inputs = {
                "legend_text": "Create new cell type",
                "help_text": self.HELP_TEXT_CREATE,
                "cancel_url": self.instance.study.get_absolute_url(),
            }

        helper = BaseFormHelper(self, **inputs)

        helper.add_row("species", 3, "col-md-4")
        helper.add_row("cell_type", 2, "col-md-6")
        helper.add_row("tissue", 2, "col-md-6")

        return helper


class IVExperimentForm(forms.ModelForm):

    HELP_TEXT_CREATE = ""
    HELP_TEXT_UPDATE = "Update an existing experiment."

    transfection = forms.CharField(
        widget=selectable.AutoCompleteWidget(lookups.IVExperimentTransfectionLookup, allow_new=True)
    )
    positive_control = forms.CharField(
        widget=selectable.AutoCompleteWidget(
            lookups.IVExperimentPositiveControlLookup, allow_new=True
        )
    )
    negative_control = forms.CharField(
        widget=selectable.AutoCompleteWidget(
            lookups.IVExperimentNegativeControlLookup, allow_new=True
        )
    )
    vehicle_control = forms.CharField(
        widget=selectable.AutoCompleteWidget(
            lookups.IVExperimentVehicleControlLookup, allow_new=True
        )
    )

    class Meta:
        model = models.IVExperiment
        exclude = ("study",)

    def __init__(self, *args, **kwargs):
        study = kwargs.pop("parent", None)
        super().__init__(*args, **kwargs)
        if study:
            self.instance.study = study
        self.fields["cell_type"].queryset = self.fields["cell_type"].queryset.filter(
            study=self.instance.study
        )

        for field in (
            "transfection",
            "positive_control",
            "negative_control",
            "vehicle_control",
        ):
            self.fields[field].widget.update_query_parameters(
                {"related": self.instance.study.assessment.id}
            )

    @property
    def helper(self):
        for fld in list(self.fields.keys()):
            widget = self.fields[fld].widget
            if type(widget) == forms.Textarea:
                widget.attrs["rows"] = 3

        if self.instance.id:
            inputs = {
                "legend_text": f"Update {self.instance}",
                "help_text": self.HELP_TEXT_UPDATE,
                "cancel_url": self.instance.get_absolute_url(),
            }
        else:
            inputs = {
                "legend_text": "Create new experiment",
                "help_text": self.HELP_TEXT_CREATE,
                "cancel_url": self.instance.study.get_absolute_url(),
            }

        helper = BaseFormHelper(self, **inputs)

        helper.add_row("name", 2, "col-md-6")
        helper.add_row("transfection", 2, "col-md-6")
        helper.add_row("dosing_notes", 2, "col-md-6")
        helper.add_row("has_positive_control", 2, "col-md-6")
        helper.add_row("has_negative_control", 2, "col-md-6")
        helper.add_row("has_vehicle_control", 2, "col-md-6")
        helper.add_row("control_notes", 2, "col-md-6")

        return helper


class CategoryModelChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.choice_label


class OELWidget(Select):
    def set_default_choices(self, instance):
        choices = [
            (-999, "---"),
        ]

        if instance.id:
            for eg in instance.groups.all():
                choices.append((eg.dose_group_id, eg.dose))

        self.choices = choices


class IVEndpointForm(forms.ModelForm):

    HELP_TEXT_CREATE = ""
    HELP_TEXT_UPDATE = "Update an existing endpoint."

    category = CategoryModelChoice(
        required=False, queryset=models.IVEndpointCategory.objects.none()
    )
    assay_type = forms.CharField(
        label="Assay Type",
        widget=selectable.AutoCompleteWidget(lookups.IVEndpointAssayTypeLookup, allow_new=True),
    )
    response_units = forms.CharField(
        label="Response Units",
        widget=selectable.AutoCompleteWidget(lookups.IVEndpointResponseUnitsLookup, allow_new=True),
    )

    class Meta:
        model = models.IVEndpoint
        exclude = (
            "assessment",
            "experiment",
        )
        widgets = {
            "NOEL": OELWidget(),
            "LOEL": OELWidget(),
        }

    def __init__(self, *args, **kwargs):
        experiment = kwargs.pop("parent", None)
        assessment = kwargs.pop("assessment", None)
        super().__init__(*args, **kwargs)
        if experiment:
            self.instance.experiment = experiment
        if assessment:
            self.instance.assessment = assessment

        self.fields["NOEL"].widget.set_default_choices(self.instance)
        self.fields["LOEL"].widget.set_default_choices(self.instance)

        self.fields["effect"].widget = selectable.AutoCompleteWidget(
            lookups.IVEndpointEffectLookup, allow_new=True
        )

        self.fields["effects"].widget = selectable.AutoCompleteSelectMultipleWidget(
            lookup_class=EffectTagLookup
        )
        self.fields["effects"].help_text = "Tags used to help categorize effect description."

        self.fields["chemical"].queryset = self.fields["chemical"].queryset.filter(
            study=self.instance.experiment.study
        )

        self.fields["category"].queryset = self.fields["category"].queryset.model.get_assessment_qs(
            self.instance.assessment_id
        )

        for field in ("assay_type", "response_units", "effect"):
            self.fields[field].widget.update_query_parameters(
                {"related": self.instance.assessment_id}
            )

    def clean_additional_fields(self):
        data = self.cleaned_data["additional_fields"]
        try:
            json.loads(data)
        except ValueError:
            raise forms.ValidationError("Must be valid JSON.")
        return data

    @property
    def helper(self):
        for fld in list(self.fields.keys()):
            widget = self.fields[fld].widget
            if type(widget) == forms.Textarea:
                widget.attrs["rows"] = 3

        if self.instance.id:
            inputs = {
                "legend_text": f"Update {self.instance}",
                "help_text": self.HELP_TEXT_UPDATE,
                "cancel_url": self.instance.get_absolute_url(),
            }
        else:
            inputs = {
                "legend_text": "Create new endpoint",
                "help_text": self.HELP_TEXT_CREATE,
                "cancel_url": self.instance.experiment.get_absolute_url(),
            }

        helper = BaseFormHelper(self, **inputs)

        helper.add_row("name", 2, "col-md-6")
        helper.add_row("chemical", 2, "col-md-6")
        helper.add_row("assay_type", 2, "col-md-6")
        helper.add_row("effect", 2, "col-md-6")
        helper.add_row("data_type", 4, "col-md-3")
        helper.add_row("observation_time", 4, "col-md-3")
        helper.add_row("monotonicity", 3, "col-md-4")
        helper.add_row("trend_test", 2, "col-md-6")
        helper.add_row("endpoint_notes", 2, "col-md-6")

        url = reverse("assessment:effect_tag_create", kwargs={"pk": self.instance.assessment_id})
        helper.add_create_btn("effects", url, "Add new effect tag")

        return helper


class IVEndpointFilterForm(forms.Form):

    ORDER_BY_CHOICES = (
        ("experiment__study__short_citation", "study"),
        ("experiment__name", "experiment name"),
        ("name", "endpoint name"),
        ("assay_type", "assay type"),
        ("effect", "effect"),
        ("chemical__name", "chemical"),
        ("category__name", "category"),
        ("observation_time", "observation time"),
        ("experiment__dose_units_id", "dose units"),
        ("response_units", "response units"),
    )

    studies = selectable.AutoCompleteSelectMultipleField(
        label="Study reference",
        lookup_class=InvitroStudyLookup,
        help_text="ex: Smith et al. 2010",
        required=False,
    )

    name = forms.CharField(
        label="Endpoint name",
        widget=selectable.AutoCompleteWidget(lookups.IVEndpointByAssessmentTextLookup),
        help_text="ex: B cells",
        required=False,
    )

    chemical = forms.CharField(
        label="Chemical name",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVChemicalNameLookup),
        help_text="ex: PFOA",
        required=False,
    )

    cas = forms.CharField(
        label="CAS",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVChemicalCASLookup),
        help_text="ex: 107-02-8",
        required=False,
    )

    cell_type = forms.CharField(
        label="Cell type",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVCellTypeNameLookup),
        help_text="ex: HeLa",
        required=False,
    )

    tissue = forms.CharField(
        label="Tissue",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVCellTypeTissueLookup),
        help_text="ex: adipocytes",
        required=False,
    )

    effect = forms.CharField(
        label="Effect",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVEndpointEffectLookup),
        help_text="ex: gene expression",
        required=False,
    )

    response_units = forms.CharField(
        label="Response units",
        widget=selectable.AutoCompleteWidget(lookups.RelatedIVEndpointResponseUnitsLookup),
        help_text="ex: counts",
        required=False,
    )

    dose_units = forms.ModelChoiceField(queryset=DoseUnits.objects.all(), required=False)

    order_by = forms.ChoiceField(choices=ORDER_BY_CHOICES,)

    paginate_by = forms.IntegerField(
        label="Items per page", min_value=10, initial=25, max_value=500, required=False
    )

    def __init__(self, *args, **kwargs):
        assessment = kwargs.pop("assessment")
        super().__init__(*args, **kwargs)
        self.fields["dose_units"].queryset = DoseUnits.objects.get_iv_units(assessment.id)
        for field in self.fields:
            if field not in ("dose_units", "order_by", "paginate_by"):
                self.fields[field].widget.update_query_parameters({"related": assessment.id})

    @property
    def helper(self):
        helper = BaseFormHelper(self, form_actions=form_actions_apply_filters())
        helper.form_method = "GET"

        helper.add_row("studies", 4, "col-md-3")
        helper.add_row("cell_type", 4, "col-md-3")
        helper.add_row("dose_units", 3, "col-md-3")

        return helper

    def get_query(self):

        studies = self.cleaned_data.get("studies")
        name = self.cleaned_data.get("name")
        chemical = self.cleaned_data.get("chemical")
        cas = self.cleaned_data.get("cas")
        cell_type = self.cleaned_data.get("cell_type")
        tissue = self.cleaned_data.get("tissue")
        effect = self.cleaned_data.get("effect")
        response_units = self.cleaned_data.get("response_units")
        dose_units = self.cleaned_data.get("dose_units")

        query = Q()
        if studies:
            query &= Q(experiment__study__in=studies)
        if name:
            query &= Q(name__icontains=name)
        if chemical:
            query &= Q(chemical__name__icontains=chemical)
        if cas:
            query &= Q(chemical__cas__icontains=cas)
        if cell_type:
            query &= Q(experiment__cell_type__cell_type__icontains=cell_type)
        if tissue:
            query &= Q(experiment__cell_type__tissue__icontains=tissue)
        if effect:
            query &= Q(effect__icontains=effect)
        if response_units:
            query &= Q(response_units__icontains=response_units)
        if dose_units:
            query &= Q(experiment__dose_units=dose_units)
        return query

    def get_order_by(self):
        return self.cleaned_data.get("order_by", self.ORDER_BY_CHOICES[0][0])

    def get_dose_units_id(self):
        if hasattr(self, "cleaned_data") and self.cleaned_data.get("dose_units"):
            return self.cleaned_data.get("dose_units").id


class IVEndpointGroupForm(forms.ModelForm):
    class Meta:
        model = models.IVEndpointGroup
        exclude = ("endpoint", "dose_group_id")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dose"].widget.attrs["class"] = "doses"


class BaseIVEndpointGroupFormset(BaseModelFormSet):
    pass


IVEndpointGroupFormset = modelformset_factory(
    models.IVEndpointGroup,
    form=IVEndpointGroupForm,
    formset=BaseIVEndpointGroupFormset,
    can_delete=True,
    extra=0,
)

BlankIVEndpointGroupFormset = modelformset_factory(
    models.IVEndpointGroup,
    form=IVEndpointGroupForm,
    formset=BaseIVEndpointGroupFormset,
    can_delete=True,
    extra=1,
)


class BaseIVBenchmarkForm(forms.ModelForm):
    class Meta:
        model = models.IVBenchmark
        fields = "__all__"


IVBenchmarkFormset = inlineformset_factory(
    models.IVEndpoint, models.IVBenchmark, form=BaseIVBenchmarkForm, extra=1
)
