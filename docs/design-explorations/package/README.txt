WASEL DESIGN SURVEY PACKAGE

survey.html     Send this one file to people (WhatsApp, email, link). Opens on a phone or laptop, works offline,
                English / French / Arabic. Three unnamed designs in a random order per person, tap-only questions.
collector.html  For you. Paste the codes people send back (or add their .json files) to see the tallies. Exports CSV.
books/          The three full interactive books. The survey links to them if this folder stays together.

How answers come back: at the end the person taps "Send by WhatsApp" / "Send by email" / "Download the file" / "Copy the code".
Set the WhatsApp number and email once with:
  python3 docs/design-explorations/_source/package_build.py 216XXXXXXXX you@example.com
Designs: A/B/C are random per person. The collector shows results by name (Terminal Desk v2, Review Desk, Clear Desk).
All data in the screens is synthetic. The French and Arabic wording of the survey was written by Claude and not checked by a native reader.
