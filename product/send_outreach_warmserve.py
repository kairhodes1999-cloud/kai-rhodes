#!/usr/bin/env python3
"""Send targeted outreach email to Warmserve Services."""
import sys
sys.path.insert(0, '/home/hermes/kai-rhodes-landing/product')
from email_outreach import send_email_via_api

to = 'enquiries@warmserve-services.co.uk'
subject = 'Quick idea for Warmserve Services'

body_text = '''Hi there,

I noticed Warmserve serves Swansea and Cardiff with plumbing, heating and electrical services.

I build AI chatbots that handle customer inquiries and booking automatically - even outside office hours. A smart chat on your website that answers FAQs, captures job details, and schedules call-outs. Like having a receptionist who never sleeps.

One client went from missing 60% of after-hours enquiries to capturing every single one. Fixed price, delivered in 48 hours.

Want to see a quick demo? Happy to hop on a call and show you what it looks like.

Best,
Kai Rhodes
AI Automation Services'''

body_html = '''<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hi there,</p>
<p>I noticed Warmserve serves Swansea and Cardiff with plumbing, heating and electrical services.</p>
<p>I build <b>AI chatbots</b> that handle customer inquiries and booking automatically - even outside office hours. A smart chat on your website that answers FAQs, captures job details, and schedules call-outs. Like having a receptionist who never sleeps.</p>
<p>One client went from missing 60% of after-hours enquiries to capturing every single one. Fixed price, delivered in 48 hours.</p>
<p>Want to see a quick demo? Happy to hop on a call and show you what it looks like.</p>
<p>Best,<br><b>Kai Rhodes</b><br>AI Automation Services</p></body></html>'''

success = send_email_via_api(to, subject, body_html, body_text)
print(f'Result: {"✅ SENT" if success else "❌ FAILED"}')
