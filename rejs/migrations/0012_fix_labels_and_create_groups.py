# Generated manually - fix Polish labels and create user groups

from django.db import migrations, models


def create_user_groups(apps, schema_editor):
    """Tworzy domyślne grupy użytkowników z odpowiednimi uprawnieniami."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # Pobierz content types dla modeli
    Rejs = apps.get_model("rejs", "Rejs")
    Zgloszenie = apps.get_model("rejs", "Zgloszenie")
    Wplata = apps.get_model("rejs", "Wplata")
    Wachta = apps.get_model("rejs", "Wachta")
    Ogloszenie = apps.get_model("rejs", "Ogloszenie")

    rejs_ct = ContentType.objects.get_for_model(Rejs)
    zgloszenie_ct = ContentType.objects.get_for_model(Zgloszenie)
    wplata_ct = ContentType.objects.get_for_model(Wplata)
    wachta_ct = ContentType.objects.get_for_model(Wachta)
    ogloszenie_ct = ContentType.objects.get_for_model(Ogloszenie)

    # 1. Grupa: Administratorzy - pełny dostęp (wszystkie uprawnienia)
    admin_group, _ = Group.objects.get_or_create(name="Administratorzy")
    all_permissions = Permission.objects.filter(
        content_type__in=[rejs_ct, zgloszenie_ct, wplata_ct, wachta_ct, ogloszenie_ct]
    )
    admin_group.permissions.set(all_permissions)

    # 2. Grupa: Koordynatorzy Rejsów - zarządzanie rejsami, wachtami, ogłoszeniami
    koordynator_group, _ = Group.objects.get_or_create(name="Koordynatorzy Rejsów")
    koordynator_permissions = Permission.objects.filter(
        content_type__in=[rejs_ct, wachta_ct, ogloszenie_ct]
    )
    koordynator_group.permissions.set(koordynator_permissions)

    # 3. Grupa: Obsługa Zgłoszeń - zarządzanie zgłoszeniami i wpłatami + podgląd rejsów
    obsluga_group, _ = Group.objects.get_or_create(name="Obsługa Zgłoszeń")
    obsluga_permissions = list(
        Permission.objects.filter(content_type__in=[zgloszenie_ct, wplata_ct])
    )
    # Dodaj tylko uprawnienie do podglądu rejsów
    view_rejs_perm = Permission.objects.filter(
        content_type=rejs_ct, codename="view_rejs"
    ).first()
    if view_rejs_perm:
        obsluga_permissions.append(view_rejs_perm)
    obsluga_group.permissions.set(obsluga_permissions)


def remove_user_groups(apps, schema_editor):
    """Usuwa utworzone grupy użytkowników."""
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=["Administratorzy", "Koordynatorzy Rejsów", "Obsługa Zgłoszeń"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rejs", "0011_zgloszenie_rola_alter_rejs_do_alter_rejs_koniec_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # Poprawka statusów zgłoszenia
        migrations.AlterField(
            model_name="zgloszenie",
            name="status",
            field=models.CharField(
                choices=[
                    ("QUALIFIED", "Zakwalifikowany"),
                    ("NOT_QUALIFIED", "Niezakwalifikowany"),
                    ("ODRZUCONE", "Odrzucone"),
                ],
                default="NOT_QUALIFIED",
                max_length=20,
            ),
        ),
        # Poprawka rodzajów wpłat
        migrations.AlterField(
            model_name="wplata",
            name="rodzaj",
            field=models.CharField(
                choices=[("wplata", "Wpłata"), ("zwrot", "Zwrot")],
                default="wplata",
                max_length=7,
            ),
        ),
        # Poprawka verbose_name dla Wachta
        migrations.AlterModelOptions(
            name="wachta",
            options={"verbose_name": "Wachta", "verbose_name_plural": "Wachty"},
        ),
        # Utworzenie grup użytkowników
        migrations.RunPython(create_user_groups, remove_user_groups),
    ]
