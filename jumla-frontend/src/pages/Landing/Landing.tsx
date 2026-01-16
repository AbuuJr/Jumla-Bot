import { Link } from 'react-router-dom';
import Button from '@components/ui/Button';

// ============================================================================
// Landing Page - Marketing homepage with CTA
// ============================================================================

export default function Landing() {
  return (
    <div className="bg-gradient-to-b from-primary-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-neutral-900">
            Sell Your Home Fast with{' '}
            <span className="text-primary-600">AI-Powered</span> Offers
          </h1>
          <p className="mb-8 text-xl text-neutral-600">
            Get a competitive cash offer in minutes. Our AI assistant guides you through the
            process and generates instant offers based on market data.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link to="/sell">
              <Button size="lg" variant="primary" className="min-w-[200px]">
                Get My Offer Now
              </Button>
            </Link>
            <Link to="/buyers">
              <Button size="lg" variant="outline" className="min-w-[200px]">
                For Buyers
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="mb-12 text-center text-3xl font-bold text-neutral-900">
          Why Choose Jumla-bot?
        </h2>

        <div className="grid gap-8 md:grid-cols-3">
          <FeatureCard
            icon="🤖"
            title="AI-Powered Assistant"
            description="Chat with our intelligent bot to provide property details naturally. No complex forms."
          />
          <FeatureCard
            icon="⚡"
            title="Instant Offers"
            description="Receive competitive cash offers within minutes based on real-time market analysis."
          />
          <FeatureCard
            icon="🔒"
            title="Secure & Transparent"
            description="Your data is protected. Review detailed offer breakdowns before making any decisions."
          />
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-neutral-50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 text-center text-3xl font-bold text-neutral-900">
            How It Works
          </h2>

          <div className="mx-auto max-w-3xl space-y-6">
            <Step
              number={1}
              title="Chat with Our AI"
              description="Tell us about your property through a simple conversation."
            />
            <Step
              number={2}
              title="Get Your Offer"
              description="Our AI analyzes market data and generates a competitive offer instantly."
            />
            <Step
              number={3}
              title="Review & Accept"
              description="Review the detailed offer and accept when ready. Close on your timeline."
            />
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-primary-600 py-16 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-4 text-3xl font-bold">Ready to Get Started?</h2>
          <p className="mb-8 text-xl text-primary-100">
            Join thousands of satisfied sellers who chose the smart way to sell.
          </p>
          <Link to="/sell">
            <Button size="lg" variant="secondary">
              Start Your Offer
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

// ===== Sub-components =====
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg bg-white p-6 text-center shadow-sm">
      <div className="mb-4 text-4xl">{icon}</div>
      <h3 className="mb-2 text-xl font-semibold text-neutral-900">{title}</h3>
      <p className="text-neutral-600">{description}</p>
    </div>
  );
}

function Step({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary-600 text-lg font-bold text-white">
        {number}
      </div>
      <div>
        <h3 className="mb-1 text-lg font-semibold text-neutral-900">{title}</h3>
        <p className="text-neutral-600">{description}</p>
      </div>
    </div>
  );
}