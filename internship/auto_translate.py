import time
import polib # type: ignore
from django.core.management.base import BaseCommand 
from deep_translator import GoogleTranslator # type: ignore

class Command(BaseCommand):
    help = 'Automatically translates empty msgstr in .po files using Google Translate'

    def add_arguments(self, parser):
        parser.add_argument('lang', type=str, help='Target language code (e.g., gu)')

    def handle(self, *args, **options):
        # --- VERIFICATION PRINT ---
        self.stdout.write(self.style.SUCCESS("--- NEW CODE IS RUNNING ---"))
        self.stdout.write(self.style.SUCCESS("If you see this, the fix is applied."))

        target_lang = options['lang']
        po_file_path = f'locale/{target_lang}/LC_MESSAGES/django.po'

        # 1. LOAD FILE
        try:
            po = polib.pofile(po_file_path)
            self.stdout.write(f'Loaded: {po_file_path}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not find file: {po_file_path}. Error: {e}'))
            return

        # 2. SETUP TRANSLATOR
        translator = GoogleTranslator(source='auto', target=target_lang)
        count = 0
        total = len(po)
        self.stdout.write(f"Scanning {total} entries...")

        # 3. TRANSLATE LOOP
        for entry in po:
            # Check if translation is missing (empty msgstr) and original text exists (msgid)
            if not entry.msgstr and entry.msgid:
                try:
                    translation = translator.translate(entry.msgid)
                    
                    if translation:
                        entry.msgstr = translation
                        count += 1
                        # Safe printing
                        try:
                            self.stdout.write(f"Translated: {entry.msgid} -> {translation}")
                        except:
                            pass
                    else:
                        entry.msgstr = "" # Fallback
                        
                    # SLEEP is important to prevent blocking/hanging
                    time.sleep(0.5) 
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error on '{entry.msgid}': {e}"))
                    entry.msgstr = ""

        # 4. FINAL SAFETY FIX (Prevents the 'NoneType' Crash)
        # This loop runs before saving to ensure NO entry is None.
        fixed_count = 0
        for entry in po:
            if entry.msgstr is None:
                entry.msgstr = ""
                fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(self.style.WARNING(f"Fixed {fixed_count} entries to prevent crash."))

        # 5. SAVE FILE
        self.stdout.write("Saving file...")
        try:
            po.save()
            self.stdout.write(self.style.SUCCESS(f'Done! Translated {count} new entries.'))
            self.stdout.write(self.style.WARNING('Run "python manage.py compilemessages" to apply.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical Error Saving: {e}"))