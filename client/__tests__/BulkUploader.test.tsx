import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import BulkUploader from '../components/BulkUploader';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string, opts?: any) => key.split('.').pop() })
}));

jest.mock('../services/bulkUpload', () => ({
  bulkCreate: jest.fn(() => Promise.resolve({ created: 1, errors: [] }))
}));

const { bulkCreate } = require('../services/bulkUpload');

test('uploads file and shows success', async () => {
  render(<BulkUploader />);
  const file = new File([
    'title,description,price,category,image_urls\nA,B,10,cat,http://example.com/img.png'
  ], 'products.csv', { type: 'text/csv' });
  const input = screen.getByLabelText('upload');
  fireEvent.change(input, { target: { files: [file] } });
  fireEvent.click(screen.getByText('upload'));
  expect(await screen.findByText('success')).toBeInTheDocument();
  expect(bulkCreate).toHaveBeenCalled();
});
