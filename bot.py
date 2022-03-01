from secrets import token_hex

from pyrogram import Client, filters

from models import Post
from config import api_id, api_hash, token, admin_id

stating = {}
spammer = Client("bot_spammer", api_id=api_id, api_hash=api_hash, parse_mode="html")
app = Client(
    "bot_app", api_id=api_id, api_hash=api_hash, bot_token=token, parse_mode="html"
)


def admin_filter(_, __, message):
    return message.from_user.id == admin_id


def finite_state_machine(data: str = None):
    def func(flt, __, message):
        if message.from_user.id not in stating:
            stating[message.from_user.id] = {"state": "*", "data": {}}

        return stating[message.from_user.id]["state"] == flt.data

    return filters.create(func, data=data)


def clear_state(user_id):
    stating[user_id] = {"state": "*", "data": {}}


static_admin_filter = filters.create(admin_filter)


@app.on_message(filters.command(["start", "help"]) & filters.private)
def welcome_handler(client, message):
    client.send_message(
        message.from_user.id,
        "<b>Привет, я просто бот для автопостинга!</b>\nСоздатель 👉 @motion_donik",
    )


@app.on_message(filters.command(["all"]) & static_admin_filter & filters.private)
def get_all_posts(client, message):
    client.send_message(
        message.from_user.id,
        "Все чаты по которым идет рассылка!\n"
        + "\n".join([f"{p.id}, {p.chat_id}, {p.timer} секунд" for p in Post.select()]),
    )


@app.on_message(filters.command(["go"]) & static_admin_filter & filters.private)
def invite_self_chat(client, message):
    payload = message.text.split(" ")
    if len(payload) == 2:
        chat = spammer.join_chat(payload[1])
        if chat:
            client.send_message(message.from_user.id, "Успешно вступил в чат!")
        else:
            client.send_message(message.from_user.id, "В этот чат не получилось войти!")
    else:
        client.send_message(
            message.from_user.id, "Неправильный ввод команды, пример /go t.me/uzbdesignerszone"
        )


@app.on_message(
    filters.command(["post", "posting"]) & static_admin_filter & filters.private,
)
def add_posting(client, message):
    payload = message.text.split(" ")
    if len(payload) == 3:
        try:
            peer = payload[1]  # spammer.resolve_peer(payload[1])
            stating[message.from_user.id] = {
                "state": "post",
                "data": {
                    "chat_id": peer,
                    "timer": int(payload[2]),
                },
            }
        except ValueError:
            client.send_message(
                message.from_user.id, "/post Число Число, обязательно числом!"
            )
        except KeyError:
            client.send_message(
                message.from_user.id, "Чат с таким айди в аккаунте не найден!"
            )
        else:
            client.send_message(
                message.from_user.id, "Хорошо, отправь пост для публикации!"
            )
    else:
        client.send_message(
            message.from_user.id,
            "Неправильный ввод команды, пример /post Айди-чата Секунды",
        )


@app.on_message(finite_state_machine("post") & filters.private)
def second_state_posting(client, message):
    data = stating[message.chat.id]["data"]
    post = Post(
        chat_id=data["chat_id"],
        timer=data["timer"],
        image=None,  # for or operator
        video=None,  # for or operator
    )  # just create object

    if message.media:
        post.text = message.caption.html
    else:
        post.text = message.text.html

    if message.photo:
        post.image = f"media/post{token_hex(8)}.jpg"
        client.download_media(message, post.image)
    elif message.video:
        post.video = f"media/post{token_hex(8)}.mp4"
        client.download_media(message, post.video)

    post.save()  # save in db

    kwargs_dict = {
        "chat_id": message.from_user.id,
        "text": "<b>Успешно сохранил!</b> 👍🏼\n\n"
        f"Чат: <code>{post.chat_id}</code>\n"
        f"Медиа: <code>{post.image or post.video or 'Нету'}</code>\n"
        f"Таймер: {post.timer} секунд\n\n{post.text}",
    }

    if post.image:
        kwargs_dict["photo"] = post.image
        kwargs_dict["caption"] = kwargs_dict["text"]
        del kwargs_dict["text"]
        client.send_photo(**kwargs_dict)
    elif post.video:
        kwargs_dict["video"] = post.video
        kwargs_dict["caption"] = kwargs_dict["text"]
        del kwargs_dict["text"]
        client.send_video(**kwargs_dict)
    else:
        client.send_message(**kwargs_dict)

    clear_state(message.from_user.id)  # clear fsm state


if __name__ == "__main__":
    from pyrogram.session import Session

    Session.notice_displayed = True  # hacking copyright...

    spammer.start()
    app.run()
