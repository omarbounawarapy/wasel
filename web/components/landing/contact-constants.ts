export interface FAQItem {
    id: string;
    number: string;
    question: string;
    answer: string;
}

export interface FormData {
    fullName: string;
    email: string;
    businessName: string;
    businessType: string;
    phoneNumber: string;
    monthlyCalls: string;
    message: string;
    newsletter: boolean;
    privacyPolicy: boolean;
}

export const FAQ_ITEMS: FAQItem[] = [
    {
        id: '0',
        number: '01',
        question: 'What is an AI Receptionist?',
        answer: 'An AI Receptionist is a virtual answering service that uses artificial intelligence to handle phone calls 24/7. Unlike traditional voicemail, it engages callers in natural conversation, answers questions, books appointments directly into your calendar, and captures leads instantly, ensuring you never miss a business opportunity.'
    },
    {
        id: '1',
        number: '02',
        question: 'What kind of businesses is Calleem built for?',
        answer: 'Calleem is built for service-based businesses that rely on phone appointments, such as dental clinics, law firms, real estate agencies, med spas, and home service providers. It is the ideal solution for any business needing 24/7 front desk coverage without the overhead of hiring additional staff.'
    },
    {
        id: '2',
        number: '03',
        question: 'Does Calleem integrate with my existing phone number?',
        answer: 'Yes, Calleem seamlessly integrates with your existing business phone number through simple call forwarding. You can choose to forward all calls, or only those you miss after hours. This ensures you maintain your established business identity while guaranteeing every caller receives an instant response.'
    },
    {
        id: '3',
        number: '04',
        question: 'Can I customize the AI’s voice and greeting?',
        answer: 'Yes, you can fully customize Calleem to match your brand. Choose from a variety of professional, natural-sounding voices and script your own custom greeting. You can also tailor the conversation flow to handle specific FAQs, ensuring the AI represents your business exactly as you wish.'
    },
    {
        id: '4',
        number: '05',
        question: 'Will I get transcripts of every call?',
        answer: 'Yes, every interaction is recorded and transcribed in real-time. You can access full text transcripts and audio recordings within your Calleem dashboard. This allows you to review client details, verify appointment information, and monitor lead quality without listening to every minute of audio.'
    },
    {
        id: '5',
        number: '06',
        question: 'How does the AI handle appointment booking?',
        answer: 'Calleem connects directly to your calendar (Google Calendar, etc.). When a caller wants to book, the AI checks your real-time availability, offers open slots, and confirms the appointment on the spot. It works just like a human receptionist but operates instantly and is available 24/7.'
    }
];

export const CALL_VOLUME_OPTIONS = [
    '300-550 calls/month',
    '560-800 calls/month',
    '810-990 calls/month'
];

export const BUSINESS_TYPES = [
    'Salon',
    'Consulting',
    'Clinic',
    'Agency',
    'Law Firm',
    'Other'
];
