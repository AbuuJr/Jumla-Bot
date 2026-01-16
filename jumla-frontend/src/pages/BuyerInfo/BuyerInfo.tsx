import Card from '@components/ui/Card';
import Button from '@components/ui/Button';

// ============================================================================
// BuyerInfo Page - Information page for potential buyers
// ============================================================================

export default function BuyerInfo() {
  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 py-12">
      <div className="container mx-auto max-w-4xl px-4">
        <h1 className="mb-6 text-center text-4xl font-bold text-neutral-900">
          Investment Opportunities
        </h1>
        <p className="mb-12 text-center text-xl text-neutral-600">
          Access exclusive off-market properties from motivated sellers
        </p>

        {/* Feature Cards */}
        <div className="mb-12 grid gap-8 md:grid-cols-2">
          <Card>
            <h3 className="mb-3 text-xl font-semibold text-neutral-900">
              📊 Pre-Qualified Deals
            </h3>
            <p className="text-neutral-600">
              Every property in our inventory has been analyzed and qualified by our AI system,
              ensuring you only see viable investment opportunities.
            </p>
          </Card>

          <Card>
            <h3 className="mb-3 text-xl font-semibold text-neutral-900">⚡ Fast Closings</h3>
            <p className="text-neutral-600">
              Our streamlined process allows for quick closings, typically within 30 days or less.
              Perfect for investors looking to move quickly.
            </p>
          </Card>

          <Card>
            <h3 className="mb-3 text-xl font-semibold text-neutral-900">💰 Competitive Prices</h3>
            <p className="text-neutral-600">
              Access properties at prices below market value from motivated sellers looking for
              fast, hassle-free transactions.
            </p>
          </Card>

          <Card>
            <h3 className="mb-3 text-xl font-semibold text-neutral-900">🔐 Transparent Data</h3>
            <p className="text-neutral-600">
              Get complete property information, including condition assessments, comparable sales
              data, and projected returns.
            </p>
          </Card>
        </div>

        {/* CTA Section */}
        <Card className="bg-gradient-to-r from-primary-600 to-primary-700 text-white">
          <div className="text-center">
            <h2 className="mb-4 text-2xl font-bold">Ready to Start Investing?</h2>
            <p className="mb-6 text-primary-100">
              Join our network of investors and get early access to new opportunities.
            </p>
            <Button variant="secondary" size="lg">
              Contact Us for Access
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}