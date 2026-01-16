import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatWidget from '@components/ChatWidget/ChatWidget';
import FallbackForm from './FallbackForm';
import Button from '@components/ui/Button';

// ============================================================================
// SellerIntake Page - Primary seller entry point with chat interface
// ============================================================================

export default function SellerIntake() {
  const [showFallbackForm, setShowFallbackForm] = useState(false);
  const [leadId, setLeadId] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLeadCreated = (newLeadId: string, conversationId: string) => {
    setLeadId(newLeadId);
    console.log('Lead created:', { leadId: newLeadId, conversationId });
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-6 text-center">
            <h1 className="mb-2 text-3xl font-bold text-neutral-900">
              Let's Get Your Offer Started
            </h1>
            <p className="text-neutral-600">
              Chat with our AI assistant or fill out the form below
            </p>
          </div>

          {/* Chat Interface */}
          {!showFallbackForm ? (
            <div className="mb-4">
              <ChatWidget
                className="h-[600px]"
                onLeadCreated={handleLeadCreated}
              />

              <div className="mt-4 text-center">
                <button
                  onClick={() => setShowFallbackForm(true)}
                  className="text-sm text-primary-600 underline hover:text-primary-700"
                >
                  Prefer a form? Click here
                </button>
              </div>
            </div>
          ) : (
            <div>
              <FallbackForm onSuccess={(newLeadId) => setLeadId(newLeadId)} />

              <div className="mt-4 text-center">
                <button
                  onClick={() => setShowFallbackForm(false)}
                  className="text-sm text-primary-600 underline hover:text-primary-700"
                >
                  Back to chat
                </button>
              </div>
            </div>
          )}

          {/* Success State */}
          {leadId && (
            <div className="mt-6 rounded-lg bg-green-50 p-6 text-center">
              <h2 className="mb-2 text-xl font-semibold text-green-900">
                ✓ Thank You!
              </h2>
              <p className="mb-4 text-green-700">
                Your information has been received. We're analyzing your property and will
                generate an offer shortly.
              </p>
              <Button variant="primary" onClick={() => navigate('/')}>
                Back to Home
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}