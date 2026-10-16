"""Диагностика старта Ио: видно, на каком шаге падает запуск."""
import os, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))


def _save_log(text):
    for p in [os.path.join(HERE, "io_crash.log"),
              "/storage/emulated/0/Download/io_crash.log"]:
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(text)
            return p
        except Exception:
            pass
    return None


def _toast(msg):
    try:
        from jnius import autoclass
        Toast = autoclass("android.widget.Toast")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Toast.makeText(PythonActivity.mActivity, msg, 1).show()
    except Exception:
        pass


def main():
    import importlib
    from kivy.app import App as KApp
    from kivy.uix.label import Label
    from kivy.clock import Clock

    steps = ["planet", "physics", "mathmind", "sciences",
             "neurobrain", "subconscious", "world", "fetch_library", "iomap"]
    done = []

    class DiagApp(KApp):
        def build(self):
            self.lab = Label(text="Ио: диагностика старта",
                             font_size="15sp", halign="left", valign="top")
            self.lab.bind(size=self.lab.setter("text_size"))
            Clock.schedule_once(self._run, 1)
            return self.lab

        def _run(self, dt):
            for name in steps:
                try:
                    importlib.import_module(name)
                    done.append("ok: " + name)
                except Exception:
                    err = "ПАДАЕТ на импорте: %s\n\n%s" % (
                        name, traceback.format_exc())
                    _save_log("\n==== " + err + "\n")
                    _toast("Ио упал: " + name)
                    self.lab.text = err[:4000]
                    return
            self.lab.text = ("все %d импортов прошли —\n"
                             "проблема не в модулях,\n"
                             "присылайте adb logcat" % len(steps))
            _toast("Ио: все импорты ок")

    DiagApp().run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        _save_log("\n==== старт\n" + err)
        _toast("Ио упал до интерфейса")
        sys.stderr.write(err)
