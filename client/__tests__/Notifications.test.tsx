import { render, screen, waitFor } from '@testing-library/react';
import Notifications from '../components/Notifications';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

const mock = new MockAdapter(axios);

describe('Notifications component', () => {
  it('renders list and marks read', async () => {
    mock.onGet(/notifications/).reply(200, [{ id: 1, message: 'hi', read: false }]);
    mock.onPut(/notifications\/1\/read/).reply(200);
    render(<Notifications />);
    await waitFor(() => screen.getByText('hi'));
    expect(screen.getByText('hi')).toBeInTheDocument();
  });
});
