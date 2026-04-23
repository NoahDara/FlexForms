import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from submissions.models import FormSubmission
from forms.models import Form


class DashboardTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        is_form_manager = (
            user.has_perm('forms.view_form') or
            user.has_perm('forms.change_form')
        )

        # --- Scoped submissions queryset ---
        if is_form_manager:
            submissions = FormSubmission.objects.filter(
                Q(owner=user) |
                ~Q(status=FormSubmission.SubmissionStatus.DRAFT)
            )
        else:
            submissions = FormSubmission.objects.filter(owner=user)

        # --- Stat cards ---
        context['total_submissions'] = submissions.count()
        context['draft_count'] = submissions.filter(
            status=FormSubmission.SubmissionStatus.DRAFT
        ).count()
        context['submitted_count'] = submissions.filter(
            status=FormSubmission.SubmissionStatus.SUBMITTED
        ).count()
        context['approved_count'] = submissions.filter(
            status=FormSubmission.SubmissionStatus.APPROVED
        ).count()
        context['rejected_count'] = submissions.filter(
            status=FormSubmission.SubmissionStatus.REJECTED
        ).count()

        # --- Forms stats ---
        context['published_forms'] = Form.objects.filter(is_published=True).count()
        context['draft_forms'] = Form.objects.filter(is_published=False).count()

        # --- Submissions over time (last 30 days) ---
        thirty_days_ago = timezone.now() - timedelta(days=30)
        over_time = (
            submissions
            .filter(created__gte=thirty_days_ago)
            .annotate(day=TruncDate('created'))
            .values('day')
            .annotate(count=Count('uid'))
            .order_by('day')
        )
        context['submissions_over_time'] = json.dumps([
            {'day': str(item['day']), 'count': item['count']}
            for item in over_time
        ])

        # --- Status distribution (for donut chart) ---
        status_dist = (
            submissions
            .values('status')
            .annotate(count=Count('uid'))
        )
        context['status_distribution'] = json.dumps([
            {'status': item['status'], 'count': item['count']}
            for item in status_dist
        ])

        # --- Per-form breakdown (admin only) ---
        if is_form_manager:
            per_form = (
                submissions
                .exclude(status=FormSubmission.SubmissionStatus.DRAFT)
                .values('form__title')
                .annotate(count=Count('uid'))
                .order_by('-count')[:10]
            )
            context['per_form_breakdown'] = json.dumps([
                {'form': item['form__title'], 'count': item['count']}
                for item in per_form
            ])

        # --- Recent submissions table ---
        context['recent_submissions'] = (
            submissions
            .select_related('form', 'owner')
            .order_by('-created')[:10]
        )

        # --- User specific: available forms and drafts ---
        context['available_forms'] = (
            Form.objects.filter(is_published=True)
            .order_by('-updated')[:6]
        )
        context['my_drafts'] = submissions.filter(
            status=FormSubmission.SubmissionStatus.DRAFT
        ).select_related('form').order_by('-updated')[:5]

        context['is_form_manager'] = is_form_manager
        return context