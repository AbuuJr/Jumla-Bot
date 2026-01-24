"""
scripts/seed_data.py
Seed database with sample data including 8 diverse lead scenarios
"""
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
import sys

# --- Project root & python path (so imports work) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_db_context
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.lead import Lead
from app.models.property import Property
from app.models.conversation import Conversation
from app.models.lead_score import LeadScore


async def seed_data():
    """Seed database with sample data"""
    print("Starting database seeding...")
    
    async with get_db_context() as db:
        # Create organization
        org = Organization(
            name="Demo Real Estate Company",
            slug="demo-rei",
            settings={
                "business_type": "wholesaler",
                "markets": ["Atlanta", "Dallas", "Phoenix"]
            }
        )
        db.add(org)
        await db.flush()
        
        # Create admin user
        admin = User(
            organization_id=org.id,
            email="admin@demo-rei.com",
            password_hash=hash_password("Admin123!"),
            full_name="John Admin",
            role="admin",
        )
        db.add(admin)
        
        # Create agent user
        agent = User(
            organization_id=org.id,
            email="agent@demo-rei.com",
            password_hash=hash_password("Agent123!"),
            full_name="Sarah Agent",
            role="agent",
        )
        db.add(agent)
        await db.flush()
        
        # ========== 8 Sample Leads ==========
        
        # Lead 1: HOT - Immediate financial need, poor condition
        lead1 = Lead(
            organization_id=org.id,
            phone="+14045551001",
            email="urgent.seller@email.com",
            name="Mike Johnson",
            source="web_form",
            stage="contacted",
            raw_data={"initial_message": "Need to sell ASAP, facing foreclosure"},
            enriched_data={
                "property_address": "123 Peachtree St, Atlanta, GA 30303",
                "bedrooms": 3,
                "bathrooms": 2.0,
                "condition": "poor",
                "urgency": "immediate",
                "motivation": "financial",
                "estimated_value": 180000,
                "estimated_arv": 220000,
            },
            assigned_to=agent.id,
        )
        db.add(lead1)
        await db.flush()
        
        # Conversations for Lead 1
        conv1a = Conversation(
            lead_id=lead1.id,
            channel="sms",
            direction="inbound",
            from_number=lead1.phone,
            message_body="I need to sell my house fast. Behind on payments.",
            extracted_data={"urgency": "immediate", "motivation": "financial"},
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        conv1b = Conversation(
            lead_id=lead1.id,
            channel="sms",
            direction="outbound",
            to_number=lead1.phone,
            message_body="I understand. Can you tell me about the property?",
            created_at=datetime.utcnow() - timedelta(hours=2, minutes=5)
        )
        conv1c = Conversation(
            lead_id=lead1.id,
            channel="sms",
            direction="inbound",
            from_number=lead1.phone,
            message_body="3 bed 2 bath in Atlanta. Needs work. Worth maybe 180k?",
            extracted_data={"bedrooms": 3, "bathrooms": 2, "condition": "poor"},
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=50)
        )
        db.add_all([conv1a, conv1b, conv1c])
        
        # Score for Lead 1
        score1 = LeadScore(
            lead_id=lead1.id,
            total_score=Decimal("92"),
            urgency_score=Decimal("20"),
            motivation_score=Decimal("20"),
            property_score=Decimal("18"),
            response_score=Decimal("18"),
            financial_score=Decimal("16"),
        )
        db.add(score1)
        lead1.temperature = "hot"
        
        # Lead 2: HOT - Divorce, quick timeline
        lead2 = Lead(
            organization_id=org.id,
            phone="+14045551002",
            email="divorce.sale@email.com",
            name="Lisa Martinez",
            source="referral",
            stage="contacted",
            enriched_data={
                "property_address": "456 Oak Ave, Dallas, TX 75201",
                "bedrooms": 4,
                "bathrooms": 2.5,
                "condition": "good",
                "urgency": "soon",
                "motivation": "divorce",
                "estimated_value": 320000,
                "estimated_arv": 330000,
            },
        )
        db.add(lead2)
        await db.flush()
        
        conv2 = Conversation(
            lead_id=lead2.id,
            channel="sms",
            direction="inbound",
            message_body="Going through divorce, need to sell quickly",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(conv2)
        
        score2 = LeadScore(
            lead_id=lead2.id,
            total_score=Decimal("85"),
            urgency_score=Decimal("18"),
            motivation_score=Decimal("18"),
            property_score=Decimal("15"),
            response_score=Decimal("18"),
            financial_score=Decimal("16"),
        )
        db.add(score2)
        lead2.temperature = "hot"
        
        # Lead 3: WARM - Relocation, good property
        lead3 = Lead(
            organization_id=org.id,
            phone="+16025551003",
            name="David Chen",
            source="paid_ad",
            stage="qualified",
            enriched_data={
                "property_address": "789 Desert Rd, Phoenix, AZ 85001",
                "bedrooms": 3,
                "bathrooms": 2.0,
                "condition": "good",
                "urgency": "flexible",
                "motivation": "relocation",
                "estimated_value": 275000,
                "estimated_arv": 285000,
            },
        )
        db.add(lead3)
        await db.flush()
        
        score3 = LeadScore(
            lead_id=lead3.id,
            total_score=Decimal("68"),
            urgency_score=Decimal("12"),
            motivation_score=Decimal("16"),
            property_score=Decimal("15"),
            response_score=Decimal("15"),
            financial_score=Decimal("10"),
        )
        db.add(score3)
        lead3.temperature = "warm"
        
        # Lead 4: WARM - Inheritance, fair condition
        lead4 = Lead(
            organization_id=org.id,
            phone="+14045551004",
            email="inherited.home@email.com",
            name="Patricia Wilson",
            source="web_form",
            stage="new",
            enriched_data={
                "property_address": "321 Heritage Ln, Atlanta, GA 30308",
                "bedrooms": 2,
                "bathrooms": 1.0,
                "condition": "fair",
                "motivation": "inheritance",
                "estimated_value": 150000,
            },
        )
        db.add(lead4)
        await db.flush()
        
        score4 = LeadScore(
            lead_id=lead4.id,
            total_score=Decimal("62"),
            urgency_score=Decimal("10"),
            motivation_score=Decimal("15"),
            property_score=Decimal("15"),
            response_score=Decimal("12"),
            financial_score=Decimal("10"),
        )
        db.add(score4)
        lead4.temperature = "warm"
        
        # Lead 5: WARM - Job relocation, motivated
        lead5 = Lead(
            organization_id=org.id,
            phone="+14695551005",
            name="Robert Taylor",
            source="referral",
            stage="contacted",
            enriched_data={
                "property_address": "555 Commerce St, Dallas, TX 75202",
                "bedrooms": 3,
                "bathrooms": 2.5,
                "condition": "excellent",
                "urgency": "soon",
                "motivation": "relocation",
                "estimated_value": 410000,
            },
        )
        db.add(lead5)
        await db.flush()
        
        score5 = LeadScore(
            lead_id=lead5.id,
            total_score=Decimal("58"),
            urgency_score=Decimal("15"),
            motivation_score=Decimal("14"),
            property_score=Decimal("8"),  # Excellent condition = lower score
            response_score=Decimal("12"),
            financial_score=Decimal("9"),
        )
        db.add(score5)
        lead5.temperature = "warm"
        
        # Lead 6: COLD - Just browsing, no urgency
        lead6 = Lead(
            organization_id=org.id,
            phone="+16025551006",
            name="Jennifer Brown",
            source="web_form",
            stage="new",
            enriched_data={
                "urgency": "flexible",
                "estimated_value": 225000,
            },
        )
        db.add(lead6)
        await db.flush()
        
        score6 = LeadScore(
            lead_id=lead6.id,
            total_score=Decimal("35"),
            urgency_score=Decimal("5"),
            motivation_score=Decimal("8"),
            property_score=Decimal("10"),
            response_score=Decimal("7"),
            financial_score=Decimal("5"),
        )
        db.add(score6)
        lead6.temperature = "cold"
        
        # Lead 7: COLD - Low engagement
        lead7 = Lead(
            organization_id=org.id,
            phone="+14045551007",
            name="Thomas Anderson",
            source="cold_call",
            stage="new",
            raw_data={"notes": "Not very responsive"},
            enriched_data={},
        )
        db.add(lead7)
        await db.flush()
        
        score7 = LeadScore(
            lead_id=lead7.id,
            total_score=Decimal("28"),
            urgency_score=Decimal("3"),
            motivation_score=Decimal("5"),
            property_score=Decimal("10"),
            response_score=Decimal("5"),
            financial_score=Decimal("5"),
        )
        db.add(score7)
        lead7.temperature = "cold"
        
        # Lead 8: COLD - Unrealistic expectations
        lead8 = Lead(
            organization_id=org.id,
            phone="+14695551008",
            email="high.expectations@email.com",
            name="Karen White",
            source="web_form",
            stage="contacted",
            enriched_data={
                "property_address": "999 Premium Blvd, Dallas, TX 75203",
                "bedrooms": 5,
                "bathrooms": 4.0,
                "condition": "excellent",
                "price_expectation": 850000,
                "estimated_value": 600000,
            },
        )
        db.add(lead8)
        await db.flush()
        
        score8 = LeadScore(
            lead_id=lead8.id,
            total_score=Decimal("42"),
            urgency_score=Decimal("8"),
            motivation_score=Decimal("10"),
            property_score=Decimal("5"),
            response_score=Decimal("10"),
            financial_score=Decimal("9"),
        )
        db.add(score8)
        lead8.temperature = "cold"
        
        # Commit all changes
        await db.commit()
        
        print("\n✓ Seeding complete!")
        print(f"\nOrganization: {org.name} ({org.slug})")
        print(f"\nUsers created:")
        print(f"  Admin: admin@demo-rei.com / Admin123!")
        print(f"  Agent: agent@demo-rei.com / Agent123!")
        print(f"\nLeads created: 8 total")
        print(f"  - HOT (2): {lead1.name}, {lead2.name}")
        print(f"  - WARM (3): {lead3.name}, {lead4.name}, {lead5.name}")
        print(f"  - COLD (3): {lead6.name}, {lead7.name}, {lead8.name}")
        print(f"\nAPI accessible at: http://localhost:8000")
        print(f"Docs at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed_data())