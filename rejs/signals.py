from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.shortcuts import reverse
from .models import Zgloszenie, Wplata, Finanse, Info
from .mailers import send_simple_mail
from django.template.loader import render_to_string

@receiver(pre_save, sender=Zgloszenie)
def zgloszenie_pre_save(sender, instance, **kwargs):
	if not instance.pk:
		instance._old_status = None
		instance._old_wachta_id = None
	else:
		try:
			old = Zgloszenie.objects.get(pk=instance.pk)
			instance._old_status = old.status
			instance._old_wachta_id = old.wachta_id
		except Zgloszenie.DoesNotExist:
			instance._old_status = None
			instance._old_wachta_id = None


@receiver(post_save, sender=Zgloszenie)
def zgloszenie_post_save(sender, instance, created, **kwargs):
	if created:
		subject = f"Potwierdzenie zgłoszenia na rejs: {instance.rejs.nazwa}"
		context = {"zgl": instance,
			 "rejs": instance.rejs,
			 "link": instance.get_absolute_url() if hasattr(instance, 'get_absolute_url') else None,}
		send_simple_mail(subject, instance.email, "emails/zgloszenie_created", context)
		return
	old_status = getattr(instance, "_old_status", None)
	if old_status is not None and old_status != instance.status:
		subject = f"zmiana statusu zgłoszenia {instance.rejs.nazwa}"
		context = {"zgl": instance,
			 "old_status": old_status,
			 "new_status": instance.status,
			 "link": f"{'http://localhost:8000'}" + reverse("zgloszenie_details", kwargs={"token": instance.token}),
			 }
		send_simple_mail(subject, instance.email, "emails/status_changed", context)
	old_wachta_id = getattr(instance, "_old_wachta_id", None)
	if old_wachta_id is None and instance.wachta_id is not None:
		subject = f"dodano do wachty {instance.wachta.nazwa}"
		context = {
			"zgl": instance,
			"wachta": instance.wachta,
			"link": f"{'http://localhost:8000'}" + reverse("zgloszenie_details", kwargs={"token": instance.token}),
		}
		send_simple_mail(subject, instance.email, "emails/wachta_added", context)

@receiver(post_save, sender=Wplata)
def wplata_post_save(sender, instance, created, **kwargs):
	if not created:
		return
	finanse = instance.finanse
	zgl = finanse.zgloszenie
	subject = f"potwierdzenie wpłaty {zgl.imie} {zgl.nazwisko}"
	context = {
		"zgl": zgl,
		"wplata": instance,
		"finanse": finanse,
		"link": f"{'http://localhost:8000'}" + reverse("zgloszenie_details", kwargs={"token": zgl.token}),
	}
	send_simple_mail(subject, zgl.email, 'emails/wplata_created', context)


@receiver(post_save, sender=Zgloszenie)
def utworz_finanse_dla_zgloszenia(sender, instance, created, **kwargs):
	if created and not hasattr(instance, "finanse"):
		Finanse.objects.create(zgloszenie=instance, kwota_do_zaplaty=instance.rejs.cena)

