import { http, HttpResponse } from 'msw';
import type {
  LoginResponse,
  LeadCreateResponse,
  LeadsListResponse,
  LeadDetailResponse,
  SendMessageResponse,
  FileUploadResponse,
  Offer,
  OfferApproveResponse,
} from '@lib/api/types';

// ============================================================================
// MSW Handlers - Mock API responses for development and testing
// Realistic data that matches backend contracts
// ============================================================================

const BASE_URL = 'http://localhost:8000';

// ===== Mock Data Store =====
let mockLeads: any[] = [
  {
    id: 'lead-001',
    status: 'new',
    source: 'chat',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    seller_info: {
      name: 'John Smith',
      email: 'john.smith@example.com',
      phone: '555-0123',
      motivation: 'Relocating for work',
      timeline: 'Within 60 days',
    },
    property_info: {
      address: '123 Main Street',
      city: 'San Francisco',
      state: 'CA',
      zip: '94102',
      property_type: 'single_family',
      bedrooms: 3,
      bathrooms: 2,
      square_feet: 1800,
      year_built: 1995,
      condition: 'good',
      asking_price: 850000,
    },
    conversation_id: 'conv-001',
  },
  {
    id: 'lead-002',
    status: 'qualified',
    source: 'form',
    created_at: '2024-01-14T15:20:00Z',
    updated_at: '2024-01-14T16:45:00Z',
    seller_info: {
      name: 'Sarah Johnson',
      email: 'sarah.j@example.com',
      phone: '555-0456',
      motivation: 'Downsizing',
      timeline: 'Flexible',
    },
    property_info: {
      address: '456 Oak Avenue',
      city: 'Oakland',
      state: 'CA',
      zip: '94601',
      property_type: 'condo',
      bedrooms: 2,
      bathrooms: 2,
      square_feet: 1200,
      year_built: 2010,
      condition: 'excellent',
      asking_price: 650000,
    },
  },
  {
    id: 'lead-003',
    status: 'offer_generated',
    source: 'chat',
    created_at: '2024-01-13T09:15:00Z',
    updated_at: '2024-01-13T14:30:00Z',
    seller_info: {
      name: 'Michael Chen',
      email: 'mchen@example.com',
      phone: '555-0789',
      motivation: 'Financial hardship',
      timeline: 'ASAP',
    },
    property_info: {
      address: '789 Pine Street',
      city: 'Berkeley',
      state: 'CA',
      zip: '94702',
      property_type: 'townhouse',
      bedrooms: 3,
      bathrooms: 2.5,
      square_feet: 1600,
      year_built: 2005,
      condition: 'fair',
      asking_price: 720000,
    },
    conversation_id: 'conv-003',
    offer_id: 'offer-003',
  },
];

let mockConversations: Record<string, any> = {
  'conv-001': {
    id: 'conv-001',
    lead_id: 'lead-001',
    messages: [
      {
        id: 'msg-001',
        role: 'user',
        content: "Hi, I'm interested in selling my home quickly.",
        timestamp: '2024-01-15T10:30:00Z',
      },
      {
        id: 'msg-002',
        role: 'assistant',
        content:
          "Great! I'd be happy to help you sell your home. Can you tell me a bit about your property? Where is it located?",
        timestamp: '2024-01-15T10:30:15Z',
      },
      {
        id: 'msg-003',
        role: 'user',
        content: "It's at 123 Main Street in San Francisco. It's a 3 bedroom, 2 bath house.",
        timestamp: '2024-01-15T10:31:00Z',
      },
      {
        id: 'msg-004',
        role: 'assistant',
        content:
          'Perfect! A 3 bed, 2 bath in San Francisco. How many square feet is your home, and when was it built?',
        timestamp: '2024-01-15T10:31:20Z',
        metadata: {
          extracted_fields: {
            address: '123 Main Street',
            city: 'San Francisco',
            bedrooms: 3,
            bathrooms: 2,
          },
          confidence_scores: {
            address: 0.95,
            bedrooms: 0.98,
            bathrooms: 0.98,
          },
        },
      },
    ],
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:31:20Z',
  },
  'conv-003': {
    id: 'conv-003',
    lead_id: 'lead-003',
    messages: [
      {
        id: 'msg-010',
        role: 'user',
        content: 'I need to sell my townhouse as soon as possible.',
        timestamp: '2024-01-13T09:15:00Z',
      },
      {
        id: 'msg-011',
        role: 'assistant',
        content:
          "I understand the urgency. Let's get you a fast offer. Can you share your property address and details?",
        timestamp: '2024-01-13T09:15:15Z',
      },
    ],
    created_at: '2024-01-13T09:15:00Z',
    updated_at: '2024-01-13T09:15:15Z',
  },
};

