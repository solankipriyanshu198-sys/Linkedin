#!/usr/bin/env python
import sys

with open('jobportal/models.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')
    
    # Find MessageThread
    for i, line in enumerate(lines):
        if 'class MessageThread' in line:
            print(f"Found MessageThread at line {i+1}")
            for j in range(max(0, i-3), min(len(lines), i+15)):
                print(f"{j+1:3d}: {lines[j]}")
            break
    else:
        print("MessageThread not found!")

    # Try to import and see what happens
    try:
        import django
        django.setup()
        from jobportal.models import MessageThread
        print("Successfully imported MessageThread")
    except Exception as e:
        print(f"Error importing: {e}")
        import traceback
        traceback.print_exc()
