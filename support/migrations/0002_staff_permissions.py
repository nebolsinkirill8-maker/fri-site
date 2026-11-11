from django.db import migrations


PERMISSIONS = {
    'ticket': ('view', 'change'),
    'ticketmessage': ('view', 'add'),
}


def grant_permissions(apps, schema_editor):
    alias = schema_editor.connection.alias
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    group = Group.objects.using(alias).get(name='Сотрудники')
    for model, actions in PERMISSIONS.items():
        content_type, _ = ContentType.objects.using(alias).get_or_create(app_label='support', model=model)
        for action in actions:
            permission, _ = Permission.objects.using(alias).get_or_create(
                content_type=content_type,
                codename=f'{action}_{model}',
                defaults={'name': f'Can {action} {model}'},
            )
            group.permissions.add(permission)


def revoke_permissions(apps, schema_editor):
    alias = schema_editor.connection.alias
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    group = Group.objects.using(alias).filter(name='Сотрудники').first()
    if group:
        codenames = [f'{action}_{model}' for model, actions in PERMISSIONS.items() for action in actions]
        permissions = Permission.objects.using(alias).filter(content_type__app_label='support', codename__in=codenames)
        group.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [('support', '0001_initial'), ('portal', '0003_roles')]
    operations = [migrations.RunPython(grant_permissions, revoke_permissions)]