let mockOffers: Record<string, Offer> = {
  'offer-003': {
    id: 'offer-003',
    lead_id: 'lead-003',
    status: 'pending',
    offer_amount: 685000,
    earnest_money: 10000,
    closing_days: 30,
    contingencies: ['Inspection', 'Financing'],
    terms:
      'Cash offer with flexible closing date. Property sold as-is with standard inspection contingency.',
    generated_at: '2024-01-13T14:30:00Z',
    expires_at: '2024-01-20T14:30:00Z',
  },
};

// ===== Authentication =====
export const authHandlers = [
  http.post(`${BASE_URL}/api/v1/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };

    // Mock authentication - accept any email/password for demo
    if (body.email && body.password) {
      const response: LoginResponse = {
        access_token: 'mock-jwt-token-' + Date.now(),
        refresh_token: 'mock-refresh-token-' + Date.now(),
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: 'user-001',
          email: body.email,
          role: 'admin',
          created_at: '2024-01-01T00:00:00Z',
        },
      };
      return HttpResponse.json(response, { status: 200 });
    }

    return HttpResponse.json(
      { error: 'InvalidCredentials', message: 'Invalid email or password' },
      { status: 401 }
    );
  }),

  http.post(`${BASE_URL}/api/v1/auth/logout`, () => {
    return HttpResponse.json({ message: 'Logged out successfully' }, { status: 200 });
  }),

  http.post(`${BASE_URL}/api/v1/auth/refresh`, () => {
    return HttpResponse.json(
      { access_token: 'mock-refreshed-token-' + Date.now() },
      { status: 200 }
    );
  }),
];

// ===== Leads =====
export const leadsHandlers = [
  // Create Lead
  http.post(`${BASE_URL}/api/v1/leads`, async ({ request }) => {
    const body = (await request.json()) as any;

    const newLead = {
      id: `lead-${Date.now()}`,
      status: 'new',
      source: body.source || 'chat',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      seller_info: body.seller_info || {},
      property_info: body.property_info || {},
      conversation_id: body.source === 'chat' ? `conv-${Date.now()}` : undefined,
    };

    mockLeads.push(newLead);

    // Create conversation if chat source
    if (newLead.conversation_id) {
      mockConversations[newLead.conversation_id] = {
        id: newLead.conversation_id,
        lead_id: newLead.id,
        messages: body.initial_message
          ? [
              {
                id: `msg-${Date.now()}`,
                role: 'user',
                content: body.initial_message,
                timestamp: new Date().toISOString(),
              },
            ]
          : [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }

    const response: LeadCreateResponse = {
      lead: newLead,
      conversation_id: newLead.conversation_id!,
    };

    return HttpResponse.json(response, { status: 201 });
  }),

  // List Leads
  http.get(`${BASE_URL}/api/v1/leads`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('page_size') || '20');
    const status = url.searchParams.get('status');
    const search = url.searchParams.get('search');

    let filteredLeads = [...mockLeads];

    // Filter by status
    if (status) {
      filteredLeads = filteredLeads.filter((lead) => lead.status === status);
    }

    // Filter by search
    if (search) {
      const searchLower = search.toLowerCase();
      filteredLeads = filteredLeads.filter(
        (lead) =>
          lead.seller_info?.name?.toLowerCase().includes(searchLower) ||
          lead.seller_info?.email?.toLowerCase().includes(searchLower) ||
          lead.property_info?.address?.toLowerCase().includes(searchLower)
      );
    }

    // Paginate
    const startIndex = (page - 1) * pageSize;
    const paginatedLeads = filteredLeads.slice(startIndex, startIndex + pageSize);

    const response: LeadsListResponse = {
      leads: paginatedLeads,
      total: filteredLeads.length,
      page,
      page_size: pageSize,
    };

    return HttpResponse.json(response, { status: 200 });
  }),

  // Get Lead Detail
  http.get(`${BASE_URL}/api/v1/leads/:id`, ({ params }) => {
    const { id } = params;
    const lead = mockLeads.find((l) => l.id === id);

    if (!lead) {
      return HttpResponse.json({ error: 'NotFound', message: 'Lead not found' }, { status: 404 });
    }

    const response: LeadDetailResponse = {
      lead,
      conversation: lead.conversation_id ? mockConversations[lead.conversation_id] : undefined,
      offer: lead.offer_id ? mockOffers[lead.offer_id] : undefined,
    };

    return HttpResponse.json(response, { status: 200 });
  }),

  // Update Lead
  http.patch(`${BASE_URL}/api/v1/leads/:id`, async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as any;
    const leadIndex = mockLeads.findIndex((l) => l.id === id);

    if (leadIndex === -1) {
      return HttpResponse.json({ error: 'NotFound', message: 'Lead not found' }, { status: 404 });
    }

    mockLeads[leadIndex] = {
      ...mockLeads[leadIndex],
      ...body,
      updated_at: new Date().toISOString(),
    };

    const response: LeadDetailResponse = {
      lead: mockLeads[leadIndex],
    };

    return HttpResponse.json(response, { status: 200 });
  }),
];

// ===== Conversations =====
export const conversationsHandlers = [
  // Send Message
  http.post(`${BASE_URL}/api/v1/conversations/:conversationId/messages`, async ({ params, request }) => {
    const { conversationId } = params;
    const body = (await request.json()) as any;

    const conversation = mockConversations[conversationId as string];
    if (!conversation) {
      return HttpResponse.json(
        { error: 'NotFound', message: 'Conversation not found' },
        { status: 404 }
      );
    }

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user' as const,
      content: body.content,
      timestamp: new Date().toISOString(),
      attachments: body.attachments || [],
    };

    // Simulate AI response
    const botMessage = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant' as const,
      content: generateBotResponse(body.content),
      timestamp: new Date(Date.now() + 1000).toISOString(),
      metadata: {
        extracted_fields: extractFields(body.content),
        confidence_scores: { general: 0.85 },
      },
    };

    conversation.messages.push(userMessage, botMessage);
    conversation.updated_at = new Date().toISOString();

    const response: SendMessageResponse = {
      user_message: userMessage,
      bot_message: botMessage,
      extracted_data: {
        seller_info: extractFields(body.content).seller_info,
        property_info: extractFields(body.content).property_info,
      },
    };

    return HttpResponse.json(response, { status: 200 });
  }),

  // Get Messages
  http.get(`${BASE_URL}/api/v1/conversations/:conversationId/messages`, ({ params }) => {
    const { conversationId } = params;
    const conversation = mockConversations[conversationId as string];

    if (!conversation) {
      return HttpResponse.json(
        { error: 'NotFound', message: 'Conversation not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(conversation, { status: 200 });
  }),
];

// ===== File Upload =====
export const fileHandlers = [
  // Request Upload URL
  http.post(`${BASE_URL}/api/v1/files/upload`, async ({ request }) => {
    const body = (await request.json()) as any;

    const response: FileUploadResponse = {
      upload_id: `upload-${Date.now()}`,
      signed_url: `https://mock-s3.amazonaws.com/signed-upload-${Date.now()}`,
      file_url: `https://mock-s3.amazonaws.com/files/${body.filename}`,
      expires_at: new Date(Date.now() + 3600000).toISOString(),
    };

    return HttpResponse.json(response, { status: 200 });
  }),
];

