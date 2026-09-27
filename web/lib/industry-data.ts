export interface IndustryData {
    slug: string;
    name: string;
    title: string;
    description: string;
    keywords: string[];
    painPoints: string[];
    benefits: string[];
    schemaType: string;
}

export const INDUSTRIES: IndustryData[] = [
    {
        slug: "dentists",
        name: "Dentists",
        title: "AI Receptionist for Dental Clinics - 24/7 Appointment Booking",
        description: "Automate dental appointment bookings, answer patient queries, and reduce no-shows with Calleem's AI Receptionist for dentists.",
        keywords: ["dental answering service", "dentist appointment ai", "virtual receptionist for dentists", "dental office automation"],
        painPoints: [
            "Missed patient calls during procedures",
            "High front desk staff turnover",
            "Empty chair time due to inefficient booking",
            "After-hours dental emergencies going to voicemail"
        ],
        benefits: [
            "Book appointments directly into your practice management software",
            "Answer FAQs about procedures, insurance, and pricing",
            "24/7 coverage for emergency inquiries",
            "Reduce overhead costs by 60%"
        ],
        schemaType: "Dentist"
    },
    {
        slug: "lawyers",
        name: "Law Firms",
        title: "AI Legal Receptionist - 24/7 Client Intake & Screening",
        description: "Never miss a potential case. Calleem AI captures leads, screens clients, and schedules consultations for law firms 24/7.",
        keywords: ["legal answering service", "law firm virtual receptionist", "automated client intake", "attorney answering service"],
        painPoints: [
            "Missing high-value case leads while in court",
            "Time wasted on unqualified callers",
            "Slow response times losing clients to competitors",
            "Expensive traditional call centers"
        ],
        benefits: [
            "Instant lead qualification and intake",
            "Integration with Clio, MyCase, and other legal CRMs",
            "Professional, discrete handling of sensitive calls",
            "Capture leads nights and weekends"
        ],
        schemaType: "LegalService"
    },
    {
        slug: "real-estate",
        name: "Real Estate Agents",
        title: "AI Receptionist for Realtors - Capture Every Lead 24/7",
        description: "Instant response for property inquiries. Calleem AI schedules viewings and qualifies buyers for real estate agents instantly.",
        keywords: ["real estate answering service", "realtor virtual assistant", "scheduling showings ai", "lead capture for agents"],
        painPoints: [
            "Missing calls while at showings or closings",
            "Inability to respond instantly to Zillow/portal leads",
            "Spending hours filtering tire-kickers",
            "Losing leads to faster-responding agents"
        ],
        benefits: [
            "Instant booking of property viewings",
            "Pre-qualification of buyer leads",
            "Zero missed opportunities from sign calls",
            "Professional image for solo agents and teams"
        ],
        schemaType: "RealEstateAgent"
    },
    {
        slug: "med-spas",
        name: "Med Spas",
        title: "AI Booking Assistant for Med Spas & Estheticians",
        description: "Fill your calendar automatically. Calleem AI handles booking, deposits, and consultation inquiries for medical spas.",
        keywords: ["med spa answering service", "esthetician virtual receptionist", "spa appointment booking", "salon automation"],
        painPoints: [
            "Front desk overwhelmed during peak hours",
            "Missed calls leading to lost revenue per treatment",
            "Complex scheduling questions disrupting staff",
            "High no-show rates without instant confirmation"
        ],
        benefits: [
            "Educate clients on treatments and pricing",
            "Secure bookings with deposit capability",
            "Upsell services during the call",
            "Build a premium, modern brand image"
        ],
        schemaType: "HealthAndBeautyBusiness"
    },
    {
        slug: "hvac",
        name: "HVAC & Plumbing",
        title: "AI Dispatcher & Receptionist for HVAC & Plumbers",
        description: "Capture emergency jobs 24/7. Calleem AI screens issues, books appointments, and prioritizes urgent calls for home service pros.",
        keywords: ["hvac answering service", "plumber virtual receptionist", "emergency dispatch ai", "home service automation"],
        painPoints: [
            "Missing emergency calls at night",
            "Losing jobs to competitors who pick up first",
            "Chaotic scheduling while in the field",
            "Wasting time on non-service area calls"
        ],
        benefits: [
            "Immediate response to emergency calls",
            "Service area and capability screening",
            "Direct integration with ServiceTitan/Housecall Pro",
            "Stop paying for per-minute live answering services"
        ],
        schemaType: "HomeAndConstructionBusiness"
    },
    {
        slug: "chiropractors",
        name: "Chiropractors",
        title: "AI Front Desk for Chiropractic Clinics",
        description: "Streamline patient flow. Calleem AI handles new patient intake and recurring appointments for chiropractors.",
        keywords: ["chiropractic answering service", "chiro appointment booking", "clinic automation", "patient scheduling ai"],
        painPoints: [
            "Front desk bottlenecks checking patients in/out",
            "Missed new patient calls during lunch/hours",
            "Time spent rescheduling missed appointments",
            "Patient frustration with voicemail"
        ],
        benefits: [
            "Seamless recurring appointment scheduling",
            "Answer insurance and location questions",
            "Reduce staff burn-out",
            "Convert more website visitors to patients"
        ],
        schemaType: "Chiropractor"
    },
    {
        slug: "financial-advisors",
        name: "Financial Advisors",
        title: "AI Receptionist for Financial Advisors & Wealth Managers",
        description: "Professional, secure call handling. Calleem AI schedules consultations and screens calls for financial professionals.",
        keywords: ["financial advisor answering service", "wealth management virtual assistant", "client scheduling ai", "professional call handling"],
        painPoints: [
            "Interruptions disrupting deep work/analysis",
            "Missed prospect calls during client meetings",
            "Need for high-touch, professional experience",
            "Scheduling friction for annual reviews"
        ],
        benefits: [
            "Executive-level conversational AI",
            "Calendar integration for seamless scheduling",
            "Screen solicitors and robocalls",
            "Impress high-net-worth clients with tech"
        ],
        schemaType: "FinancialService"
    },
    {
        slug: "gyms",
        name: "Gyms & Fitness Studios",
        title: "AI Front Desk for Gyms & Fitness Studios",
        description: "Boost membership sales. Calleem AI answers class questions, books tours, and handles membership inquiries 24/7.",
        keywords: ["gym answering service", "fitness studio automation", "class booking ai", "membership sales assistant"],
        painPoints: [
            "Staff distracted by phone while training clients",
            "Missed membership inquiries after hours",
            "Repetitive questions about class schedules",
            "Lost leads from drop-ins"
        ],
        benefits: [
            "Book tours and trial classes instantly",
            "Answer questions about pricing and hours",
            "24/7 lead capture from social media ads",
            "Free up coaches to focus on members"
        ],
        schemaType: "ExerciseGym"
    },
    {
        slug: "pest-control",
        name: "Pest Control",
        title: "AI Dispatcher for Pest Control Companies",
        description: "Capture urgent service requests. Calleem AI qualifies leads, quotes prices, and schedules technicians for pest control.",
        keywords: ["pest control answering service", "exterminator virtual receptionist", "service scheduling ai", "field service automation"],
        painPoints: [
            "Missing seasonal rush calls",
            "Technicians answering calls while driving/spraying",
            "Difficulty scaling admin staff for busy season",
            "Losing leads to national competitors"
        ],
        benefits: [
            "Scale up capacity instantly for seasonal spikes",
            "Quote standard services automatically",
            "Qualify leads by pest type",
            "Route urgent infestations to priority support"
        ],
        schemaType: "HomeAndConstructionBusiness"
    },
    {
        slug: "recruiting",
        name: "Recruiting Agencies",
        title: "AI Assistant for Recruiters & Staffing Agencies",
        description: "Screen candidates faster. Calleem AI handles initial applicant screening and interview scheduling for recruiters.",
        keywords: ["staffing agency answering service", "recruiter scheduling ai", "candidate screening automation", "hiring assistant"],
        painPoints: [
            "Endless phone tag with candidates",
            "Time wasted on unqualified applicants",
            "Missed calls from hiring managers",
            "Scheduling logistical nightmares"
        ],
        benefits: [
            "Automated heavy lifting of candidate screening",
            "24/7 interview scheduling on your calendar",
            "Faster time-to-hire",
            "Candidate engagement improvement"
        ],
        schemaType: "EmploymentAgency"
    },
    {
        slug: "auto-repair",
        name: "Auto Repair Shops",
        title: "AI Service Advisor for Auto Repair & Mechanics",
        description: "Capture every repair job. Calleem AI schedules service appointments, provides status updates, and answers pricing queries 24/7.",
        keywords: ["auto repair answering service", "mechanic virtual receptionist", "car service scheduling ai", "garage automation"],
        painPoints: [
            "Mechanics stopping work to answer the phone",
            "Missed calls while under a car",
            "Constant calls asking 'is my car ready?'",
            "Losing routine maintenance jobs to chains"
        ],
        benefits: [
            "Book oil changes and diagnostics instantly",
            "Screen for vehicle make/model",
            "Reduce front-office distractions",
            "Professional image for independent shops"
        ],
        schemaType: "AutoRepair"
    },
    {
        slug: "veterinarians",
        name: "Veterinary Clinics",
        title: "AI Front Desk for Veterinary Clinics",
        description: "Care for pets, not phones. Calleem AI handles appointment booking, emergency triage, and prescription refill requests.",
        keywords: ["vet clinic answering service", "veterinary receptionist ai", "pet hospital scheduling", "vet appointment automation"],
        painPoints: [
            "Overwhelmed staff during check-in/out",
            "Missed emergency calls after hours",
            "Time spent on simple prescription questions",
            "Phone tag confirming appointments"
        ],
        benefits: [
            "Triage emergency vs. routine calls",
            "Schedule check-ups and vaccinations",
            "Answer FAQs about hours and services",
            "Reduce staff burnout"
        ],
        schemaType: "VeterinaryCare"
    },
    {
        slug: "cleaning-services",
        name: "Cleaning Services",
        title: "AI Booking Agent for Cleaning Companies",
        description: "Clean up your schedule. Calleem AI quotes prices, books cleanings, and manages cancellations for residential and commercial cleaners.",
        keywords: ["cleaning service answering service", "maid service virtual receptionist", "cleaning appointment booking", "janitorial automation"],
        painPoints: [
            "Missing calls while cleaning client homes",
            "Difficulty quoting prices over the phone",
            "Last-minute cancellation chaos",
            "Scheduling conflicts suited for automation"
        ],
        benefits: [
            "Instant quotes based on room count/size",
            "Fill gaps in the schedule automatically",
            "Professional handling of new inquiries",
            "Grow your client base 24/7"
        ],
        schemaType: "ProfessionalService"
    },
    {
        slug: "landscaping",
        name: "Landscaping & Lawn Care",
        title: "AI Office Manager for Landscapers",
        description: "Grow your business. Calleem AI schedules estimates, routes service crews, and answers seasonal inquiries for landscaping pros.",
        keywords: ["landscaping answering service", "lawn care virtual receptionist", "mowing schedule ai", "gardener appointment booking"],
        painPoints: [
            "Noise from equipment making calls impossible",
            "Missed estimate requests during spring rush",
            "Scheduling rain delays manually",
            "Losing leads to competitors who answer fast"
        ],
        benefits: [
            "Book on-site estimates automatically",
            "Answer questions about service areas",
            "Capture leads while on the mower",
            "Scale for the busy season instantly"
        ],
        schemaType: "ProfessionalService"
    },
    {
        slug: "it-support",
        name: "IT Support & MSPs",
        title: "AI Help Desk for IT Support & MSPs",
        description: "First-line tech support. Calleem AI triages ticketing, schedules on-site visits, and escalates critical outages.",
        keywords: ["msp answering service", "it support virtual receptionist", "help desk automation", "tech appointment booking"],
        painPoints: [
            "Technicians distracted by Level 1 calls",
            "Missed critical outage alerts",
            "Difficulty prioritizing tickets manually",
            "High cost of 24/7 human help desk"
        ],
        benefits: [
            "Create tickets in your PSA (ConnectWise/Autotask)",
            "Screen for critical vs. low priority",
            "Schedule remote sessions or site visits",
            "Provide 24/7 coverage for SLAs"
        ],
        schemaType: "ProfessionalService"
    },
    {
        slug: "event-planners",
        name: "Event Planners",
        title: "AI Coordinator for Event Planners & Venues",
        description: "Focus on the event. Calleem AI captures venue inquiries, schedules tours, and answers vendor questions.",
        keywords: ["event planner answering service", "venue booking assistant", "wedding planner virtual receptionist", "event automation"],
        painPoints: [
            "Missing new leads while running events",
            "Repetitive questions about venue capacity/pricing",
            "Endless back-and-forth scheduling tours",
            "Client anxiety when calls aren't returned"
        ],
        benefits: [
            "Qualify leads by event date and budget",
            "Schedule venue tours automatically",
            "Answer FAQs about packages",
            "Professional first impression"
        ],
        schemaType: "EventVenue"
    },
    {
        slug: "counseling",
        name: "Therapists & Counselors",
        title: "AI Intake Coordinator for Therapists",
        description: "Compassionate, private networking. Calleem AI handles new patient intake, insurance queries, and confidential scheduling.",
        keywords: ["therapist answering service", "counseling practice automation", "psychologist virtual receptionist", "mental health appointment booking"],
        painPoints: [
            "Cannot answer phone during sessions",
            "Privacy concerns with general answering services",
            "Patient anxiety about leaving voicemails",
            "Scheduling intake calls manually"
        ],
        benefits: [
            "HIPAA-compliant conversational handling",
            "Screen for insurance acceptance",
            "Schedule intake consultations",
            "Private and professional experience"
        ],
        schemaType: "MedicalBusiness"
    },
    {
        slug: "solar",
        name: "Solar Installers",
        title: "AI Lead Capture for Solar Companies",
        description: "Convert more leads. Calleem AI qualifies homeowners, schedules site surveys, and answers technical questions for solar installers.",
        keywords: ["solar company answering service", "solar lead qualification ai", "installer virtual receptionist", "site survey scheduling"],
        painPoints: [
            "High volume of unqualified leads",
            "Missed calls from ad campaigns",
            "Sales team wasting time on non-homeowners",
            "Complex scheduling for site visits"
        ],
        benefits: [
            "Pre-qualify homeowners vs. renters",
            "Schedule site surveys for sales team",
            "Capture leads 24/7 from marketing",
            "Increase speed-to-lead"
        ],
        schemaType: "HomeAndConstructionBusiness"
    },
    {
        slug: "moving",
        name: "Moving Companies",
        title: "AI Logistics Coordinator for Movers",
        description: "Fill your trucks. Calleem AI provides instant quotes, books moves, and answers status scheduling questions.",
        keywords: ["moving company answering service", "mover virtual receptionist", "moving quote ai", "logistics automation"],
        painPoints: [
            "Missing calls during physical moves",
            "Difficulty providing estimates quickly",
            "Last-minute scheduling gaps",
            "High competition for every lead"
        ],
        benefits: [
            "Collect move details (size, distance)",
            "Schedule in-home estimates",
            "Answer questions about insurance/supplies",
            "Book moves directly into calendar"
        ],
        schemaType: "ProfessionalService"
    },
    {
        slug: "tattoo",
        name: "Tattoo Studios",
        title: "AI Booking Assistant for Tattoo Artists",
        description: "Focus on the art. Calleem AI handles consultation bookings, deposit questions, and aftercare inquiries.",
        keywords: ["tattoo shop answering service", "tattoo artist scheduling ai", "studio virtual receptionist", "consultation booking"],
        painPoints: [
            "Artists can't answer phone while tattooing",
            "Constant interruptions for pricing questions",
            "No-shows for consultations",
            "Managing deposits manually"
        ],
        benefits: [
            "Book consultations and flash appointments",
            "Answer pricing and age requirement FAQs",
            "Explain deposit policies",
            "Maintain a cool, modern studio vibe"
        ],
        schemaType: "HealthAndBeautyBusiness"
    }
];
