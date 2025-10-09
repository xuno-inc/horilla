"""
forms.py
"""

from typing import Any

from django import forms
from django.forms import widgets
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from base.forms import Form, ModelForm
from employee.forms import MultipleFileField
from employee.models import Employee
from payroll.context_processors import get_active_employees
from payroll.models.models import (
    Contract,
    EncashmentGeneralSettings,
    PayrollGeneralSetting,
    ReimbursementFile,
    ReimbursementrequestComment,
)


class ContractForm(ModelForm):
    """
    ContactForm
    """

    verbose_name = _("Contract")
    contract_start_date = forms.DateField()
    contract_end_date = forms.DateField(required=False)
    
    # Salary entry mode fields
    salary_entry_mode = forms.ChoiceField(
        choices=[
            ("manual", _("Manual (Basic + Allowance)")),
            ("net_split", _("Net Split (60% / 40%)")),
        ],
        widget=forms.RadioSelect,
        initial="manual",
        label=_("Salary Entry Mode"),
        help_text=_("Choose how to enter salary information")
    )
    allowance_salary = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label=_("Allowance Salary"),
        help_text=_("Allowance amount (used in manual mode)")
    )
    net_salary = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label=_("Net Salary"),
        help_text=_("Net salary amount (used in net split mode)")
    )

    class Meta:
        """
        Meta class for additional options
        """

        fields = "__all__"
        exclude = [
            "is_active",
        ]
        model = Contract

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee_id"].widget.attrs.update(
            {"onchange": "contractInitial(this)"}
        )
        self.fields["contract_start_date"].widget = widgets.DateInput(
            attrs={
                "type": "date",
                "class": "oh-input w-100",
                "placeholder": "Select a date",
            }
        )
        self.fields["contract_end_date"].widget = widgets.DateInput(
            attrs={
                "type": "date",
                "class": "oh-input w-100",
                "placeholder": "Select a date",
            }
        )
        self.fields["contract_status"].widget.attrs.update(
            {
                "class": "oh-select",
            }
        )
        if self.instance and self.instance.pk:
            dynamic_url = self.get_dynamic_hx_post_url(self.instance)
            self.fields["contract_status"].widget.attrs.update(
                {
                    "hx-target": "this",
                    "hx-post": dynamic_url,
                    "hx-swap": "beforebegin",
                }
            )
        first = PayrollGeneralSetting.objects.first()
        if first and self.instance.pk is None:
            self.initial["notice_period_in_days"] = first.notice_period
        self.fields["contract_document"].widget.attrs[
            "accept"
        ] = ".jpg, .jpeg, .png, .pdf"

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("contract_form_with_salary.html", context)
        return table_html

    def get_dynamic_hx_post_url(self, instance):
        """
        Render the url for contract status update through hx request
        """
        return f"/payroll/update-contract-status/{instance.pk}"

    def clean(self):
        """
        Validate salary entry mode logic
        """
        cleaned_data = super().clean()
        salary_entry_mode = cleaned_data.get('salary_entry_mode')
        wage = cleaned_data.get('wage')
        allowance_salary = cleaned_data.get('allowance_salary')
        net_salary = cleaned_data.get('net_salary')
        
        if salary_entry_mode == "manual":
            # Manual mode: basic_salary and allowance_salary are required
            if wage is None:
                raise forms.ValidationError({
                    'wage': _("Basic salary is required in manual mode.")
                })
            if allowance_salary is None:
                raise forms.ValidationError({
                    'allowance_salary': _("Allowance salary is required in manual mode.")
                })
            
            # Ensure non-negative values
            if wage is not None and wage < 0:
                raise forms.ValidationError({
                    'wage': _("Basic salary must be non-negative.")
                })
            if allowance_salary is not None and allowance_salary < 0:
                raise forms.ValidationError({
                    'allowance_salary': _("Allowance salary must be non-negative.")
                })
            
            # Clear net_salary for manual mode
            cleaned_data['net_salary'] = None
            
        elif salary_entry_mode == "net_split":
            # Net split mode: net_salary is required
            if net_salary is None:
                raise forms.ValidationError({
                    'net_salary': _("Net salary is required in net split mode.")
                })
            
            # Ensure non-negative net salary
            if net_salary is not None and net_salary < 0:
                raise forms.ValidationError({
                    'net_salary': _("Net salary must be non-negative.")
                })
            
            # Compute basic and allowance from net salary
            if net_salary is not None:
                basic = round((net_salary * 60) / 100, 2)
                allowance = round(net_salary - basic, 2)
                cleaned_data['wage'] = basic
                cleaned_data['allowance_salary'] = allowance
        
        return cleaned_data


class ReimbursementRequestCommentForm(ModelForm):
    """
    ReimbursementRequestCommentForm form
    """

    class Meta:
        """
        Meta class for additional options
        """

        model = ReimbursementrequestComment
        fields = ("comment",)


class reimbursementCommentForm(ModelForm):
    """
    Reimbursement request comment model form
    """

    verbose_name = "Add Comment"

    class Meta:
        """
        Meta class for additional options
        """

        model = ReimbursementrequestComment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["files"] = MultipleFileField(label="files")
        self.fields["files"].required = False
        self.fields["files"].widget.attrs["accept"] = ".jpg, .jpeg, .png, .pdf"

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html

    def save(self, commit: bool = ...) -> Any:
        multiple_files_ids = []
        files = None
        if self.files.getlist("files"):
            files = self.files.getlist("files")
            self.instance.attachemnt = files[0]
            multiple_files_ids = []
            for attachemnt in files:
                file_instance = ReimbursementFile()
                file_instance.file = attachemnt
                file_instance.save()
                multiple_files_ids.append(file_instance.pk)
        instance = super().save(commit)
        if commit:
            instance.files.add(*multiple_files_ids)
        return instance, files


class EncashmentGeneralSettingsForm(ModelForm):
    class Meta:
        model = EncashmentGeneralSettings
        fields = "__all__"


class DashboardExport(Form):
    status_choices = [
        ("", ""),
        ("draft", "Draft"),
        ("review_ongoing", "Review Ongoing"),
        ("confirmed", "Confirmed"),
        ("paid", "Paid"),
    ]
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "oh-input w-100"}),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "oh-input w-100"}),
    )
    employees = forms.ChoiceField(
        required=False,
        choices=[(emp.id, emp.get_full_name()) for emp in Employee.objects.all()],
        widget=forms.SelectMultiple,
    )
    status = forms.ChoiceField(required=False, choices=status_choices)
    contributions = forms.ChoiceField(
        required=False,
        choices=[
            (emp.id, emp.get_full_name())
            for emp in get_active_employees(None)["get_active_employees"]
        ],
        widget=forms.SelectMultiple,
    )
