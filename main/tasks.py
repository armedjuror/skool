"""
Celery Tasks for Fee Management
apps/fees/tasks.py

Periodic tasks for automatic fee creation:
- Monthly fees (runs on 1st of each month)
- Annual fees (runs daily, checks for annual fee triggers)

Author: Backend Team
Date: December 31, 2024
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from main.models import AcademicYear
from main.models import StudentEnrollment
from main.models import (
    FeeType,
    FeeStructure,
    StudentFeeDue,
    StudentFeeConfiguration
)


@shared_task
def create_monthly_fees():
    """
    Create monthly fee dues for all enrolled students.
    Runs on the 1st of every month via Celery Beat.

    Usage in celery.py:
    from celery.schedules import crontab

    app.conf.beat_schedule = {
        'create-monthly-fees': {
            'task': 'apps.fees.tasks.create_monthly_fees',
            'schedule': crontab(day_of_month='1', hour='0', minute='0'),
        },
    }
    """
    current_date = timezone.now().date()
    current_month = current_date.month
    current_year = current_date.year

    total_created = 0
    total_errors = 0

    print(f"\n{'=' * 60}")
    print(f"Starting Monthly Fee Creation: {current_date}")
    print(f"{'=' * 60}\n")

    # Get all active academic years
    active_years = AcademicYear.objects.filter(
        is_active=True,
        start_date__lte=current_date,
        end_date__gte=current_date
    )

    for academic_year in active_years:
        print(f"Processing Academic Year: {academic_year.name}")
        print(f"Organization: {academic_year.organization.name}\n")

        # Get monthly fee types for this organization
        monthly_fees = FeeType.objects.filter(
            organization=academic_year.organization,
            charge_trigger='MONTHLY',
            is_recurring=True,
            is_active=True
        )

        for fee_type in monthly_fees:
            print(f"  Processing Fee Type: {fee_type.name}")

            # Get all enrolled students for this academic year
            enrollments = StudentEnrollment.objects.filter(
                academic_year=academic_year,
                enrollment_status='ENROLLED'
            ).select_related(
                'student',
                'student__user',
                'student__user__userprofile',
                'class_division'
            )

            created_count = 0
            skipped_count = 0

            for enrollment in enrollments:
                try:
                    # Check if due already exists for this month
                    existing = StudentFeeDue.objects.filter(
                        student=enrollment.student,
                        academic_year=academic_year,
                        fee_type=fee_type,
                        month=current_month
                    ).exists()

                    if existing:
                        skipped_count += 1
                        continue

                    # Get applicable fee structure
                    fee_structure = get_applicable_fee_structure(
                        enrollment.student,
                        fee_type,
                        academic_year,
                        enrollment.class_division
                    )

                    if not fee_structure or not fee_structure.auto_create_due:
                        skipped_count += 1
                        continue

                    # Get amount (with student-specific override if exists)
                    amount = get_student_fee_amount(
                        enrollment.student,
                        fee_type,
                        academic_year
                    )

                    if amount <= 0:
                        skipped_count += 1
                        continue

                    # Create due record
                    StudentFeeDue.objects.create(
                        student=enrollment.student,
                        academic_year=academic_year,
                        fee_type=fee_type,
                        month=current_month,
                        total_amount=amount,
                        paid_amount=0,
                        due_amount=amount,
                        creation_source='AUTO_MONTHLY',
                        triggered_by_enrollment=enrollment,
                        due_date=current_date + timedelta(
                            days=fee_structure.due_days_after_trigger
                        )
                    )

                    created_count += 1
                    total_created += 1

                except Exception as e:
                    total_errors += 1
                    print(f"    ERROR for student {enrollment.student.admission_number}: {str(e)}")

            print(f"    Created: {created_count}, Skipped: {skipped_count}")

        print()

    print(f"{'=' * 60}")
    print(f"Monthly Fee Creation Complete")
    print(f"Total Created: {total_created}")
    print(f"Total Errors: {total_errors}")
    print(f"{'=' * 60}\n")

    return {
        'total_created': total_created,
        'total_errors': total_errors,
        'date': current_date.isoformat()
    }


@shared_task
def create_annual_fees():
    """
    Check and create annual fees based on charge_month.
    Runs daily to check if any annual fees are due.

    Usage in celery.py:
    app.conf.beat_schedule = {
        'create-annual-fees': {
            'task': 'apps.fees.tasks.create_annual_fees',
            'schedule': crontab(hour='1', minute='0'),  # Daily at 1 AM
        },
    }
    """
    current_date = timezone.now().date()
    current_month = current_date.month
    current_year = current_date.year

    total_created = 0
    total_errors = 0

    print(f"\n{'=' * 60}")
    print(f"Checking Annual Fees: {current_date}")
    print(f"{'=' * 60}\n")

    # Get annual fee types that should be charged this month
    annual_fees = FeeType.objects.filter(
        charge_trigger='ANNUAL',
        charge_month=current_month,
        is_active=True
    )

    if not annual_fees.exists():
        print("No annual fees configured for this month.\n")
        return {'total_created': 0, 'total_errors': 0}

    for fee_type in annual_fees:
        print(f"Processing Annual Fee: {fee_type.name}")
        print(f"Organization: {fee_type.organization.name}")

        # Get active academic years for this organization
        active_years = AcademicYear.objects.filter(
            organization=fee_type.organization,
            is_active=True,
            start_date__lte=current_date,
            end_date__gte=current_date
        )

        for academic_year in active_years:
            # Get all enrolled students
            enrollments = StudentEnrollment.objects.filter(
                academic_year=academic_year,
                enrollment_status='ENROLLED'
            ).select_related(
                'student',
                'student__user',
                'student__user__userprofile',
                'class_division'
            )

            created_count = 0
            skipped_count = 0

            for enrollment in enrollments:
                try:
                    # Check if due already exists for this year
                    existing = StudentFeeDue.objects.filter(
                        student=enrollment.student,
                        academic_year=academic_year,
                        fee_type=fee_type,
                        creation_source='AUTO_ANNUAL'
                    ).exists()

                    if existing:
                        skipped_count += 1
                        continue

                    # Get applicable fee structure
                    fee_structure = get_applicable_fee_structure(
                        enrollment.student,
                        fee_type,
                        academic_year,
                        enrollment.class_division
                    )

                    if not fee_structure or not fee_structure.auto_create_due:
                        skipped_count += 1
                        continue

                    # Get amount
                    amount = get_student_fee_amount(
                        enrollment.student,
                        fee_type,
                        academic_year
                    )

                    if amount <= 0:
                        skipped_count += 1
                        continue

                    # Create due record
                    StudentFeeDue.objects.create(
                        student=enrollment.student,
                        academic_year=academic_year,
                        fee_type=fee_type,
                        month=None,  # Annual fees don't have a specific month
                        total_amount=amount,
                        paid_amount=0,
                        due_amount=amount,
                        creation_source='AUTO_ANNUAL',
                        triggered_by_enrollment=enrollment,
                        due_date=current_date + timedelta(
                            days=fee_structure.due_days_after_trigger
                        )
                    )

                    created_count += 1
                    total_created += 1

                except Exception as e:
                    total_errors += 1
                    print(f"  ERROR for student {enrollment.student.admission_number}: {str(e)}")

            print(f"  Created: {created_count}, Skipped: {skipped_count}")

        print()

    print(f"{'=' * 60}")
    print(f"Annual Fee Check Complete")
    print(f"Total Created: {total_created}")
    print(f"Total Errors: {total_errors}")
    print(f"{'=' * 60}\n")

    return {
        'total_created': total_created,
        'total_errors': total_errors,
        'date': current_date.isoformat()
    }


@shared_task
def send_fee_reminders():
    """
    Send email reminders for overdue fees.
    Runs daily to check for dues past their due date.

    Usage in celery.py:
    app.conf.beat_schedule = {
        'send-fee-reminders': {
            'task': 'apps.fees.tasks.send_fee_reminders',
            'schedule': crontab(hour='9', minute='0'),  # Daily at 9 AM
        },
    }
    """
    from main.models import EmailNotification

    current_date = timezone.now().date()

    # Get overdue fees
    overdue_fees = StudentFeeDue.objects.filter(
        due_amount__gt=0,
        due_date__lt=current_date
    ).select_related(
        'student',
        'student__user',
        'student__user__userprofile',
        'student__family',
        'fee_type',
        'academic_year'
    )

    # Group by student
    student_dues = {}
    for due in overdue_fees:
        student_id = due.student.id
        if student_id not in student_dues:
            student_dues[student_id] = []
        student_dues[student_id].append(due)

    emails_queued = 0

    for student_id, dues in student_dues.items():
        student = dues[0].student
        family = student.family

        # Calculate total overdue
        total_overdue = sum(due.due_amount for due in dues)

        # Create email notification
        EmailNotification.objects.create(
            organization=student.user.organization,
            recipient_email=family.email,
            subject=f"Fee Payment Reminder - {student.admission_number}",
            body=f"""
