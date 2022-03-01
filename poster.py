from os import link
from time import sleep
from config import api_id, api_hash, token, admin_id

from pyrogram import Client
from pyrogram.errors import RPCError

from models import Post, datetime_now

spammer = Client("poster_spammer", api_id=api_id, api_hash=api_hash, parse_mode="html")


class Poster:
    """
    Arguments:
        client - pyrogram Client
        event - threading Event
    """

    def __init__(self, client, sleep=15):
        self.client = client
        self._work = False
        self._update_time = sleep

        client.start()

    def run(self):
        self.start()

        while self.working:
            for post in Post.select():
                if post.timer <= (datetime_now() - post.last_timer).total_seconds():
                    try:
                        if getattr(post, "image", None) is not None:
                            msg = self.client.send_photo(
                                post.chat_id, post.image, caption=post.text
                            )
                        elif getattr(post, "video", None) is not None:
                            msg = self.client.send_video(
                                post.chat_id, post.video, caption=post.text
                            )
                        else:
                            msg = self.client.send_message(post.chat_id, post.text)

                        post.last_timer = datetime_now()
                        post.save()
                        # maybe send as bot not as user account saved
                        self.client.send_message(
                            admin_id,
                            f"Автопостинг: Отправил <a href={msg.link}"
                            f">пост в {post.chat_id}</a>",
                        )
                    except RPCError as ex:
                        print(ex)

            sleep(self._update_time)

    @property
    def working(self) -> bool:
        return self._work

    def start(self):
        self._work = True

    def stop(self):
        self._work = False


if __name__ == "__main__":
    from pyrogram.session import Session

    Session.notice_displayed = True  # hacking copyright...

    poster = Poster(spammer)

    try:
        poster.run()
    except KeyboardInterrupt:
        print("bye)")
