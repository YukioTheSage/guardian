from django.shortcuts import render


def landing_page(request):
    return render(request, "shieldid/landing.html")


def registration_page(request):
    return render(request, "shieldid/register.html")


def verification_page(request):
    return render(request, "shieldid/verify.html")


def edtech_demo_page(request):
    return render(request, "shieldid/edtech_demo.html")


def dashboard_page(request):
    return render(request, "shieldid/dashboard.html")