Dear {family.father_name},

This is a reminder that the following fees for {student.user.userprofile.full_name} 
({student.admission_number}) are overdue:

{chr(10).join([f"- {due.fee_type.name}: {due.due_amount} QAR (Due: {due.due_date})" for due in dues])}

Total Overdue: {total_overdue} QAR

Please make the payment at your earliest convenience.

Thank you,
{student.user.organization.name}
            """.strip(),
            template_name='fee_reminder',
            context_data={
                'student': {
                    'name': student.user.userprofile.full_name,
                    'admission_number': student.admission_number,
                },
                'parent_name': family.father_name,
                'dues': [
                    {
                        'fee_type': due.fee_type.name,
                        'amount': float(due.due_amount),
                        'due_date': due.due_date.isoformat()
                    }
                    for due in dues
                ],
                'total_overdue': float(total_overdue)
            },
            status='PENDING'
        )

        emails_queued += 1

    return {
        'emails_queued': emails_queued,
        'date': current_date.isoformat()
    }


# Helper functions (same as in signals.py)
def get_applicable_fee_structure(student, fee_type, academic_year, class_division=None):
    """Get the applicable fee structure for a student."""
    from main.models import FeeStructure

    organization = student.user.organization

    if not academic_year:
        return None

    class_level = None
    if class_division:
        class_level = class_division.level
    elif student.current_enrollment:
        class_level = student.current_enrollment.class_division.level

    queries = [
        {
            'organization': organization,
            'academic_year': academic_year,
            'fee_type': fee_type,
            'branch': student.branch,
            'class_level': class_level,
            'is_active': True,
        },
        {
            'organization': organization,
            'academic_year': academic_year,
            'fee_type': fee_type,
            'branch': student.branch,
            'class_level__isnull': True,
            'is_active': True,
        },
        {
            'organization': organization,
            'academic_year': academic_year,
            'fee_type': fee_type,
            'branch__isnull': True,
            'class_level': class_level,
            'is_active': True,
        },
        {
            'organization': organization,
            'academic_year': academic_year,
            'fee_type': fee_type,
            'branch__isnull': True,
            'class_level__isnull': True,
            'is_active': True,
        },
    ]

    for query in queries:
        fee_structure = FeeStructure.objects.filter(**query).filter(
            applicable_to__in=['ALL', student.category]
        ).first()

        if fee_structure:
            return fee_structure

    return None


def get_student_fee_amount(student, fee_type, academic_year):
    """Get the fee amount for a student (with override check)."""
    if academic_year:
        student_config = StudentFeeConfiguration.objects.filter(
            student=student,
            academic_year=academic_year,
            fee_type=fee_type
        ).first()

        if student_config:
            return student_config.amount

    fee_structure = get_applicable_fee_structure(student, fee_type, academic_year)

    if fee_structure:
        return fee_structure.amount

    return 0