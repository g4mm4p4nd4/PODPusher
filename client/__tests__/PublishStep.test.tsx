import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import PublishStep from '../components/PublishStep';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.split('.').pop() }),
}));

test('publishes with price and tags', () => {
  const onPublish = jest.fn();
  render(<PublishStep product={{ mockups: ['img'] }} onPublish={onPublish} />);
  const price = screen.getByRole('spinbutton');
  fireEvent.change(price, { target: { value: '20' } });
  const tags = screen.getByRole('textbox');
  fireEvent.change(tags, { target: { value: 'one,two' } });
  fireEvent.click(screen.getByText('publishNow'));
  expect(onPublish).toHaveBeenCalledWith({ price: 20, tags: ['one', 'two'] });
});
