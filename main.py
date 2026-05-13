import time
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

class ShieldSyncApp(App):
    def build(self):
        self.store = JsonStore('shield_config.json')
        
        # Standardwerte laden, falls nicht gesetzt
        if not self.store.exists('settings'):
            self.store.put('settings', gist_id="8a31394fb00ddee15af6176caab86c2e", token="DEIN_TOKEN", render_url="onrender.com")

        config = self.store.get('settings')

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # UI Elemente
        layout.add(Label(text="🛡️ SHIELD TITAN MOBILE GATE", font_size=20, size_hint_y=None, height=40))
        
        self.lbl_status = Label(text="Status: Bereit", halign="center")
        layout.add(self.lbl_status)

        self.txt_token = TextInput(text=config['token'], hint_text="GitHub Token", password=True, multiline=False)
        layout.add(self.txt_token)

        self.txt_render = TextInput(text=config['render_url'], hint_text="Render URL", multiline=False)
        layout.add(self.txt_render)

        # Manuelle Trigger Knöpfe
        btn_render = Button(text="Render wachhalten (Manual)", on_press=self.ping_render)
        btn_sync = Button(text="Gist & IP jetzt synchronisieren", on_press=self.manual_sync)
        layout.add(btn_render)
        layout.add(btn_sync)

        # Automatische Timer starten
        Clock.schedule_interval(self.ping_render, 180) # 3 Minuten
        Clock.schedule_interval(self.manual_sync, 600)  # 10 Minuten

        return layout

    def ping_render(self, instance=None):
        url = self.txt_render.text
        try:
            res = requests.get(url, timeout=5)
            self.lbl_status.text = f"Status: Render angepingt ({res.status_code})"
        except Exception as e:
            self.lbl_status.text = f"Status: Ping Fehler: {str(e)[:30]}"

    def manual_sync(self, instance=None):
        self.lbl_status.text = "Status: Synchronisiere..."
        token = self.txt_token.text
        gist_id = self.store.get('settings')['gist_id']
        
        # Einstellungen speichern
        self.store.put('settings', gist_id=gist_id, token=token, render_url=self.txt_render.text)

        try:
            # Aktuelle IP holen
            current_ip = requests.get("ipify.org", timeout=5).text.strip()
            
            # Gist holen
            headers = {"Authorization": f"token {token}"}
            url = f"github.com{gist_id}"
            res = requests.get(url, headers=headers, timeout=5).json()
            
            filename = list(res['files'].keys())[0]
            remote_ips = [ip.strip() for ip in res['files'][filename]['content'].split('\n') if ip.strip()]

            if current_ip not in remote_ips:
                remote_ips.append(current_ip)
                new_content = "\n".join(remote_ips)
                payload = {"files": {filename: {"content": new_content}}}
                requests.patch(url, headers=headers, json=payload, timeout=5)
                self.lbl_status.text = f"Status: IP {current_ip} hinzugefügt!"
            else:
                self.lbl_status.text = "Status: IP bereits im Gist."
        except Exception as e:
            self.lbl_status.text = f"Status: Sync Fehler: {str(e)[:30]}"

if __name__ == '__main__':
    ShieldSyncApp().run()
