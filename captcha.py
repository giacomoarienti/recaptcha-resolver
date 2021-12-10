import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import speech_recognition as sr
from pydub import AudioSegment
import os
import time

class Captcha(object):
    class SpeechToTex(object):
        OUTPUT_FILE = "result_tmp.wav"

        def __init__(self, file: str) -> None:
            super().__init__()
            self.file = file.rstrip()
            self.audio_input = ""

        def convert_file(self) -> bool:
            try:
                self.file = os.getcwd() + "/" + self.file
                sound = AudioSegment.from_mp3(self.file)
                sound.export(self.OUTPUT_FILE, format="wav")
                self.audio_input = os.getcwd() + "/" + self.OUTPUT_FILE

                return True
            except:
                return False

        def remove_file(self) -> None:
            os.remove(os.getcwd() + "/" + self.OUTPUT_FILE)

        def speach_to_text(self) -> str:
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(self.audio_input) as source:
                    audio = recognizer.record(source)

                audio_output = ""
                audio_output = recognizer.recognize_google(audio)
            except:
                return ""

            return audio_output

        def start(self) -> str:
            if(not self.convert_file()):
                #print("[!] Failed to convert file")
                return ""

            str = self.speach_to_text()
            self.remove_file()
            return str

    class Downloader(object):
        def __init__(self, url: str, ofile="audio.mp3") -> None:
            super().__init__()
            self.url = url
            self.ofile = ofile

        def start(self) -> None:
            resp = ""
            try:
                resp = requests.get(self.url)
            except:
                #print("[!] Failed to download file !")
                return

            if resp.status_code != 200:
                #print("[!] Failed to download file !")
                return

            with open(self.ofile, 'wb') as f:
                f.write(resp.content)
            #print("[+] File downloaded !")

        def remove_file(self) -> None:
            os.remove(os.getcwd() + "/" + self.ofile)

    def __init__(self, url: str, proxy="", method="audio", headless=True, debug=False) -> None:
        super().__init__()
        self.url = url
        self.proxy = proxy
        self.method = method
        self.debug = debug
        self.headless = headless

        self.frame = None

        self.init_browser()
        self.init_action()

    def print_dbg(self, str) -> None:
        if self.debug:
            print(str)

    def init_browser(self) -> None:
        chrome_options = webdriver.chrome.options.Options()
        chrome_options.add_argument("--disable-gpu")
        if(self.proxy != ""):
            chrome_options.add_argument(f'--proxy-server=http://{self.proxy}')
        chrome_options.headless = self.headless
        self.browser = webdriver.Chrome(options=chrome_options)

    def init_action(self) -> None:
        self.action = webdriver.ActionChains(self.browser)

    def find_element_by_css_selector_timeout(self, selector: str, timeout=10) -> any:
        timeout += time.time()
        while time.time() < timeout:
            try:
                element = (self.browser).find_element(By.CSS_SELECTOR, selector)
                return element
            except:
                pass
        return None

    def find_elements_by_css_selector_timeout(self, selector: str, timeout=10) -> any:
        timeout += time.time()
        while time.time() < timeout:
            try:
                element = (self.browser).find_elements(By.CSS_SELECTOR, selector)
                return element
            except:
                pass
        return None

    def connect(self) -> bool:
        try:
            (self.browser).get(self.url)
            return True
        except:
            return False

    def get_captcha(self) -> None:
        try:
            frames = self.find_elements_by_css_selector_timeout("iframe")
            for frame in frames:
                if "https://google.com/recaptcha/api2/" in frame.get_attribute('src'):
                    self.frame = frame
                    return
            return
        except:
            return

    def get_token(self) -> str:
        try:
            (self.browser).switch_to.frame(self.frame)
            token = self.find_element_by_css_selector_timeout(
                "#recaptcha-token")
            return token.get_attribute('value')
        except Exception as e:
            self.print_dbg(e)
            return None

    def click_solve(self) -> bool:
        try:
            (self.browser).switch_to.default_content()
            (self.browser).switch_to.frame(self.frame)

            button = self.find_element_by_css_selector_timeout(
                '#recaptcha-anchor')
            button.click()

            return True
        except:
            return False

    def click_audio(self) -> bool:
        try:
            (self.browser).switch_to.default_content()
            self.frame = self.find_element_by_css_selector_timeout(
                "iframe[title='recaptcha challenge']")
            (self.browser).switch_to.frame(self.frame)

            button = self.find_element_by_css_selector_timeout(
                '#recaptcha-audio-button')
            button.click()

            return True
        except:
            return False

    def get_audio_link(self) -> str:
        try:
            (self.browser).switch_to.default_content()
            self.frame = self.find_element_by_css_selector_timeout(
                "iframe[title='recaptcha challenge']")
            (self.browser).switch_to.frame(self.frame)

            link = self.find_element_by_css_selector_timeout(
                '.rc-audiochallenge-tdownload-link')
            if(not link):
                return None

            link = link.get_attribute('href')
            return link
        except Exception as e:
            self.print_dbg(e)
            return None

    def send_audio_response(self, text: str) -> None:
        try:
            (self.browser).switch_to.default_content()
            (self.browser).switch_to.frame(self.frame)

            input = self.find_element_by_css_selector_timeout(
                '#audio-response')
            input.send_keys(text)

            self.find_element_by_css_selector_timeout(
                "#recaptcha-verify-button").click()

            return
        except:
            return

    def check_error_message(self) -> bool:
        try:
            (self.browser).switch_to.default_content()
            (self.browser).switch_to.frame(self.frame)

            error = self.find_element_by_css_selector_timeout(
                '.rc-audiochallenge-error-message')
            display = error.value_of_css_property("display")
            if(display == "hidden" or display == "none"):
                return False

            return True
        except:
            return False

    def is_solved(self):
        try:
            (self.browser).switch_to.default_content()
            (self.browser).switch_to.frame(self.frame)

            error = self.find_element_by_css_selector_timeout(
                '.recaptcha-checkbox-checkmark')
            if(error.value_of_css_property("display") == ""):
                return True

            return False
        except:
            return False

    def audio_method(self):
        if(not self.click_audio()):
            self.print_dbg("[!] Failed to use audio method")
            return

        i = 1
        while(1):
            self.print_dbg(f"\n{i}° cicle:")

            audio = self.get_audio_link()
            if(not audio):
                self.print_dbg("[!] Cannot get Audio Link !")
                return
            self.print_dbg("[+] Got Audio Link")

            download = self.Downloader(audio)
            download.start()

            resp = self.SpeechToTex("audio.mp3").start()
            download.remove_file()
            if(resp == ""):
                self.print_dbg("[!] Failed to parse audio text")
                return
            self.print_dbg("[+] Audio correctly parsed !")

            self.send_audio_response(resp)

            if(not self.check_error_message()):
                break

            if(self.is_solved()):
                break

            i += 1

    def start(self):
        if(not self.connect()):
            self.print_dbg("[!] Failed to connect to the website !")
            return
        self.print_dbg("[+] Connected")

        self.get_captcha()
        if(not self.frame):
            self.print_dbg("[!] Cannot find ReCAPTCHA !")
            return
        self.print_dbg("[+] ReCAPTCHA found")

        token = self.get_token()
        if(not token):
            self.print_dbg("[!] Cannot get Token !")
            return
        self.print_dbg("[+] Got Token")

        if(not self.click_solve()):
            self.print_dbg("[!] Failed to solve capthca !")
            return

        if(self.method == "audio"):
            self.audio_method()
        elif(self.method == "images"):
            self.print_dbg("[!] Method not implemented yet !")
            return
        else:
            self.print_dbg(f"[!] Method {self.method} not found !")
            return

        cookies = (self.browser).get_cookies()

        self.print_dbg("\n[+] Captcha solved")
        self.print_dbg(f"Cookies: {cookies}")
        (self.browser).quit()

        return cookies


Captcha(
    url="https://google.com/recaptcha/api2/demo",
    proxy="",

    method="audio",
    headless=True,

    debug=True
).start()
