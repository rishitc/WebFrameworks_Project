from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, 'ChatBox/index.html')


def room(request, room_name):
    return render(request, 'ChatBox/room.html', {
        'room_name': room_name
    })
