from django.shortcuts import get_object_or_404, redirect, render

from .forms import ZgloszenieForm
from .models import Rejs, Zgloszenie


def index(request):
    rejsy = Rejs.objects.all().order_by("od")
    return render(request, "rejs/index.html", {"rejsy": rejsy})


def zgloszenie_utworz(request, rejs_id):
    rejs = get_object_or_404(Rejs, id=rejs_id)
    if request.method == "POST":
        form = ZgloszenieForm(request.POST)
        if form.is_valid():
            zgl = form.save(commit=False)
            zgl.rejs = rejs
            zgl.save()
            return redirect("zgloszenie_details", token=zgl.token)
    else:
        form = ZgloszenieForm()

    return render(request, "rejs/zgloszenie_form.html", {"form": form, "rejs": rejs})


def zgloszenie_details(request, token):
    zgloszenie = get_object_or_404(Zgloszenie, token=token)
    return render(request, "rejs/zgloszenie_details.html", {"zgloszenie": zgloszenie})
