from django.db import migrations, models


def migrate_branch_to_branches(apps, schema_editor):
    """Copy existing FK branch data into the new M2M branches field."""
    StaffProfile = apps.get_model('main', 'StaffProfile')
    for staff in StaffProfile.objects.filter(branch__isnull=False).select_related('branch'):
        staff.branches.add(staff.branch)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_add_qid_upload_and_school_fields_to_student_registration'),
    ]

    operations = [
        # Step 1: Add the new M2M field (keeping old FK temporarily)
        migrations.AddField(
            model_name='staffprofile',
            name='branches',
            field=models.ManyToManyField(
                blank=True,
                related_name='staff_members_m2m',
                to='main.branch',
            ),
        ),
        # Step 2: Copy FK data into M2M
        migrations.RunPython(
            migrate_branch_to_branches,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 3: Remove the old FK field
        migrations.RemoveField(
            model_name='staffprofile',
            name='branch',
        ),
        # Step 4: Rename M2M to final name (remove old related_name collision)
        migrations.AlterField(
            model_name='staffprofile',
            name='branches',
            field=models.ManyToManyField(
                blank=True,
                related_name='staff_members',
                to='main.branch',
            ),
        ),
        # Step 5: Remove the old branch index
        migrations.AlterIndexTogether(
            name='staffprofile',
            index_together=set(),
        ),
    ]