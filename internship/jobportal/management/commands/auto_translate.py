import time
import polib
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator

class Command(BaseCommand):
    help = 'Automatically translates empty msgstr in .po files'

    def add_arguments(self, parser):
        parser.add_argument('lang', type=str, help='Target language code (e.g., gu)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- RUNNING FIXED CODE ---"))
        target_lang = options['lang']
        po_file_path = f'locale/{target_lang}/LC_MESSAGES/django.po'

        # 1. LOAD FILE
        try:
            po = polib.pofile(po_file_path)
            self.stdout.write(f'Loaded: {po_file_path}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading file: {e}'))
            return

        # 2. SETUP TRANSLATOR
        translator = GoogleTranslator(source='auto', target=target_lang)
        self.stdout.write(f"Scanning {len(po)} entries...")

        # 3. TRANSLATE
        for entry in po:
            if not entry.msgstr and entry.msgid:
                try:
                    res = translator.translate(entry.msgid)
                    if res:
                        entry.msgstr = res
                        self.stdout.write(f"Translated: {entry.msgid[:20]}...")
                    else:
                        entry.msgstr = "" 
                    time.sleep(0.5)
                except:
                    entry.msgstr = ""

        # 4. *** THE CLEANING LOOP (CRITICAL FIX) ***
        # This prevents the "NoneType" crash you are seeing
        count_fixed = 0
        for entry in po:
            if entry.msgstr is None:
                entry.msgstr = ""
                count_fixed += 1
        
        if count_fixed > 0:
            self.stdout.write(self.style.WARNING(f"Fixed {count_fixed} broken entries."))

        # 5. SAVE
        self.stdout.write("Saving file...")
        po.save()
        self.stdout.write(self.style.SUCCESS("Done! Run 'python manage.py compilemessages'"))