// ===== Offers =====
export const offersHandlers = [
  // Generate Offer
  http.post(`${BASE_URL}/api/v1/offers/generate`, async ({ request }) => {
    const body = (await request.json()) as any;
    const leadId = body.lead_id;

    const lead = mockLeads.find((l) => l.id === leadId);
    if (!lead) {
      return HttpResponse.json({ error: 'NotFound', message: 'Lead not found' }, { status: 404 });
    }

    const newOffer: Offer = {
      id: `offer-${Date.now()}`,
      lead_id: leadId,
      status: 'pending',
      offer_amount:
        body.override_params?.offer_amount ||
        Math.floor((lead.property_info?.asking_price || 500000) * 0.92),
      earnest_money: body.override_params?.earnest_money || 10000,
      closing_days: body.override_params?.closing_days || 30,
      contingencies: ['Inspection', 'Financing'],
      terms: 'Standard cash offer with inspection contingency. Property sold as-is.',
      generated_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    };

    mockOffers[newOffer.id] = newOffer;

    // Update lead
    const leadIndex = mockLeads.findIndex((l) => l.id === leadId);
    if (leadIndex !== -1) {
      mockLeads[leadIndex].status = 'offer_generated';
      mockLeads[leadIndex].offer_id = newOffer.id;
    }

    return HttpResponse.json(newOffer, { status: 201 });
  }),

  // Get Offer
  http.get(`${BASE_URL}/api/v1/leads/:leadId/offer`, ({ params }) => {
    const { leadId } = params;
    const lead = mockLeads.find((l) => l.id === leadId);

    if (!lead || !lead.offer_id) {
      return HttpResponse.json({ error: 'NotFound', message: 'Offer not found' }, { status: 404 });
    }

    const offer = mockOffers[lead.offer_id];
    return HttpResponse.json(offer, { status: 200 });
  }),

  // Approve Offer
  http.post(`${BASE_URL}/api/v1/offers/approve`, async ({ request }) => {
    const body = (await request.json()) as any;
    const offerId = body.offer_id;

    const offer = mockOffers[offerId];
    if (!offer) {
      return HttpResponse.json({ error: 'NotFound', message: 'Offer not found' }, { status: 404 });
    }

    offer.status = 'approved';
    offer.approved_at = new Date().toISOString();
    offer.approved_by = 'user-001';

    // Update lead status
    const leadIndex = mockLeads.findIndex((l) => l.offer_id === offerId);
    if (leadIndex !== -1) {
      mockLeads[leadIndex].status = 'offer_approved';
    }

    const response: OfferApproveResponse = {
      offer,
      notification_sent: true,
    };

    return HttpResponse.json(response, { status: 200 });
  }),

  // Reject Offer
  http.post(`${BASE_URL}/api/v1/offers/:offerId/reject`, async ({ params }) => {
    const { offerId } = params;
    const offer = mockOffers[offerId as string];

    if (!offer) {
      return HttpResponse.json({ error: 'NotFound', message: 'Offer not found' }, { status: 404 });
    }

    offer.status = 'rejected';
    return HttpResponse.json({ message: 'Offer rejected' }, { status: 200 });
  }),
];

