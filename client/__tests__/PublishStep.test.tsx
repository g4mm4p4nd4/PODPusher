import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import PublishStep from '../components/PublishStep';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.split('.').pop() }),
}));

test('publishes with price and tags', () => {
  const onPublish = jest.fn();

  render(<PublishStep product={{ image_url: 'img' }} onPublish={onPublish} />);

  fireEvent.change(screen.getByRole('spinbutton'), { target: { value: '20' } });
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'one,two' } });
  fireEvent.click(screen.getByText('publishNow'));

  expect(onPublish).toHaveBeenCalledWith({ price: 20, tags: ['one', 'two'] });
});
