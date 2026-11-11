from django.db import migrations


def provision_roles(apps, schema_editor):
    alias = schema_editor.connection.alias
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('portal', 'User')
    participants, _ = Group.objects.using(alias).get_or_create(name='Участники')
    participants.permissions.clear()
    staff, _ = Group.objects.using(alias).get_or_create(name='Сотрудники')
    permissions = []
    for model in ('tournamentsettings', 'stage', 'sponsor', 'team', 'match', 'user'):
        content_type, _ = ContentType.objects.using(alias).get_or_create(app_label='portal', model=model)
        for action in (('view',) if model == 'user' else ('view', 'add', 'change')):
            permission, _ = Permission.objects.using(alias).get_or_create(content_type=content_type, codename=f'{action}_{model}', defaults={'name': f'Can {action} {model}'})
            permissions.append(permission)
    staff.permissions.set(permissions)
    for user in User.objects.using(alias).filter(is_staff=False, is_superuser=False).iterator():
        user.groups.add(participants)


class Migration(migrations.Migration):
    dependencies = [('portal', '0002_user_mmr_user_nickname_user_position_user_steam_url_and_more')]
    operations = [migrations.RunPython(provision_roles, migrations.RunPython.noop)]
