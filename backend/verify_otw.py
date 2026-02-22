import json
from src.sourcing import SourcingEngine
from src.models import CandidateProfile

def verify():
    # Mock PhantomBuster data
    mock_pb_data = [
        # Candidate 1: Official Flag (True)
        {
            "profileUrl": "https://linkedin.com/in/otw-official",
            "fullName": "Official OTW",
            "headline": "Software Engineer",
            "isOpenToWork": True
        },
        # Candidate 2: Headline Keyword
        {
            "profileUrl": "https://linkedin.com/in/otw-headline",
            "fullName": "Headline OTW",
            "headline": "Looking for new opportunities | Python Dev",
            "isOpenToWork": False
        },
        # Candidate 3: About snippet Keyword
        {
            "profileUrl": "https://linkedin.com/in/otw-about",
            "fullName": "About OTW",
            "headline": "Lead Designer",
            "additionalInfo": "I am #opentowork and seeking my next challenge.",
            "isOpenToWork": False
        },
        # Candidate 4: Not Open to Work (No flags, no keywords)
        {
            "profileUrl": "https://linkedin.com/in/not-otw",
            "fullName": "Stable Employee",
            "headline": "Director of Engineering at Google",
            "isOpenToWork": False
        }
    ]

    engine = SourcingEngine()
    print("\n🧐 Verifying OTW Filter with mixed candidates...")
    
    # Run the parser (which now has 'only_open_to_work=True' by default)
    filtered_candidates = engine._parse_pb_results(mock_pb_data)

    print(f"\n📊 RESULTS:")
    print(f"   Original count: {len(mock_pb_data)}")
    print(f"   Filtered count: {len(filtered_candidates)}")
    
    print("\n✅ Filtered Candidates (Should be 3):")
    for c in filtered_candidates:
        print(f"   - {c.name} (OTW: {c.is_open_to_work})")

    # Assertions
    names = [c.name for c in filtered_candidates]
    assert "Official OTW" in names
    assert "Headline OTW" in names
    assert "About OTW" in names
    assert "Stable Employee" not in names
    
    print("\n🏆 VERIFICATION PASSED: Only Open-to-Work candidates imported.")

if __name__ == "__main__":
    verify()
