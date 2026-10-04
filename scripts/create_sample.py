"""Author a small, original mechanics PDF for reproducible local evaluation."""
from pathlib import Path

import pymupdf

PAGES = [
    ("01 / Newton's laws", "Newton's first law: A body remains at rest or moves in a straight line at constant "
     "velocity unless a net external force acts on it.\n\n"
     "Newton's second law: Net force equals mass times acceleration: F = m a. Force is measured in "
     "newtons (N), mass in kilograms (kg), and acceleration in metres per second squared (m/s^2).\n\n"
     "Worked example: A 2 kg body accelerating at 4 m/s^2 experiences a net force of 8 N.\n\n"
     "Newton's third law: Forces in an interaction are equal in magnitude and opposite in direction. "
     "They act on different bodies, so they do not cancel as forces on one body."),
    ("02 / Energy and momentum", "Kinetic energy is the energy of motion. For a body of mass m moving at speed v, "
     "kinetic energy is E = (1/2) m v^2. Energy is measured in joules (J).\n\n"
     "Worked example: A 2 kg body moving at 3 m/s has kinetic energy of 9 J.\n\n"
     "Linear momentum equals mass times velocity: p = m v. Its SI unit is kg m/s.\n\n"
     "Worked example: A 2 kg body moving at 3 m/s has momentum of 6 kg m/s."),
    ("03 / Work and power", "When a constant force acts parallel to displacement, work equals force times "
     "displacement: W = F d. Work is measured in joules (J).\n\n"
     "Worked example: A 10 N force acting along a displacement of 3 m does 30 J of work.\n\n"
     "Average power is work divided by elapsed time: P = W/t. Power is measured in watts (W).\n\n"
     "Worked example: Doing 30 J of work in 6 seconds gives an average power of 5 W."),
]


def create_sample(path=Path("eval/sample.pdf")):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as doc:
        for index, (title, text) in enumerate(PAGES):
            page = doc.new_page()
            page.insert_text((52, 60), "CITETUTOR / STUDY FIXTURE", fontsize=10, color=(0.2, 0.35, 0.25))
            page.insert_text((52, 108), title, fontsize=23)
            remaining = page.insert_textbox((52, 155, 540, 710), text, fontsize=13, lineheight=1.65)
            if remaining < 0:
                raise RuntimeError("Sample PDF text overflowed the page")
            page.insert_text((52, 785), f"Original evaluation material · Physical page {index + 1}", fontsize=9)
        doc.set_metadata({"title": "CiteTutor: Foundations of Mechanics", "author": "CiteTutor project"})
        doc.save(path, garbage=4, deflate=True)
    return path


if __name__ == "__main__":
    print(create_sample())
