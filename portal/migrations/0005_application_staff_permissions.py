from django.db import migrations


def grant_application_permissions(apps, schema_editor):
    alias = schema_editor.connection.alias
    group_model = apps.get_model('auth', 'Group')
    permission_model = apps.get_model('auth', 'Permission')
    content_type_model = apps.get_model('contenttypes', 'ContentType')
    group, _ = group_model.objects.using(alias).get_or_create(name='Сотрудники')
    content_type, _ = content_type_model.objects.using(alias).get_or_create(
        app_label='portal', model='tournamentapplication',
    )
    for action in ('view', 'change'):
        permission, _ = permission_model.objects.using(alias).get_or_create(
            content_type=content_type,
            codename=f'{action}_tournamentapplication',
            defaults={'name': f'Can {action} tournament application'},
        )
        group.permissions.add(permission)


def revoke_application_permissions(apps, schema_editor):
    alias = schema_editor.connection.alias
    group_model = apps.get_model('auth', 'Group')
    permission_model = apps.get_model('auth', 'Permission')
    group = group_model.objects.using(alias).filter(name='Сотрудники').first()
    if group:
        permissions = permission_model.objects.using(alias).filter(
            content_type__app_label='portal',
            content_type__model='tournamentapplication',
            codename__in=('view_tournamentapplication', 'change_tournamentapplication'),
        )
        group.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [('portal', '0004_tournament_applications')]
    operations = [migrations.RunPython(grant_application_permissions, revoke_application_permissions)]
