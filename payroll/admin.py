"""
admin.py

Used to register models on admin site
"""

from django.contrib import admin

from payroll.models.models import (
    Allowance,
    Contract,
    Deduction,
    FilingStatus,
    LoanAccount,
    MultipleCondition,
    Payslip,
    PayslipAutoGenerate,
    Reimbursement,
    ReimbursementrequestComment,
)
from payroll.models.tax_models import PayrollSettings, TaxBracket

# Register your models here.

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_name', 
        'employee_id', 
        'contract_start_date', 
        'contract_end_date',
        'salary_entry_mode',
        'wage',
        'allowance_salary',
        'net_salary',
        'contract_status'
    ]
    list_filter = [
        'contract_status',
        'salary_entry_mode',
        'wage_type',
        'pay_frequency',
        'contract_start_date',
        'contract_end_date'
    ]
    search_fields = [
        'contract_name',
        'employee_id__employee_first_name',
        'employee_id__employee_last_name'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('contract_name', 'employee_id', 'contract_start_date', 'contract_end_date', 'contract_status')
        }),
        ('Salary Information', {
            'fields': ('salary_entry_mode', 'wage', 'allowance_salary', 'net_salary'),
            'description': 'Choose salary entry mode and enter salary details'
        }),
        ('Job Details', {
            'fields': ('department', 'job_position', 'job_role', 'shift', 'work_type'),
            'classes': ('collapse',)
        }),
        ('Pay Details', {
            'fields': ('wage_type', 'pay_frequency', 'filing_status'),
            'classes': ('collapse',)
        }),
        ('Leave Settings', {
            'fields': ('deduct_leave_from_basic_pay', 'calculate_daily_leave_amount', 'deduction_for_one_leave_amount'),
            'classes': ('collapse',)
        }),
        ('Additional', {
            'fields': ('notice_period_in_days', 'contract_document', 'note'),
            'classes': ('collapse',)
        })
    )

admin.site.register(FilingStatus)
admin.site.register(TaxBracket)
admin.site.register(Allowance)
admin.site.register(Deduction)
admin.site.register(Payslip)
admin.site.register(PayrollSettings)
admin.site.register(LoanAccount)
admin.site.register(Reimbursement)
admin.site.register(ReimbursementrequestComment)
admin.site.register(MultipleCondition)
admin.site.register(PayslipAutoGenerate)
