#!/usr/bin/env python3
"""Send batch outreach to newly found leads."""
import sys
sys.path.insert(0, '/home/hermes/kai-rhodes-landing/product')
from email_outreach import send_email_via_api

leads = [
    ("info@antlinplumbing.co.uk", "Antlin Plumbing & Heating"),
    ("enquiries@cambrianiplumbing.co.uk", "Cambriani Plumbing"),
    ("enquiries@tjpelectrical.co.uk", "TJP Electrical"),
]

body_text = '''Hi there,

I noticed your business serves customers in South Wales.

I build AI chatbots that handle customer enquiries automatically — even outside office hours. A smart chat on your website that answers FAQs, captures job details, and books appointments. Like having a receptionist who never misses a call.

One client went from missing 60% of after-hours enquiries to capturing every single one. Fixed price, delivered in 48 hours.

If that sounds useful, reply here and I'll send over a demo link. No call needed.

Best,
Kai Rhodes
AI Automation Services'''

body_html = '''<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hi there,</p>
<p>I noticed your business serves customers in South Wales.</p>
<p>I build <b>AI chatbots</b> that handle customer enquiries automatically — even outside office hours. A smart chat on your website that answers FAQs, captures job details, and books appointments. Like having a receptionist who never misses a call.</p>
<p>One client went from missing 60% of after-hours enquiries to capturing every single one. Fixed price, delivered in 48 hours.</p>
<p>If that sounds useful, reply here and I'll send over a demo link. No call needed.</p>
<p>Best,<br><b>Kai Rhodes</b><br>AI Automation Services</p></body></html>'''

for email, name in leads:
    print(f"📧 Sending to {name} ({email})...")
    success = send_email_via_api(email, f"Quick idea for {name}", body_html, body_text)
    print(f"   {'✅' if success else '❌'} Sent\n")