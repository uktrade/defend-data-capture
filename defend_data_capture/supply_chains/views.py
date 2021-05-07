from datetime import date, datetime, timedelta
from typing import List, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.template.defaultfilters import date as date_filter
from django.db.models import Count, QuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, TemplateView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    UpdateView,
    CreateView,
    TemplateView,
)
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin

from supply_chains.models import (
    SupplyChain,
    StrategicAction,
    StrategicActionUpdate,
    RAGRating,
)
from accounts.models import User, GovDepartment
from supply_chains.forms import (
    MonthlyUpdateSubmissionForm,
    YesNoChoices,
    ApproximateTimings,
)
from supply_chains.models import (
    SupplyChain,
    StrategicAction,
    StrategicActionUpdate,
    RAGRating,
)
from supply_chains import forms

from supply_chains.utils import (
    get_last_day_of_this_month,
    get_last_working_day_of_a_month,
    get_last_working_day_of_previous_month,
)
from supply_chains.mixins import PaginationMixin, GovDepPermissionMixin


class HomePageView(LoginRequiredMixin, PaginationMixin, ListView):
    model = SupplyChain
    context_object_name = "supply_chains"
    template_name = "index.html"

    def get_queryset(self):
        return self.request.user.gov_department.supply_chains.annotate(
            strategic_action_count=Count("strategic_actions")
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_deadline = get_last_working_day_of_previous_month()

        context["supply_chains"] = self.paginate(self.object_list, 5)
        context["deadline"] = get_last_working_day_of_a_month(
            get_last_day_of_this_month()
        )
        context["num_updated_supply_chains"] = self.object_list.submitted_since(
            last_deadline
        ).count()
        context["gov_department_name"] = self.request.user.gov_department.name

        # TODO: Remove attribute update_complete if its not going to be used by RT-170
        context["update_complete"] = (
            context["num_updated_supply_chains"] == self.object_list.count()
        )

        context["num_in_prog_supply_chains"] = (
            self.object_list.count() - context["num_updated_supply_chains"]
        )

        return context


class SCTaskListView(
    LoginRequiredMixin, GovDepPermissionMixin, PaginationMixin, TemplateView
):
    template_name = "task_list.html"
    tasks_per_page = 5
    last_deadline = get_last_working_day_of_previous_month()

    def _update_review_routes(self) -> None:
        for update in self.sa_updates:
            update["route"] += "/review"

    def _sort_updates(self, updates: List) -> List:
        SORT_ORDER = {
            "Not started": 0,
            "In progress": 1,
            "Completed": 2,
            "Submitted": 3,
        }

        updates.sort(key=lambda val: SORT_ORDER[val["status"].label])

        return updates

    def _get_sa_update_list(self, sa_qset) -> List[Dict]:
        sa_updates = list()

        for sa in sa_qset.iterator():
            update = dict()

            update["name"] = sa.name
            update["description"] = sa.description

            sau = StrategicActionUpdate.objects.since(
                self.last_deadline,
                supply_chain=self.supply_chain,
                strategic_action=sa,
            )

            # Note: route property could be replaced with URL of StrategicActionUpdate view
            # method, when its available
            if sau:
                update["status"] = StrategicActionUpdate.Status(sau[0].status)
                update["route"] = reverse(
                    "monthly-update-info-edit",
                    kwargs={
                        "supply_chain_slug": self.supply_chain.slug,
                        "strategic_action_slug": sa.slug,
                        "update_slug": sau[0].slug,
                    },
                )
            else:
                update["status"] = StrategicActionUpdate.Status.NOT_STARTED
                update["route"] = reverse(
                    "monthly-update-create",
                    kwargs={
                        "supply_chain_slug": self.supply_chain.slug,
                        "strategic_action_slug": sa.slug,
                    },
                )

            sa_updates.append(update)

        return self._sort_updates(sa_updates)

    def _extract_view_data(self, *args, **kwargs):
        sc_slug = kwargs.get("sc_slug", "DEFAULT")
        self.supply_chain = SupplyChain.objects.get(slug=sc_slug, is_archived=False)

        sa_qset = StrategicAction.objects.filter(supply_chain=self.supply_chain)
        self.total_sa = sa_qset.count()

        self.sa_updates = self._get_sa_update_list(sa_qset)

        self.completed_updates = StrategicActionUpdate.objects.since(
            self.last_deadline,
            supply_chain=self.supply_chain,
            status__in=[
                StrategicActionUpdate.Status.COMPLETED,
                StrategicActionUpdate.Status.SUBMITTED,
            ],
        ).count()

        self.submitted_only_updates = StrategicActionUpdate.objects.since(
            self.last_deadline,
            supply_chain=self.supply_chain,
            status=StrategicActionUpdate.Status.SUBMITTED,
        ).count()

        self.update_complete = (
            self.total_sa == self.completed_updates and self.total_sa != 0
        )
        self.update_submitted = (
            self.total_sa == self.submitted_only_updates and self.total_sa != 0
        )

        if self.update_submitted:
            self._update_review_routes()

    def dispatch(self, *args, **kwargs):
        self._extract_view_data(*args, **kwargs)
        self.sa_updates = self.paginate(self.sa_updates, self.tasks_per_page)

        return super().dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.total_sa == self.completed_updates and self.total_sa:
            self.supply_chain.last_submission_date = date.today()
            self.supply_chain.save()

            updates = StrategicActionUpdate.objects.since(
                self.last_deadline,
                supply_chain=self.supply_chain,
                status=StrategicActionUpdate.Status.COMPLETED,
            )

            for update in updates.iterator():
                update.submission_date = date.today()
                update.status = StrategicActionUpdate.Status.SUBMITTED
                update.save()

            return redirect("update_complete", sc_slug=self.supply_chain.slug)
        else:
            self.submit_error = True
            kwargs.setdefault("view", self)
            return render(self.request, self.template_name, context=kwargs)


class SCCompleteView(LoginRequiredMixin, GovDepPermissionMixin, TemplateView):
    template_name = "task_complete.html"

    def _validate(self) -> bool:
        total_sa = StrategicAction.objects.filter(
            supply_chain=self.supply_chain
        ).count()
        submitted = StrategicActionUpdate.objects.since(
            self.last_deadline,
            supply_chain=self.supply_chain,
            status=StrategicActionUpdate.Status.SUBMITTED,
        ).count()

        return total_sa == submitted

    def get(self, request, *args, **kwargs):
        sc_slug = kwargs.get("sc_slug", "DEFAULT")
        self.last_deadline = get_last_working_day_of_previous_month()
        self.supply_chain = SupplyChain.objects.filter(slug=sc_slug, is_archived=False)[
            0
        ]

        # This is to gaurd manual access if not actually complete, help them to complete
        if not self._validate():
            return redirect("tlist", sc_slug=self.supply_chain.slug)

        supply_chains = request.user.gov_department.supply_chains.order_by("name")

        self.sum_of_supply_chains = supply_chains.count()

        self.num_updated_supply_chains = supply_chains.submitted_since(
            self.last_deadline
        ).count()

        kwargs.setdefault("view", self)
        return render(request, self.template_name, context=kwargs)


# @login_required
# class MonthlyUpdate
class StrategicActionListView(ListView):
    model = StrategicAction
    template_name = "supply_chains/temp-sa-list.html"
    context_object_name = "strategic_actions"


class MonthlyUpdateMixin:
    model = StrategicActionUpdate
    context_object_name = "strategic_action_update"
    slug_url_kwarg = "update_slug"

    def get_queryset(self):
        strategic_action_slug = self.kwargs.get("strategic_action_slug")
        return (
            super().get_queryset().filter(strategic_action__slug=strategic_action_slug)
        )

    def get_strategic_action(self, strategic_action_slug):
        return StrategicAction.objects.get(slug=strategic_action_slug)

    def get_success_url(self):
        # This method needs to be implemented by the pages
        # so as to express their rules for what the "next" page is
        raise NotImplementedError(
            f"get_success_url() not implemented by {self.__class__}"
        )

    def get_navigation_links(self):
        url_kwargs = {
            "supply_chain_slug": self.object.strategic_action.supply_chain.slug,
            "strategic_action_slug": self.object.strategic_action.slug,
            "update_slug": self.object.slug,
        }

        navigation_links = {
            "Info": {
                "label": "Update information",
                "url": reverse_lazy("monthly-update-info-edit", kwargs=url_kwargs),
                "view": MonthlyUpdateInfoEditView,
            },
            "Timing": {
                "label": "Timing",
                "url": reverse_lazy("monthly-update-timing-edit", kwargs=url_kwargs),
                "view": MonthlyUpdateTimingEditView,
            },
            "Status": {
                "label": "Action status",
                "url": reverse_lazy("monthly-update-status-edit", kwargs=url_kwargs),
                "view": MonthlyUpdateStatusEditView,
            },
            "RevisedTiming": {
                "label": "Revised timing",
                "url": reverse_lazy(
                    "monthly-update-revised-timing-edit", kwargs=url_kwargs
                ),
                "view": MonthlyUpdateRevisedTimingEditView,
            },
            "Summary": {
                "label": "Confirm",
                "url": reverse_lazy("monthly-update-summary", kwargs=url_kwargs),
                "view": MonthlyUpdateSummaryView,
            },
        }
        if self.object.has_existing_target_completion_date:
            navigation_links.pop("Timing")
            if (
                not self.object.has_changed_target_completion_date
                and not isinstance(self, MonthlyUpdateRevisedTimingEditView)
                and not self.object.is_becoming_ongoing
            ):
                navigation_links.pop("RevisedTiming")
        else:
            navigation_links.pop("RevisedTiming")
        for title, info in navigation_links.items():
            info["is_current_page"] = isinstance(self, info["view"])
        return navigation_links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation_links"] = self.get_navigation_links()
        return context


class MonthlyUpdateInfoCreateView(MonthlyUpdateMixin, CreateView):
    template_name = "supply_chains/monthly-update-info-form.html"
    form_class = forms.MonthlyUpdateInfoForm

    def get(self, request, *args, **kwargs):
        last_deadline = get_last_working_day_of_previous_month()
        strategic_action: StrategicAction = self.get_strategic_action(
            kwargs["strategic_action_slug"]
        )
        current_month_updates = strategic_action.monthly_updates.since(last_deadline)
        if current_month_updates.exists():
            current_month_update: StrategicActionUpdate = (
                current_month_updates.order_by("date_created").last()
            )
        else:
            current_month_update: StrategicActionUpdate = (
                strategic_action.monthly_updates.create(
                    status=StrategicActionUpdate.Status.IN_PROGRESS,
                    supply_chain=strategic_action.supply_chain,
                )
            )
        update_url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": current_month_update.strategic_action.supply_chain.slug,
                "strategic_action_slug": current_month_update.strategic_action.slug,
                "update_slug": current_month_update.slug,
            },
        )
        return redirect(update_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["strategic_action"] = self.get_strategic_action(
            self.kwargs["strategic_action_slug"]
        )
        return context

    def form_valid(self, form):
        strategic_action = self.get_strategic_action(
            self.kwargs["strategic_action_slug"]
        )
        form.instance.strategic_action = strategic_action
        form.instance.supply_chain = strategic_action.supply_chain
        return super().form_valid(form)

    # def get_success_url(self):
    #     return super().get_success_url()
    #


class MonthlyUpdateInfoEditView(MonthlyUpdateMixin, UpdateView):
    template_name = "supply_chains/monthly-update-info-form.html"
    form_class = forms.MonthlyUpdateInfoForm

    def get_success_url(self):
        if self.object.strategic_action.target_completion_date is None:
            next_page_url = "monthly-update-timing-edit"
        else:
            next_page_url = "monthly-update-status-edit"
        url_kwargs = {
            "supply_chain_slug": self.object.strategic_action.supply_chain.slug,
            "update_slug": self.object.slug,
            "strategic_action_slug": self.object.strategic_action.slug,
        }
        return reverse(next_page_url, kwargs=url_kwargs)


class MonthlyUpdateStatusEditView(MonthlyUpdateMixin, UpdateView):
    template_name = "supply_chains/monthly-update-status-form.html"
    form_class = forms.MonthlyUpdateStatusForm

    completion_date_change_form = None

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "RED-will_completion_date_change" in self.request.POST:
            self.completion_date_change_form = form.fields[
                "implementation_rag_rating"
            ].widget.details["RED"]["form"]
        return form

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        return form_kwargs

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        next_page_url = "monthly-update-summary"
        if self.completion_date_change_form:
            if self.completion_date_change_form.is_valid():
                if (
                    self.completion_date_change_form.cleaned_data[
                        "will_completion_date_change"
                    ]
                    == "True"
                ):
                    next_page_url = "monthly-update-revised-timing-edit"
        url_kwargs = {
            "supply_chain_slug": self.object.strategic_action.supply_chain.slug,
            "update_slug": self.object.slug,
            "strategic_action_slug": self.object.strategic_action.slug,
        }
        return reverse(next_page_url, kwargs=url_kwargs)


class MonthlyUpdateTimingEditView(MonthlyUpdateMixin, UpdateView):
    template_name = "supply_chains/monthly-update-timing-form.html"
    form_class = forms.MonthlyUpdateTimingForm

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        next_page_url = "monthly-update-status-edit"
        url_kwargs = {
            "supply_chain_slug": self.object.strategic_action.supply_chain.slug,
            "update_slug": self.object.slug,
            "strategic_action_slug": self.object.strategic_action.slug,
        }
        return reverse(next_page_url, kwargs=url_kwargs)


class MonthlyUpdateRevisedTimingEditView(MonthlyUpdateTimingEditView):
    template_name = "supply_chains/monthly-update-revised-timing-form.html"
    form_class = forms.MonthlyUpdateModifiedTimingForm

    def get_success_url(self):
        next_page_url = "monthly-update-summary"
        # see form_valid() for an explanation of original_object
        url_kwargs = {
            "supply_chain_slug": self.object.strategic_action.supply_chain.slug,
            "update_slug": self.object.slug,
            "strategic_action_slug": self.object.strategic_action.slug,
        }
        return reverse(next_page_url, kwargs=url_kwargs)


class MonthlyUpdateSummaryView(MonthlyUpdateMixin, UpdateView):
    template_name = "supply_chains/monthly-update-summary.html"
    form_class = MonthlyUpdateSubmissionForm

    def get_object(self, queryset=None):
        return super().get_object(queryset)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["data"] = self.build_form_data()
        return form_kwargs

    def build_form_data(self):
        """
        As this page won't really display the form but needs to show error messages for missing or invalid values,
        we have to build a representation of the form data that would have caused the current state of our instance
        had a form been submitted to us.
        When this is passed into the "form" constructor via form_kwargs, it takes care of instantiating
        the forms we actually need with this data. Then the form is validated (in get_context_data)
        which gives us the valid or invalid forms we use to build the page.
        """
        # we always have the content field and the delivery status
        form_data = {
            "content": self.object.content,
            "implementation_rag_rating": self.object.implementation_rag_rating,
        }
        # we always have the action status form, but we need to determine how to configure it
        if self.object.implementation_rag_rating != RAGRating.GREEN:
            # Red or Amber, so must include the reason for delays
            if self.object.implementation_rag_rating == RAGRating.AMBER:
                form_data[
                    f"{RAGRating.AMBER}-reason_for_delays"
                ] = self.object.reason_for_delays
            elif self.object.implementation_rag_rating == RAGRating.RED:
                form_data[
                    f"{RAGRating.RED}-reason_for_delays"
                ] = self.object.reason_for_delays
                # if the status is RED and the timing is changing, include the revised timing fields
                if (
                    self.object.implementation_rag_rating == RAGRating.RED
                    and self.object.is_changing_target_completion_date
                ):
                    form_data[
                        f"reason_for_completion_date_change"
                    ] = self.model.reason_for_completion_date_change
                    if self.object.has_changed_target_completion_date:
                        additional_form_data = {
                            "is_completion_date_known": YesNoChoices.YES,
                            f"{YesNoChoices.YES}-changed_target_completion_date_day": self.object.changed_target_completion_date.day,
                            f"{YesNoChoices.YES}-changed_target_completion_date_month": self.object.changed_target_completion_date.month,
                            f"{YesNoChoices.YES}-changed_target_completion_date_year": self.object.changed_target_completion_date.year,
                        }
                        form_data.update(additional_form_data)
                    elif self.model.changed_is_ongoing:
                        additional_form_data = {
                            "is_completion_date_known": YesNoChoices.YES,
                            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONGOING,
                        }
                        form_data.update(additional_form_data)
        # we only have the timing form if the instance either didn't already know its target completion date
        # or didn't already know it was ongoing
        # or still doesn't know either of those things from pending changes
        if (
            self.object.has_new_target_completion_date
            or self.object.has_new_is_ongoing
            or self.object.has_no_timing_information
        ):
            if self.object.has_new_target_completion_date:
                additional_form_data = {
                    "is_completion_date_known": YesNoChoices.YES,
                    f"{YesNoChoices.YES}-changed_target_completion_date_day": self.object.changed_target_completion_date.day,
                    f"{YesNoChoices.YES}-changed_target_completion_date_month": self.object.changed_target_completion_date.month,
                    f"{YesNoChoices.YES}-changed_target_completion_date_year": self.object.changed_target_completion_date.year,
                }
                form_data.update(additional_form_data)
            elif self.object.has_new_is_ongoing:
                additional_form_data = {
                    "is_completion_date_known": YesNoChoices.NO,
                    f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONGOING,
                }
                form_data.update(additional_form_data)
        return form_data

    def get_context_data(self, **kwargs):
        kwargs[
            "has_revised_date_of_completion"
        ] = self.object.is_changing_target_completion_date
        kwargs[
            "has_date_of_completion"
        ] = self.object.has_updated_target_completion_date
        kwargs[
            "has_new_date_of_completion"
        ] = self.object.has_new_target_completion_date
        kwargs["needs_target_completion_date"] = (
            self.object.has_no_target_completion_date and self.object.has_no_is_ongoing
        )
        kwargs = super().get_context_data(**kwargs)
        if "form" in kwargs.keys():
            kwargs["form"].is_valid()
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if not form.is_valid():
            return self.get(request, *args, **kwargs)
        """
        To finalise the update we must:
        1. Copy a revised target completion date to the strategic action, or copy is ongoing and clear the SA's date;
        2. If there is a revised target completion date, record the change in reversion;
        3. Change the update's status to "Completed"
        """
        strategic_action_update = self.get_object()
        self.object = strategic_action_update
        strategic_action: StrategicAction = strategic_action_update.strategic_action
        strategic_action_changed = False
        if strategic_action_update.changed_target_completion_date is not None:
            strategic_action.target_completion_date = (
                strategic_action_update.changed_target_completion_date
            )
            strategic_action.is_ongoing = False
            strategic_action_changed = True
        if strategic_action_update.changed_is_ongoing:
            strategic_action.is_ongoing = strategic_action_update.changed_is_ongoing
            strategic_action.target_completion_date = None
            strategic_action_changed = True
        # TODO: reversion!
        strategic_action_update.status = StrategicActionUpdate.Status.COMPLETED
        if strategic_action_changed:
            strategic_action.save()
        strategic_action_update.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("tlist", kwargs={"sc_slug": self.object.supply_chain.slug})


class SASummaryView(
    LoginRequiredMixin, GovDepPermissionMixin, PaginationMixin, TemplateView
):
    template_name = "strategic_action_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supply_chain = SupplyChain.objects.get(slug=kwargs.get("sc_slug"))

        context["strategic_actions"] = self.paginate(
            supply_chain.strategic_actions.filter(is_archived=False).order_by("name"),
            5,
        )
        context["supply_chain"] = supply_chain
        return context


class SCSummary(LoginRequiredMixin, GovDepPermissionMixin, TemplateView):
    template_name = "sc_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sc_slug = kwargs.get("sc_slug", "DEFAULT")

        context["supply_chain"] = SupplyChain.objects.filter(
            slug=sc_slug, is_archived=False
        )[0]
        return context


class SAUReview(LoginRequiredMixin, GovDepPermissionMixin, TemplateView):
    template_name = "sau_review.html"
    last_deadline = get_last_working_day_of_previous_month()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sc_slug, sa_slug, sau_slug = (
            kwargs.get("sc_slug"),
            kwargs.get("sa_slug"),
            kwargs.get("sau_slug"),
        )

        sau = StrategicActionUpdate.objects.since(
            deadline=self.last_deadline,
            status=StrategicActionUpdate.Status.SUBMITTED,
            slug=sau_slug,
            supply_chain__slug=sc_slug,
            strategic_action__slug=sa_slug,
        )[0]

        context["supply_chain"] = sau.supply_chain
        context["strategic_action"] = sau.strategic_action
        context["update"] = sau

        if sau.strategic_action.is_ongoing:
            context["completion_estimation"] = "Ongoing"
        else:
            context["completion_estimation"] = date_filter(
                sau.strategic_action.target_completion_date, "d F Y"
            )

        return context
