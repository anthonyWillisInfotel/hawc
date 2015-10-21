import abc
import json

from datetime import datetime

from django.core.urlresolvers import reverse_lazy
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from utils.views import (AssessmentPermissionsMixin, MessageMixin, BaseList,
                         BaseCreate, BaseDetail, BaseUpdate, BaseDelete,
                         GenerateReport, ProjectManagerOrHigherMixin,
                         TeamMemberOrHigherMixin)
from utils.helper import listToUl
from assessment.models import Assessment

from . import forms, exports, models


class LitOverview(BaseList):
    parent_model = Assessment
    model = models.Search
    template_name = "lit/overview.html"

    def get_queryset(self):
        return self.model.objects.filter(assessment=self.assessment)\
                                 .exclude(slug="manual-import")

    def get_context_data(self, **kwargs):
        context = super(LitOverview, self).get_context_data(**kwargs)
        context['overview'] = models.Reference.get_overview_details(self.assessment)
        context['manual_import'] = models.Search.get_manually_added(self.assessment)
        if context['obj_perms']['edit']: # expensive, only calculate if needed
            qryset = models.Reference.get_references_ready_for_import(self.assessment)
            context['need_import_count'] = qryset.count()
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class SearchList(BaseList):
    parent_model = Assessment
    model = models.Search

    def get_queryset(self):
        return self.model.objects.filter(assessment=self.assessment)


