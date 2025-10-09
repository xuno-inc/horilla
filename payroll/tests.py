"""test cases"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from payroll.forms.forms import ContractForm
from payroll.models.models import Contract
from employee.models import Employee


class ContractSalaryEntryModeTests(TestCase):
    """Test cases for salary entry mode functionality"""

    def setUp(self):
        """Set up test data"""
        self.employee = Employee.objects.create(
            employee_first_name="John",
            employee_last_name="Doe",
            employee_id="EMP001"
        )

    def test_manual_mode_validation(self):
        """Test manual mode validation"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'manual',
            'wage': 5000.00,
            'allowance_salary': 1000.00,
        }
        form = ContractForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test that net_salary is cleared in manual mode
        cleaned_data = form.clean()
        self.assertIsNone(cleaned_data.get('net_salary'))

    def test_manual_mode_missing_basic_salary(self):
        """Test manual mode with missing basic salary"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'manual',
            'allowance_salary': 1000.00,
        }
        form = ContractForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('wage', form.errors)

    def test_manual_mode_missing_allowance_salary(self):
        """Test manual mode with missing allowance salary"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'manual',
            'wage': 5000.00,
        }
        form = ContractForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('allowance_salary', form.errors)

    def test_manual_mode_negative_values(self):
        """Test manual mode with negative values"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'manual',
            'wage': -1000.00,
            'allowance_salary': 1000.00,
        }
        form = ContractForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('wage', form.errors)

    def test_net_split_mode_validation(self):
        """Test net split mode validation"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'net_split',
            'net_salary': 10000.00,
        }
        form = ContractForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test that basic and allowance are computed correctly
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['wage'], Decimal('6000.00'))
        self.assertEqual(cleaned_data['allowance_salary'], Decimal('4000.00'))

    def test_net_split_mode_missing_net_salary(self):
        """Test net split mode with missing net salary"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'net_split',
        }
        form = ContractForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('net_salary', form.errors)

    def test_net_split_mode_negative_net_salary(self):
        """Test net split mode with negative net salary"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'net_split',
            'net_salary': -1000.00,
        }
        form = ContractForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('net_salary', form.errors)

    def test_net_split_calculation_precision(self):
        """Test net split calculation with precise rounding"""
        form_data = {
            'contract_name': 'Test Contract',
            'employee_id': self.employee.id,
            'contract_start_date': '2024-01-01',
            'salary_entry_mode': 'net_split',
            'net_salary': 1000.33,  # Test with decimal that doesn't divide evenly
        }
        form = ContractForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.clean()
        # Basic should be 60% = 600.20
        self.assertEqual(cleaned_data['wage'], Decimal('600.20'))
        # Allowance should be 40% = 400.13
        self.assertEqual(cleaned_data['allowance_salary'], Decimal('400.13'))

    def test_contract_model_apply_net_split(self):
        """Test the apply_net_split method on Contract model"""
        contract = Contract(
            contract_name='Test Contract',
            employee_id=self.employee,
            contract_start_date='2024-01-01',
            salary_entry_mode='net_split',
            net_salary=Decimal('10000.00')
        )
        
        contract.apply_net_split()
        
        self.assertEqual(contract.wage, 6000.00)
        self.assertEqual(contract.allowance_salary, Decimal('4000.00'))

    def test_contract_model_apply_net_split_with_none(self):
        """Test apply_net_split with None net_salary"""
        contract = Contract(
            contract_name='Test Contract',
            employee_id=self.employee,
            contract_start_date='2024-01-01',
            salary_entry_mode='net_split',
            net_salary=None
        )
        
        # Should not raise an error
        contract.apply_net_split()
        
        # Values should remain unchanged
        self.assertIsNone(contract.wage)
        self.assertIsNone(contract.allowance_salary)


class ContractMigrationTests(TestCase):
    """Test cases for contract migrations"""

    def test_migration_sets_default_values(self):
        """Test that migration sets correct default values for existing contracts"""
        # This test would typically be run after applying migrations
        # For now, we'll test the model defaults
        contract = Contract(
            contract_name='Test Contract',
            employee_id=self.employee,
            contract_start_date='2024-01-01'
        )
        
        # Test default values
        self.assertEqual(contract.salary_entry_mode, 'manual')
        self.assertEqual(contract.allowance_salary, Decimal('0.00'))
        self.assertIsNone(contract.net_salary)

    def test_backward_compatibility(self):
        """Test that existing contracts without new fields work correctly"""
        # Create a contract with only basic fields (simulating pre-migration state)
        contract = Contract.objects.create(
            contract_name='Legacy Contract',
            employee_id=self.employee,
            contract_start_date='2024-01-01',
            wage=5000.00
        )
        
        # After migration, these should have default values
        contract.refresh_from_db()
        self.assertEqual(contract.salary_entry_mode, 'manual')
        self.assertEqual(contract.allowance_salary, Decimal('0.00'))
        self.assertIsNone(contract.net_salary)
