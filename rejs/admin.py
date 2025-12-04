from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Rejs, Zgloszenie, Finanse, Wplata, Wachta, Info


class InfoInline(admin.StackedInline):
	model = Info
	extra = 0

class WachtaForm(forms.ModelForm):
	czlonkowie = forms.ModelMultipleChoiceField(
		Zgloszenie.objects.none(),
		required=False,
		widget=admin.widgets.FilteredSelectMultiple("Członkowie", is_stacked=False)
	)
	class Meta:
		fields = "__all__"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if self.instance and self.instance.pk:
			self.fields['czlonkowie'].queryset = Zgloszenie.objects.filter(rejs=self.instance.rejs)
			self.fields['czlonkowie'].initial = self.instance.czlonkowie.all()
		else:
			rejs_initial = self.initial.get('rejs') or (self.data.get('rejs')if self.data else None) 
			if rejs_initial:
				try:
					self.fields['czlonkowie'].queryset = Zgloszenie.objects.filter(rejs_id=rejs_initial)
				except Exception:
					self.fields['czlonkowie'].queryset = Zgloszenie.Objects.none()
			else:
				self.fields['czlonkowie'].queryset = Zgloszenie.objects.none()
	def save(self, commit=True):
		instance = super().save(commit=commit)
		selected = self.cleaned_data.get('czlonkowie', [])
		current = set(self.instance.czlonkowie.all())
		to_remove = current - set(selected)
		for zg in to_remove:
			zg.wachta = None
			zg.save(update_fields=['wachta'])

		for zg in selected:
			if zg.rejs_id != instance.rejs_id:
				raise forms.ValidationError(f"Zgłoszenie {zg} nie nalezy do rejsu {instance.rejs}")
			zg.wachta = instance
			zg.save(update_fields=['wachta'])
		return instance

#@admin.register(Wachta)
class WachtaAdmin(admin.ModelAdmin):
	form=WachtaForm
	list_display = ('nazwa', 'rejs')
	list_filter = ('rejs', )
	#filter_horizontal = ("czlonkowie", )

class WachtaInline(admin.TabularInline):
	model = Wachta
	extra = 0
	show_change_link = True

class WplataInline(admin.TabularInline):
	model = Wplata
	extra = 0
	readonly_fields = ['data']
	ordering = ['data']

class FinanseInline(admin.StackedInline):
	model = Finanse
	extra = 0
	can_delete = False
	show_change_link = True
	readonly_fields = ['suma_wplat', 'do_zaplaty']
	inlines = WplataInline
	fieldsets = (
		("rozliczenie:", {
			"fields": (
				"kwota_do_zaplaty",
				"suma_wplat",
				"do_zaplaty"
			)
		}),
	)

	def has_add_perrmission(self, request, obj=None):
		return False

class ZgloszenieInline(admin.TabularInline):
	model = Zgloszenie
	extra = 0
	readonly_fields = ['imie', 'nazwisko', 'email', 'telefon']
	show_change_link = True


@admin.register(Rejs)
class RejsyAdmin(admin.ModelAdmin):
	list_display = ['nazwa', 'od', 'do', 'start', 'koniec']
	inlines = [ZgloszenieInline, WachtaInline, InfoInline]

@admin.register(Zgloszenie)
class ZgloszenieAdmin(admin.ModelAdmin):
	list_display = ("id", "imie", "nazwisko", "rejs")
	list_filter = ('rejs', )
	search_fields = ('imie', 'nazwisko')
	inlines = [FinanseInline]
	def link_do_finansow(self, obj):
		if hasattr(obj, 'finanse') and obj.finanse:
			app_label = obj._meta.app_label
			model_name = obj.finanse._meta.model_name
			url = reverse(f"admin:{app_label}_{model_name}_change", args=(obj.finanse.pk,))
			return format_html('<a href="{}">Otwórz finanse</a>', url)

	link_do_finansow.short_description = 'finanse'

@admin.register(Finanse)
class FinanseAdmin(admin.ModelAdmin):
	list_display = ["id", "zgloszenie", "kwota_do_zaplaty", "suma_wplat", "do_zaplaty"]
	inlines = [WplataInline]

@admin.register(Wplata)
class WplataAdmin(admin.ModelAdmin):
	list_display = ["id", "finanse", "kwota", "data"]
	list_filter = ['finanse']
	ordering = ["-data"]
