"""Assemble the single submission PDF: A4 cover -> complete A2 submission -> A4 Sections 2-4."""
import sys
from pypdf import PdfReader, PdfWriter
a2_path = sys.argv[1] if len(sys.argv) > 1 else "reports/PRT661_Assessment2_Syd2Theme2.pdf"
a4 = PdfReader("reports/PRT661_A4_additions.pdf"); a2 = PdfReader(a2_path)
w = PdfWriter(); w.add_page(a4.pages[0])
for p in a2.pages: w.add_page(p)
for p in a4.pages[1:]: w.add_page(p)
w.add_metadata({"/Title": "PRT661 Assessment 4 – Final Professional Report (Sydn2 – Theme 2)", "/Author": "Sydn2 – Theme 2"})
n2 = 1 + len(a2.pages)
for t, i in [("Cover & document map", 0), ("Section 1 – Complete Assessment 2 submission", 1),
             ("Section 2 – Final Project Update Summary", n2), ("Section 3 – Final Technical Development", n2 + 1),
             ("Section 4 – Individual Work and Contribution Summary", n2 + 17)]:
    w.add_outline_item(t, i)
w.write("reports/PRT661_Assessment4_Final_Report_Syd2Theme2.pdf"); print("pages:", len(w.pages))
