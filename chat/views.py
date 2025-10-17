from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required # 로그인한 사용자만 접근 가능하도록 설정
def chat_room(request, other_user_id):
    return render(request, 'chat/chat_room.html', {
        'other_user_id': other_user_id
    })
