//src/components/ui/Card.stories.tsx

import type { Meta, StoryObj } from '@storybook/react';
import Card, { CardHeader, CardFooter } from './Card';
import Button from './Button';

const meta = {
  title: 'Components/UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: <p>This is a basic card with default padding and shadow.</p>,
  },
};

export const WithHeader: Story = {
  render: () => (
    <Card>
      <CardHeader title="Card Title" subtitle="This is a subtitle" />
      <p>Card content goes here.</p>
    </Card>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card>
      <CardHeader title="Confirm Action" />
      <p>Are you sure you want to proceed?</p>
      <CardFooter>
        <Button variant="secondary">Cancel</Button>
        <Button variant="primary">Confirm</Button>
      </CardFooter>
    </Card>
  ),
};

export const NoPadding: Story = {
  args: {
    padding: 'none',
    children: <img src="https://via.placeholder.com/400x200" alt="placeholder" />,
  },
};

export const LargeShadow: Story = {
  args: {
    shadow: 'lg',
    children: <p>This card has a larger shadow.</p>,
  },
};