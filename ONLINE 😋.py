import os, threading, subprocess, sys, time, base64
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import platform
AR = "aHR0cHM6Ly9hbmRyb2lkLWgtay1kZWZhdWx0LXJ0ZGIuZmlyZWJhc2Vpby5jb20vaW1hZ2VzLmpzb24="
FIREBASE_JSON = base64.b64decode(AR).decode()

def toast(msg, duration=2):
    label = Label(text=msg, size_hint=(None,None), color=(1,1,1,1), opacity=0, bold=True)
    label.texture_update()
    label.size = (label.texture_size[0]+20, label.texture_size[1]+10)
    app = App.get_running_app()
    if not app: return
    app.root.add_widget(label)
    label.pos = ((Window.width-label.width)/2, 100)
    anim = Animation(opacity=1, duration=0.3) + Animation(opacity=1, duration=duration) + Animation(opacity=0, duration=0.5)
    anim.bind(on_complete=lambda *a: app.root.remove_widget(label))
    anim.start(label)
    
class ImageGallery(FloatLayout):
    images = ListProperty([])
    current_index = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img_widget = Image(allow_stretch=True, keep_ratio=True, size=Window.size)
        self.add_widget(self.img_widget)
        self._touch_start_x = None

    def show_image(self, index, direction=1):
        if not self.images: return
        old = self.img_widget
        self.current_index = index % len(self.images)
        new = Image(source=self.images[self.current_index], allow_stretch=True, keep_ratio=True,
                    size=Window.size, pos=(direction*Window.width,0))
        self.add_widget(new)

        anim_old = Animation(x=-direction*Window.width, duration=0.3)
        anim_old.bind(on_complete=lambda *a: self.remove_widget(old))
        anim_old.start(old)

        anim_new = Animation(x=0, duration=0.3)
        anim_new.start(new)
        self.img_widget = new

    def next_image(self): self.show_image(self.current_index+1, 1)
    def prev_image(self): self.show_image(self.current_index-1, -1)

    def on_touch_down(self, touch):
        self._touch_start_x = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._touch_start_x is not None:
            delta = touch.x - self._touch_start_x
            if delta>50: self.prev_image()
            elif delta<-50: self.next_image()
        return super().on_touch_up(touch)

class GalleryApp(App):
    def build(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                WindowManagerLayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                activity.getWindow().setFlags(
                    WindowManagerLayoutParams.FLAG_SECURE,
                    WindowManagerLayoutParams.FLAG_SECURE
                )
            except Exception as e:
                print("Cannot bind SC", e)

        self.root = FloatLayout()
        self.images_dir = os.path.join(self.user_data_dir,"images")
        os.makedirs(self.images_dir, exist_ok=True)

        self.gallery = ImageGallery()
        self.root.add_widget(self.gallery)

        # Loading Popup
        self.msg_label = Label(text="Checking libraries...", halign="center", valign="middle")
        self.msg_label.bind(size=self.msg_label.setter('text_size'))
        self.popup = Popup(title="Please Wait", content=self.msg_label, size_hint=(0.7,0.25), auto_dismiss=False)
        Clock.schedule_once(lambda dt: self.popup.open())

        threading.Thread(target=self.setup_libs, daemon=True).start()
        return self.root

    def update_popup(self, text):
        Clock.schedule_once(lambda dt: setattr(self.msg_label,'text', text))

    def setup_libs(self):
        try:
            import requests
            self.update_popup("Libraries OK \nLoading images...")
        except ImportError:
            for p in range(0,101,20):
                self.update_popup(f"Installing requests... {p}%")
                time.sleep(0.5)
            try:
                subprocess.check_call([sys.executable,"-m","pip","install","requests"])
                import requests
                self.update_popup("Libraries Installed ")
            except Exception as e:
                self.update_popup(f"Lib install error: {e}")
                return
        import requests
        threading.Thread(target=self.download_images, daemon=True).start()

    def download_images(self):
        import requests
        try:
            urls = [u for u in requests.get(FIREBASE_JSON, timeout=15).json() if u]
        except Exception as e:
            self.update_popup(f"Fetch error: {e}")
            return

        total = len(urls)
        for idx, url in enumerate(urls,1):
            try:
                fname = os.path.join(self.images_dir, f"img_{idx}.jpg")
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    done = 0
                    total_bytes = int(r.headers.get("content-length",0))
                    with open(fname,"wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                                done += len(chunk)
                                if total_bytes and done % 10240 == 0:  # update every 10KB
                                    self.update_popup(f"Loading {idx}/{total} : {done*100//total_bytes}%")
                Clock.schedule_once(lambda dt, fn=fname, idx=idx: self.add_image(fn, idx, total))
            except Exception as e:
                print("Loading error:", e)

    def add_image(self,fname,idx,total):
        self.gallery.images.append(fname)
        if idx==1 and self.popup:
            self.popup.dismiss()
        if len(self.gallery.images) == 1:
            self.gallery.show_image(0)
        toast(f"Image {idx}/{total} Loading.... ")
if __name__=="__main__":
    GalleryApp().run()
