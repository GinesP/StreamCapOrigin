import flet as ft


class ShowSnackBar:
    def __init__(self, page):
        self.page = page

    async def show_snack_bar(self, message, bgcolor=None, duration=1500, action=None, emoji=None,
                             show_close_icon=False):
        """Helper method to show a snack bar with optional emoji."""
        formatted_message = f"{emoji} {message}" if emoji else message

        snack_bar = ft.SnackBar(
            content=ft.Text(formatted_message),
            behavior=ft.SnackBarBehavior.FLOATING,
            action=action,
            bgcolor=bgcolor,
            duration=duration,
            margin=ft.margin.only(left=self.page.width - 300, top=0, right=10, bottom=10),
            show_close_icon=show_close_icon
        )

        snack_bar.open = True
        self.page.snack_bar_area.content = snack_bar
        self.page.update()
