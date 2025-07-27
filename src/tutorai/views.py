from django.shortcuts import redirect


def redirect_to_frontend(request):
    return redirect("http://localhost:8080/courses/")  # Adjust the URL as needed
