from django.apps import apps
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView

from ..assessment.models import Assessment
from ..common.crumbs import Breadcrumb
from ..common.helper import WebappConfig
from ..common.views import BaseList, LoginRequiredMixin, TeamMemberOrHigherMixin, WebappMixin
from . import models


def mgmt_dashboard_breadcrumb(assessment) -> Breadcrumb:
    return Breadcrumb(
        name="Management dashboard", url=reverse("mgmt:assessment_dashboard", args=(assessment.id,))
    )


# View mixins for ensuring tasks are started
class EnsurePreparationStartedMixin:
    """Ensure the preparation task has been started if form is valid."""

    def get_success_url(self):
        models.Task.objects.ensure_preparation_started(self.object, self.request.user)
        return super().get_success_url()


class EnsureExtractionStartedMixin:
    """Ensure the extraction task has been started if form is valid."""

    def get_success_url(self):
        study = self.object.study
        user = self.request.user
        models.Task.objects.ensure_preparation_stopped(study)
        models.Task.objects.ensure_extraction_started(study, user)
        return super().get_success_url()


# User-level task views
class RobTaskMixin:
    """
    Add risk of bias tasks for a user to task views.
    """

    def get_rob_queryset(self, RiskOfBias):
        raise NotImplementedError("Abstract method; requires implementation")

    def get_review_tasks(self):
        RiskOfBias = apps.get_model("riskofbias", "RiskOfBias")
        rob_tasks = self.get_rob_queryset(RiskOfBias)
        filtered_tasks = [rob for rob in rob_tasks if rob.is_complete is False]
        return RiskOfBias.get_qs_json(filtered_tasks, json_encode=False)

    def get_app_config(self, context) -> WebappConfig:
        assessment_id = self.assessment.id if hasattr(self, "assessment") else None
        task_url = (
            reverse("mgmt:api:task-assessment-assignments", args=(assessment_id,))
            if assessment_id
            else reverse("mgmt:api:task-assignments")
        )
        return WebappConfig(
            app="mgmtStartup",
            page="TaskAssignments",
            data={
                "assessment_id": assessment_id,
                "csrf": get_token(self.request),
                "user": self.request.user.id,
                "rob_tasks": self.get_review_tasks(),
                "tasks": {
                    "submit_url": reverse("mgmt:api:task-list"),
                    "url": task_url,
                    "list": self.model.get_qs_json(context["object_list"], json_encode=False),
                },
                "autocomplete": {
                    "url": reverse(
                        "selectable-lookup", args=("myuser-assessmentteammemberorhigherlookup",)
                    )
                },
            },
        )


class UserAssignments(WebappMixin, RobTaskMixin, LoginRequiredMixin, ListView):
    model = models.Task
    template_name = "mgmt/user_assignments.html"

    def get_queryset(self):
        return self.model.objects.owned_by(self.request.user)

    def get_rob_queryset(self, RiskOfBias):
        return RiskOfBias.objects.filter(author=self.request.user, active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = Breadcrumb.build_crumbs(self.request.user, "Assigned tasks")
        return context


class UserAssessmentAssignments(RobTaskMixin, LoginRequiredMixin, BaseList):
    parent_model = Assessment
    model = models.Task
    template_name = "mgmt/user_assessment_assignments.html"

    def get_queryset(self):
        return (
            self.model.objects.owned_by(self.request.user)
            .filter(study__assessment=self.assessment)
            .select_related("owner", "study", "study__reference_ptr", "study__assessment")
        )

    def get_rob_queryset(self, RiskOfBias):
        return RiskOfBias.objects.filter(
            author=self.request.user, active=True, study__assessment=self.assessment
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"].insert(2, mgmt_dashboard_breadcrumb(self.assessment))
        context["breadcrumbs"][3] = Breadcrumb(name="My assigned tasks")
        return context


# Assessment-level task views
class TaskDashboard(TeamMemberOrHigherMixin, BaseList):
    parent_model = Assessment
    model = models.Task
    template_name = "mgmt/assessment_dashboard.html"

    def get_assessment(self, *args, **kwargs):
        return get_object_or_404(Assessment, pk=kwargs["pk"])

    def get_queryset(self):
        return self.model.objects.assessment_qs(self.assessment.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"][2] = Breadcrumb(name="Management dashboard")
        return context

    def get_app_config(self, context) -> WebappConfig:
        return WebappConfig(
            app="mgmtStartup", page="Dashboard", data=dict(assessment_id=self.assessment.id)
        )


def task_table_app_config(view, edit: bool) -> WebappConfig:
    a_id = view.assessment.id
    return WebappConfig(
        app="mgmtStartup",
        page="TaskTable",
        data=dict(
            assessment_id=a_id,
            csrf=get_token(view.request),
            displayAsForm=edit,
            cancelUrl=reverse("mgmt:assessment_tasks", args=(a_id,)),
            tasksListUrl=reverse("mgmt:api:task-list") + f"?assessment_id={a_id}",
            taskUpdateBaseUrl=reverse("mgmt:api:task-list"),
            taskBulkPatchUrl=reverse("mgmt:api:task-bulk-patch") + f"?assessment_id={a_id}",
            studyListUrl=reverse("study:api:study-list") + f"?assessment_id={a_id}",
            userAutocompleteUrl=reverse(
                "selectable-lookup", args=("myuser-assessmentteammemberorhigherlookup",)
            ),
        ),
    )


class TaskDetail(TaskDashboard):
    template_name = "mgmt/assessment_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"].insert(2, mgmt_dashboard_breadcrumb(self.assessment))
        context["breadcrumbs"][3] = Breadcrumb(name="Assignments")
        return context

    def get_app_config(self, context) -> WebappConfig:
        return task_table_app_config(self, False)


class TaskModify(TaskDashboard):
    template_name = "mgmt/assessment_modify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"].insert(2, mgmt_dashboard_breadcrumb(self.assessment))
        context["breadcrumbs"][3] = Breadcrumb(name="Update assignments")
        return context

    def get_app_config(self, context) -> WebappConfig:
        return task_table_app_config(self, True)