// ===== Helper Functions =====
function generateBotResponse(userMessage: string): string {
  const lower = userMessage.toLowerCase();

  if (lower.includes('address') || lower.includes('located') || lower.includes('where')) {
    return "Great! Can you provide the full address including city, state, and ZIP code?";
  }

  if (lower.includes('bedroom') || lower.includes('bath')) {
    return 'Perfect! How many square feet is your home, and when was it built?';
  }

  if (lower.includes('square') || lower.includes('sqft') || lower.includes('size')) {
    return "Thanks! What condition is the property in? (Excellent, Good, Fair, or Needs Work)";
  }

  if (lower.includes('condition')) {
    return 'Understood. Why are you looking to sell, and what is your ideal timeline?';
  }

  if (lower.includes('timeline') || lower.includes('when') || lower.includes('soon')) {
    return "Thank you for all that information! I'm analyzing your property details and will generate an offer shortly. Is there anything else you'd like me to know?";
  }

  return "I understand. Can you tell me more about your property so I can provide the best offer?";
}

function extractFields(content: string): any {
  const extracted: any = {
    seller_info: {},
    property_info: {},
  };

  // Simple pattern matching for demo purposes
  const addressMatch = content.match(/\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr)/i);
  if (addressMatch) {
    extracted.property_info.address = addressMatch[0];
  }

  const bedroomMatch = content.match(/(\d+)\s*(?:bed|bedroom)/i);
  if (bedroomMatch) {
    extracted.property_info.bedrooms = parseInt(bedroomMatch[1]);
  }

  const bathroomMatch = content.match(/(\d+(?:\.\d+)?)\s*(?:bath|bathroom)/i);
  if (bathroomMatch) {
    extracted.property_info.bathrooms = parseFloat(bathroomMatch[1]);
  }

  return extracted;
}

// ===== Export All Handlers =====
export const handlers = [
  ...authHandlers,
  ...leadsHandlers,
  ...conversationsHandlers,
  ...fileHandlers,
  ...offersHandlers,
];