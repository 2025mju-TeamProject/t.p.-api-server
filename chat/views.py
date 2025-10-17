from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required  # 로그인이 필요한 뷰
def chat_room(request, other_user_id):
    my_id = request.user.id
    if my_id == other_user_id:
        raise Http404("다른 사용자와의 채팅만 지원합니다.")

    room_name = "-".join(sorted([str(my_id), str(other_user_id)]))

    return render(
        request,
        "chat/chat_room.html",
        {
            "other_user_id": other_user_id,
            "room_name": room_name,
        },
    )
