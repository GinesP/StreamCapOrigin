import flet as ft


class ProgressOverlay:
    def __init__(self):
        self.overlay = ft.Stack(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressRing(width=50, height=50, stroke_width=5),
                            ft.Text("正在停止录制并保存...", size=16)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    bgcolor=ft.colors.with_opacity(0.5, ft.colors.WHITE)
                )
            ],
            visible=False
        )

    def show(self):
        self.overlay.visible = True
        self.overlay.update()

    def hide(self):
        self.overlay.visible = False
        self.overlay.update()

    @property
    def visible(self):
        return self.overlay.visible