class SearchCopyAsNewSelector(AssessmentPermissionsMixin, FormView):
    """
    Select an existing search and copy-as-new
    """
    template_name = "lit/search_copy_selector.html"
    form_class = forms.SearchSelectorForm

    def dispatch(self, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment, pk=kwargs['pk'])
        self.permission_check_user_can_view()
        return super(SearchCopyAsNewSelector, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchCopyAsNewSelector, self).get_context_data(**kwargs)
        context['assessment'] = self.assessment
        return context

    def get_form_kwargs(self):
        kwargs = super(SearchCopyAsNewSelector, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['assessment'] = self.assessment
        return kwargs


class RefDownloadExcel(BaseList):
    """
    If a tag primary-key is specified, download all references associated
    with that tag or any child tags for the selected assessment. Otherwise,
    download a full export of data.
    """
    parent_model = Assessment
    model = models.Reference

    def get(self, request, *args, **kwargs):
        try:
            tag_id = int(request.GET.get('tag_id'))
            self.tag = models.ReferenceFilterTag.get_tag_in_assessment(
                self.assessment.id, tag_id)
        except:
            self.tag = None
        return super(RefDownloadExcel, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.tag:
            self.include_parent_tag = True
            self.fn = "{}-{}-refs".format(self.tag.name, self.assessment)
            self.sheet_name = self.tag.name
            self.tags = models.ReferenceFilterTag.dump_bulk(self.tag)
        else:
            self.include_parent_tag = False
            self.fn = "{}-refs".format(self.assessment)
            self.sheet_name = unicode(self.assessment)
            self.tags = models.ReferenceFilterTag.get_all_tags(
                assessment=self.assessment, json_encode=False)

    def get_queryset(self):
        if self.tag:
            return self.model.get_references_with_tag(self.tag, descendants=True)
        else:
            return self.model.objects.filter(assessment=self.assessment)

    def render_to_response(self, context, **response_kwargs):
        exporter = exports.ReferenceFlatComplete(
            self.object_list,
            export_format="excel",
            filename=self.fn,
            sheet_name=self.sheet_name,
            assessment=self.assessment,
            tags=self.tags,
            include_parent_tag=self.include_parent_tag)
        return exporter.build_response()


class SearchNew(BaseCreate):
    success_message = 'Search created.'
    parent_model = Assessment
    parent_template_name = 'assessment'
    model = models.Search
    form_class = forms.SearchForm
    search_type = 'Search'

    def get_context_data(self, **kwargs):
        context = super(SearchNew, self).get_context_data(**kwargs)
        context['type'] = self.search_type
        return context

    def get_form_kwargs(self):
        kwargs = super(SearchNew, self).get_form_kwargs()

        # check if we have a template to use
        try:
            pk = int(self.request.GET.get('initial', -1))
        except ValueError:
            pk = -1

        if pk > 0:
            obj = self.model.objects.filter(pk=pk).first()
            permitted_assesments = Assessment.get_viewable_assessments(
                self.request.user, exclusion_id=self.assessment.pk)
            if obj and obj.assessment in permitted_assesments:
                kwargs['initial'] = model_to_dict(obj)

        return kwargs


class ImportNew(SearchNew):
    success_message = "Import created."
    form_class = forms.ImportForm
    search_type = 'Import'

    def post_object_save(self, form):
        self.object.run_new_import()


class ImportRISNew(ImportNew):
    form_class = forms.RISForm


class RISExportInstructions(TemplateView):
    template_name = 'lit/ris_export_instructions.html'


class SearchDetail(BaseDetail):
    model = models.Search

    def get_object(self, **kwargs):
        obj = get_object_or_404(models.Search,
                                slug=self.kwargs.get(self.slug_url_kwarg),
                                assessment=self.kwargs.get('pk'))
        return super(SearchDetail, self).get_object(object=obj)


class SearchUpdate(BaseUpdate):
    success_message = 'Search updated.'
    model = models.Search
    form_class = forms.SearchForm

    def get_object(self):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        assessment = self.kwargs.get('pk', None)
        obj = get_object_or_404(models.Search, assessment=assessment, slug=slug)
        return super(SearchUpdate, self).get_object(object=obj)

    def post_object_save(self, form):
        if self.object.source == 2:
            self.object.run_new_query()  # re-import from HERO only

    def get_context_data(self, **kwargs):
        context = super(SearchUpdate, self).get_context_data(**kwargs)
        context['type'] = self.object.get_search_type_display()
        return context


class SearchDelete(BaseDelete):
    success_message = 'Search deleted.'
    model = models.Search

    def get_object(self):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        self.assessment = get_object_or_404(Assessment, pk=self.kwargs.get('pk'))
        obj = get_object_or_404(models.Search, assessment=self.assessment, slug=slug)
        return super(SearchDelete, self).get_object(object=obj)

    def get_success_url(self):
        return reverse_lazy('lit:search_list', kwargs={'pk': self.assessment.pk})


class SearchDownloadExcel(BaseDetail):
    model = models.Search

    def get_object(self, **kwargs):
        obj = get_object_or_404(models.Search,
                                slug=self.kwargs.get(self.slug_url_kwarg),
                                assessment=self.kwargs.get('pk'))
        return super(SearchDownloadExcel, self).get_object(object=obj)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        exporter = exports.ReferenceFlatComplete(
            self.object.references.all(),
            export_format="excel",
            filename=self.object.slug,
            sheet_name=self.object.slug,
            assessment=self.assessment,
            tags=models.ReferenceFilterTag.get_all_tags(assessment=self.assessment, json_encode=False),
            include_parent_tag=False)
        return exporter.build_response()


class SearchQuery(BaseUpdate):
    model = models.Search
    form_class = forms.SearchForm
    http_method_names = (u'get', )  # don't allow POST

    def get_object(self, **kwargs):
        obj = get_object_or_404(self.model,
                                slug=self.kwargs.get(self.slug_url_kwarg),
                                assessment=self.kwargs.get('pk'))
        return super(SearchQuery, self).get_object(object=obj)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.run_new_query()
        except models.TooManyPubMedResults as e:
            return HttpResponse("""
                                <p>PubMed Search error: <br>{0}</p>
                                <p>Please perform a more targeted-search.</p>
                                """.format(e))
        return HttpResponseRedirect(self.object.get_absolute_url())


class TagReferences(TeamMemberOrHigherMixin, FormView):
    """
    Abstract base-class to tag references, using various methods to get instance.
    """
    form_class = forms.TagReferenceForm
    template_name = "lit/search_tags_edit.html"

    @abc.abstractmethod
    def get_assessment(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404
        response = self.update_reference_tags()
        return HttpResponse(json.dumps(response), content_type="application/json")

    def update_reference_tags(self):
        # find reference, check that the assessment is the same as the one we
        # have permissions-checked for, and if so, update reference-tags
        response = {"status": "fail"}
        pk = self.request.POST.get('pk', -1)
        ref = models.Reference.objects\
            .filter(pk=pk, assessment=self.assessment).first()
        if ref:
            tag_pks = self.request.POST.getlist('tags[]', [])
            ref.tags.set(tag_pks)
            ref.last_updated = datetime.now()
            ref.save()
            response["status"] = "success"
        return response

    def get_context_data(self, **kwargs):
        context = super(TagReferences, self).get_context_data(**kwargs)
        context['object'] = self.object
        context['model'] = self.model.__name__
        return context


class TagBySearch(TagReferences):
    """
    Edit tags for a single Search.
    """
    model = models.Search

    def get_assessment(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            self.model,
            slug=self.kwargs.get('slug'),
            assessment=self.kwargs.get('pk'))
        return self.object.get_assessment()

    def get_context_data(self, **kwargs):
        context = super(TagBySearch, self).get_context_data(**kwargs)
        context['references'] = models.Reference.objects\
            .filter(searches=self.object)\
            .prefetch_related('identifiers')
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class TagByReference(TagReferences):
    """
    Edit tags for on a single reference.
    """
    model = models.Reference

    def get_assessment(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            self.model,
            pk=self.kwargs.get('pk'))
        return self.object.get_assessment()

    def get_context_data(self, **kwargs):
        context = super(TagByReference, self).get_context_data(**kwargs)
        context['references'] = self.model.objects\
            .filter(pk=self.object.pk)\
            .prefetch_related('identifiers')
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class TagByTag(TagReferences):
    """
    Tag references with a specific tag.
    """
    model = models.ReferenceFilterTag

    def get_assessment(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            self.model,
            pk=self.kwargs.get('pk'))
        return self.object.get_assessment()

    def get_context_data(self, **kwargs):
        context = super(TagByTag, self).get_context_data(**kwargs)
        context['references'] = models.Reference.objects\
            .filter(tags=self.object.pk)\
            .distinct()\
            .prefetch_related('identifiers')
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class TagByUntagged(TagReferences):
    """
    View to tag all untagged references for an assessment.
    """
    model = Assessment

    def get_assessment(self, request, *args, **kwargs):
        self.object = get_object_or_404(Assessment, id=self.kwargs.get('pk'))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(TagByUntagged, self).get_context_data(**kwargs)
        context['references'] = models.Reference.get_untagged_references(self.assessment)
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class SearchRefList(BaseDetail):
    model = models.Search
    template_name = "lit/reference_list.html"

    def get_object(self, **kwargs):
        obj = get_object_or_404(models.Search,
                                slug=self.kwargs.get(self.slug_url_kwarg),
                                assessment=self.kwargs.get('pk'))
        return super(SearchRefList, self).get_object(object=obj)

    def get_context_data(self, **kwargs):
        context = super(SearchRefList, self).get_context_data(**kwargs)
        context['ref_objs'] = self.object.get_all_reference_tags()
        context['object_type'] = 'search'
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        context['untagged'] = self.object.references_untagged
        return context


class SearchTagsVisualization(BaseDetail):
    model = models.Search
    template_name = "lit/reference_visual.html"

    def get_object(self, **kwargs):
        obj = get_object_or_404(models.Search,
                                slug=self.kwargs.get(self.slug_url_kwarg),
                                assessment=self.kwargs.get('pk'))
        return super(SearchTagsVisualization, self).get_object(object=obj)

    def get_context_data(self, **kwargs):
        context = super(SearchTagsVisualization, self).get_context_data(**kwargs)
        context['object_type'] = 'search'
        context['ref_objs'] = self.object.get_all_reference_tags()
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        context['objectType'] = self.model.__name__
        return context


class RefList(BaseList):
    parent_model = Assessment
    model = models.Reference

    def get_context_data(self, **kwargs):
        context = super(RefList, self).get_context_data(**kwargs)
        context['object_type'] = 'reference'
        context['ref_objs'] = models.Reference.get_full_assessment_json(self.assessment)
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        context['untagged'] = models.Reference.get_untagged_references(self.assessment)
        return context


class RefUploadExcel(ProjectManagerOrHigherMixin, MessageMixin, FormView):
    """
    Upload Excel files and update reference details.
    """
    model = Assessment
    template_name = "lit/reference_upload_excel.html"
    form_class = forms.ReferenceExcelUploadForm

    def get_assessment(self, request, *args, **kwargs):
        return get_object_or_404(Assessment, pk=kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super(RefUploadExcel, self).get_form_kwargs()
        kwargs['assessment'] = self.assessment
        return kwargs

    def form_valid(self, form):
        errors = models.Reference.process_excel(
            form.cleaned_data['df'],
            self.assessment.id
        )
        if len(errors) > 0:
            msg = u"""References updated, but some errors were found
                (references with errors were not updated): {0}"""\
                .format(listToUl(errors))
        else:
            msg = "References updated."
        self.success_message = msg
        return super(RefUploadExcel, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('lit:overview', args=[self.assessment.pk])


class RefReport(GenerateReport):
    parent_model = Assessment
    model = models.Reference
    report_type = 0

    def get_queryset(self):
        return self.model.objects.filter(assessment=self.assessment)

    def get_filename(self):
        return "literature.docx"

    def get_context(self, queryset):
        return self.model.get_docx_template_context(queryset)


class RefListExtract(BaseList):
    parent_model = Assessment
    model = models.Reference
    crud = 'Update' # update-level permission required despite list-view
    template_name = 'lit/reference_extract_list.html'

    def get_queryset(self):
        return self.model.get_references_ready_for_import(self.assessment)


class RefDetail(BaseDetail):
    model = models.Reference

    def get_context_data(self, **kwargs):
        context = super(RefDetail, self).get_context_data(**kwargs)
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        context['object_json'] = self.object.get_json()
        return context


class RefSearch(AssessmentPermissionsMixin, FormView):
    template_name = 'lit/reference_search.html'
    form_class = forms.ReferenceSearchForm

    def dispatch(self, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment, pk=kwargs['pk'])
        return super(RefSearch, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        kwargs['assessment_pk'] = self.assessment.pk
        return kwargs

    def form_valid(self, form):
        refs = form.search()
        return HttpResponse(json.dumps({"status": "success",
                                        "refs": refs}),
                            content_type="application/json")

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        context['assessment'] = self.assessment
        context['obj_perms'] = super(RefSearch, self).get_obj_perms()
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context


class RefsByTagJSON(BaseDetail):
    model = Assessment

    def get_context_data(self, **kwargs):
        response = {"status": "success", "refs": []}
        search_id = self.request.GET.get('search_id', None)
        if search_id is not None:
            search_id = int(search_id)

        tag_id = self.kwargs.get('tag_id', None)
        tag = None
        if tag_id != "untagged":
            tag = models.ReferenceFilterTag.get_tag_in_assessment(
                self.assessment.id, int(tag_id))

        if search_id:
            search = models.Search.objects.get(id=search_id)
            refs = search.get_references_with_tag(tag=tag, descendants=True)
        elif tag:
            refs = models.Reference.get_references_with_tag(tag, descendants=True)
        else:
            refs = models.Reference.get_untagged_references(self.assessment)

        response["refs"] = [
            ref.get_json(json_encode=False, searches=True)
            for ref in refs
        ]
        self.response = response

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(json.dumps(self.response), content_type="application/json")


class RefVisualization(BaseDetail):
    model = Assessment
    template_name = "lit/reference_visual.html"

    def get_context_data(self, **kwargs):
        context = super(RefVisualization, self).get_context_data(**kwargs)
        context['object_type'] = 'reference'
        context['ref_objs'] = models.Reference.get_full_assessment_json(self.assessment)
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        context['objectType'] = self.model.__name__
        return context


class TagsJSON(BaseDetail):
    model = Assessment

    def get_object(self, **kwargs):
        try:
            pk = int(self.request.GET.get('pk', -1))
        except ValueError:
            pk = -1
        obj = get_object_or_404(self.model, pk=pk)
        return super(TagsJSON, self).get_object(object=obj)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        tags = models.ReferenceFilterTag.get_all_tags(self.object)
        return HttpResponse(json.dumps(tags), content_type="application/json")


class TagsUpdate(BaseUpdate):
    """
    Update tags for an assessment. Note that right now, only project managers
    of the assessment can update tags. (we use the Assessment as the model in an
    update-view, which only project-managers have permission to do-so).
    """
    model = Assessment
    template_name = "lit/tags_update.html"
    form_class = forms.NullForm

    def get_context_data(self, **kwargs):
        context = super(TagsUpdate, self).get_context_data(**kwargs)
        context['tags'] = models.ReferenceFilterTag.get_all_tags(self.assessment)
        return context

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax():
            self.object = self.get_object()
            response = self.post_update_ReferenceFilterTag({"status": "success"})
            return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            raise Http404

    def post_update_ReferenceFilterTag(self, response):
        try:
            status = self.request.POST.get('status')
            if status == "add":
                parent_pk = self.request.POST.get('parent_pk', None)
                name = self.request.POST.get('name')
                response["node"] = models.ReferenceFilterTag.add_tag(self.assessment.pk, name, parent_pk)
            elif status == "remove":
                pk = self.request.POST.get('pk', None)
                models.ReferenceFilterTag.remove_tag(self.assessment.pk, pk)
            elif status == "move":
                tag = get_object_or_404(models.ReferenceFilterTag, pk=self.request.POST.get('pk', -1))
                offset = int(self.request.POST.get('offset'))
                tag.move_within_parent(self.assessment.pk, offset)
            else:
                raise Exception()
        except:
            response["status"] = "fail"
        return response


class TagsCopy(AssessmentPermissionsMixin, MessageMixin, FormView):
    """
    Remove exiting tags and copy all tags from a separate assessment.
    """
    model = Assessment
    template_name = "lit/tags_copy.html"
    form_class = forms.TagsCopyForm
    success_message = 'Literature tags for this assessment have been updated'

    def dispatch(self, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment, pk=kwargs['pk'])
        self.permission_check_user_can_edit()
        return super(TagsCopy, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TagsCopy, self).get_context_data(**kwargs)
        context['assessment'] = self.assessment
        return context

    def get_form_kwargs(self):
        kwargs = super(TagsCopy, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['assessment'] = self.assessment
        return kwargs

    def form_valid(self, form):
        form.copy_tags()
        return super(TagsCopy, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('lit:tags_update', kwargs={'pk': self.assessment.pk})
