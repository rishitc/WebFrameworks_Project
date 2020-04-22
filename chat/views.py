from django.shortcuts import render,redirect
from .models import Feedback
from .forms import FeedbackForm
from django.contrib.auth.forms import UserCreationForm
def testimonials(request,pk):
    posts=Feedback.objects.filter(pk=pk)
    return render(request, 'chat/testimonials.html', {'posts':posts})

def feedback(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('testimonials', pk=post.pk)
    else:
        form = FeedbackForm()
    return render(request, 'chat/feedback.html', {'form': form})   

def indexView(request):
    return render(request,'chat/index.html')

def homeView(request):
    return render(request,'chat/home.html')

def registerView(request):
    if request.method == "POST":
        form=UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
            form = UserCreationForm()
    return render(request, 'registration/register.html',{'form':form})
