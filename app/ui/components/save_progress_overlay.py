import flet as ft


class SaveProgressOverlay:
    def __init__(self, app):
        self.app = app
        self._ = {}
        self.load()
        self.overlay = ft.Stack(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressRing(
                                width=50, 
                                height=50, 
                                stroke_width=5,
                                color=ft.colors.BLUE_400,
                                value=0.7
                            ),
                            ft.Text(self._["saving_recording"], size=16, weight=ft.FontWeight.W_500)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    bgcolor=ft.colors.with_opacity(0.7, ft.colors.BLACK),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        color=ft.colors.with_opacity(0.2, ft.colors.BLACK),
                        offset=ft.Offset(0, 4)
                    ),
                    animate_opacity=300,
                    animate_scale=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
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

    def load(self):
        """Load language resources."""
        self._ = self.app.language_manager.language.get("progress_overlay", {})

    @property
    def visible(self):
        return self.overlay.visible
